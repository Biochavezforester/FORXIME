"""
Módulo de análisis temporal para FORXIME/2
Incluye patrones de actividad y solapamiento temporal (Ridout-Linkie y KDE)
"""
import pandas as pd
import numpy as np
from scipy import stats
from scipy.integrate import simpson
import warnings
import streamlit as st
warnings.filterwarnings('ignore')


def extract_hour_from_time(time_obj):
    """
    Extrae la hora de un objeto de tiempo
    
    Args:
        time_obj: Objeto de tiempo o string
    
    Returns:
        float: Hora en formato decimal (0-24)
    """
    try:
        if isinstance(time_obj, str):
            time_obj = pd.to_datetime(time_obj).time()
        
        hour = time_obj.hour + time_obj.minute / 60 + time_obj.second / 3600
        return hour
    except:
        return None


def convert_time_to_radians(hours):
    """
    Convierte horas a radianes para análisis circular
    
    Args:
        hours: Array de horas (0-24)
    
    Returns:
        array: Radianes (0-2π)
    """
    return (np.array(hours) / 24) * 2 * np.pi


def circular_kernel_density(times_radians, grid_size=1000, bandwidth=None):
    """
    Calcula Kernel Density Estimation circular
    
    Args:
        times_radians: Array de tiempos en radianes
        grid_size: Número de puntos en la grilla
        bandwidth: Ancho de banda (si None, se calcula automáticamente)
    
    Returns:
        tuple: (grid_radians, density)
    """
    if bandwidth is None:
        # Regla de Silverman adaptada para datos circulares
        n = len(times_radians)
        bandwidth = 1.06 * np.std(times_radians) * n**(-1/5)
        bandwidth = max(bandwidth, 0.1)  # Mínimo bandwidth
    
    # Crear grilla
    grid = np.linspace(0, 2 * np.pi, grid_size)
    
    # Calcular densidad
    density = np.zeros(grid_size)
    
    for time in times_radians:
        # Von Mises kernel (equivalente circular del kernel gaussiano)
        kappa = 1 / (bandwidth ** 2)
        density += np.exp(kappa * np.cos(grid - time))
    
    # Normalizar
    density = density / (len(times_radians) * 2 * np.pi * np.i0(1 / (bandwidth ** 2)))
    
    return grid, density


def classify_activity_pattern(hours):
    """
    Clasifica el patrón de actividad
    
    Args:
        hours: Array de horas (0-24)
    
    Returns:
        str: Clasificación del patrón
    """
    hours = np.array(hours)
    
    # Definir períodos
    day_mask = (hours >= 6) & (hours < 18)
    night_mask = (hours < 6) | (hours >= 18)
    crepuscular_mask = ((hours >= 5) & (hours < 7)) | ((hours >= 17) & (hours < 19))
    
    day_pct = day_mask.sum() / len(hours)
    night_pct = night_mask.sum() / len(hours)
    crep_pct = crepuscular_mask.sum() / len(hours)
    
    if crep_pct > 0.5:
        return 'Crepuscular'
    elif day_pct > 0.7:
        return 'Diurno'
    elif night_pct > 0.7:
        return 'Nocturno'
    else:
        return 'Catémero'


@st.cache_data(show_spinner=False)
def calculate_activity_pattern(df, species):
    """
    Calcula el patrón de actividad para una especie
    
    Args:
        df: DataFrame con datos
        species: Nombre de la especie
    
    Returns:
        dict: Información del patrón de actividad
    """
    species_data = df[df['Especie_Categoria'] == species].copy()
    
    # Extraer horas
    species_data['Hora_Decimal'] = species_data['Hora'].apply(extract_hour_from_time)
    hours = species_data['Hora_Decimal'].dropna().values
    
    if len(hours) == 0:
        return None
    
    # Convertir a radianes
    radians = convert_time_to_radians(hours)
    
    # Calcular KDE
    grid, density = circular_kernel_density(radians)
    
    # Convertir grid de vuelta a horas
    grid_hours = (grid / (2 * np.pi)) * 24
    
    # Clasificar patrón
    pattern = classify_activity_pattern(hours)
    
    # Calcular estadísticas circulares
    mean_angle = np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())
    mean_hour = (mean_angle / (2 * np.pi)) * 24
    if mean_hour < 0:
        mean_hour += 24
    
    # Concentración (r)
    r = np.sqrt(np.sin(radians).mean()**2 + np.cos(radians).mean()**2)
    
    return {
        'species': species,
        'n_records': len(hours),
        'pattern': pattern,
        'mean_hour': mean_hour,
        'concentration': r,
        'grid_hours': grid_hours,
        'density': density,
        'raw_hours': hours
    }


def calculate_overlap_coefficient_delta(times1_radians, times2_radians, estimator='delta4'):
    """
    Calcula coeficiente de solapamiento Δ (Ridout & Linkie)
    
    Args:
        times1_radians: Tiempos de especie 1 en radianes
        times2_radians: Tiempos de especie 2 en radianes
        estimator: 'delta1' o 'delta4'
    
    Returns:
        float: Coeficiente de solapamiento (0-1)
    """
    # Calcular KDE para ambas especies
    grid1, density1 = circular_kernel_density(times1_radians)
    grid2, density2 = circular_kernel_density(times2_radians)
    
    # Asegurar que las grillas sean iguales
    grid = np.linspace(0, 2 * np.pi, 1000)
    density1_interp = np.interp(grid, grid1, density1)
    density2_interp = np.interp(grid, grid2, density2)
    
    if estimator == 'delta1':
        # Δ1 = integral de min(f1, f2)
        overlap = simpson(np.minimum(density1_interp, density2_interp), grid)
    else:  # delta4
        # Δ4 = integral de sqrt(f1 * f2) * 2
        overlap = 2 * simpson(np.sqrt(density1_interp * density2_interp), grid)
    
    return min(overlap, 1.0)  # Asegurar que esté en [0, 1]


def bootstrap_overlap_ci(times1_radians, times2_radians, estimator='delta4', 
                        n_bootstrap=1000, ci_level=0.95):
    """
    Calcula intervalos de confianza para el coeficiente de solapamiento usando bootstrap
    
    Args:
        times1_radians: Tiempos de especie 1
        times2_radians: Tiempos de especie 2
        estimator: 'delta1' o 'delta4'
        n_bootstrap: Número de iteraciones bootstrap
        ci_level: Nivel de confianza
    
    Returns:
        dict: Coeficiente y intervalos de confianza
    """
    # Calcular coeficiente observado
    observed = calculate_overlap_coefficient_delta(times1_radians, times2_radians, estimator)
    
    # Bootstrap
    bootstrap_values = []
    
    for _ in range(n_bootstrap):
        # Resample con reemplazo
        sample1 = np.random.choice(times1_radians, size=len(times1_radians), replace=True)
        sample2 = np.random.choice(times2_radians, size=len(times2_radians), replace=True)
        
        # Calcular coeficiente
        boot_coef = calculate_overlap_coefficient_delta(sample1, sample2, estimator)
        bootstrap_values.append(boot_coef)
    
    # Calcular intervalos de confianza
    alpha = 1 - ci_level
    lower = np.percentile(bootstrap_values, alpha/2 * 100)
    upper = np.percentile(bootstrap_values, (1 - alpha/2) * 100)
    
    return {
        'coefficient': observed,
        'ci_lower': lower,
        'ci_upper': upper,
        'ci_level': ci_level,
        'estimator': estimator
    }


def calculate_kernel_overlap(times1_radians, times2_radians):
    """
    Calcula solapamiento basado en área bajo las curvas KDE
    
    Args:
        times1_radians: Tiempos de especie 1
        times2_radians: Tiempos de especie 2
    
    Returns:
        dict: Métricas de solapamiento
    """
    # Calcular KDE para ambas especies
    grid1, density1 = circular_kernel_density(times1_radians)
    grid2, density2 = circular_kernel_density(times2_radians)
    
    # Usar misma grilla
    grid = np.linspace(0, 2 * np.pi, 1000)
    density1_interp = np.interp(grid, grid1, density1)
    density2_interp = np.interp(grid, grid2, density2)
    
    # Calcular área de solapamiento
    overlap_area = simpson(np.minimum(density1_interp, density2_interp), grid)
    
    # Calcular áreas totales
    area1 = simpson(density1_interp, grid)
    area2 = simpson(density2_interp, grid)
    
    # Porcentaje de solapamiento
    overlap_pct = (overlap_area / min(area1, area2)) * 100 if min(area1, area2) > 0 else 0
    
    return {
        'overlap_area': overlap_area,
        'overlap_percentage': overlap_pct,
        'density1': density1_interp,
        'density2': density2_interp,
        'grid_radians': grid,
        'grid_hours': (grid / (2 * np.pi)) * 24
    }


@st.cache_data(show_spinner=False)
def analyze_temporal_overlap(df, species1, species2):
    """
    Análisis completo de solapamiento temporal entre dos especies
    
    Args:
        df: DataFrame con datos
        species1: Nombre de especie 1
        species2: Nombre de especie 2
    
    Returns:
        dict: Resultados completos de solapamiento
    """
    # Extraer datos de cada especie
    data1 = df[df['Especie_Categoria'] == species1].copy()
    data2 = df[df['Especie_Categoria'] == species2].copy()
    
    data1['Hora_Decimal'] = data1['Hora'].apply(extract_hour_from_time)
    data2['Hora_Decimal'] = data2['Hora'].apply(extract_hour_from_time)
    
    hours1 = data1['Hora_Decimal'].dropna().values
    hours2 = data2['Hora_Decimal'].dropna().values
    
    if len(hours1) < 5 or len(hours2) < 5:
        return {
            'success': False,
            'message': 'Datos insuficientes para análisis (mínimo 5 registros por especie)'
        }
    
    # Convertir a radianes
    radians1 = convert_time_to_radians(hours1)
    radians2 = convert_time_to_radians(hours2)
    
    # Determinar estimador apropiado
    n1, n2 = len(hours1), len(hours2)
    
    if n1 < 50 or n2 < 50:
        estimator_ridout = 'delta1'
    else:
        estimator_ridout = 'delta4'
    
    # Método 1: Ridout & Linkie
    ridout_linkie = bootstrap_overlap_ci(radians1, radians2, estimator=estimator_ridout)
    
    # Método 2: Kernel Density Overlap
    kernel_overlap = calculate_kernel_overlap(radians1, radians2)
    
    # Patrones de actividad individuales
    pattern1 = calculate_activity_pattern(df, species1)
    pattern2 = calculate_activity_pattern(df, species2)
    
    results = {
        'success': True,
        'species1': species1,
        'species2': species2,
        'n_records_sp1': n1,
        'n_records_sp2': n2,
        'ridout_linkie': ridout_linkie,
        'kernel_overlap': kernel_overlap,
        'activity_pattern_sp1': pattern1,
        'activity_pattern_sp2': pattern2
    }
    
    return results


def analyze_all_species_overlaps(df):
    """
    Analiza solapamiento temporal entre todas las parejas de especies
    
    Args:
        df: DataFrame con datos
    
    Returns:
        list: Lista de resultados de solapamiento
    """
    species_list = df['Especie_Categoria'].unique()
    
    results = []
    
    for i in range(len(species_list)):
        for j in range(i + 1, len(species_list)):
            sp1 = species_list[i]
            sp2 = species_list[j]
            
            overlap_result = analyze_temporal_overlap(df, sp1, sp2)
            
            if overlap_result['success']:
                results.append(overlap_result)
    
    return results


def identify_predator_prey_patterns(df, predator, prey):
    """
    Identifica patrones de depredador-presa basado en solapamiento temporal
    
    Args:
        df: DataFrame con datos
        predator: Nombre del depredador
        prey: Nombre de la presa
    
    Returns:
        dict: Análisis de interacción depredador-presa
    """
    overlap_result = analyze_temporal_overlap(df, predator, prey)
    
    if not overlap_result['success']:
        return overlap_result
    
    # Interpretar resultados
    ridout_coef = overlap_result['ridout_linkie']['coefficient']
    
    if ridout_coef > 0.75:
        interpretation = "Alto solapamiento temporal. El depredador y la presa están activos en las mismas horas, lo que sugiere alta probabilidad de encuentros."
    elif ridout_coef > 0.5:
        interpretation = "Solapamiento temporal moderado. Existe cierta coincidencia en los períodos de actividad."
    else:
        interpretation = "Bajo solapamiento temporal. La presa podría estar evitando temporalmente al depredador."
    
    overlap_result['interpretation'] = interpretation
    overlap_result['interaction_type'] = 'predator-prey'
    
    return overlap_result


def identify_competitor_patterns(df, species1, species2):
    """
    Identifica patrones de competencia basado en solapamiento temporal
    
    Args:
        df: DataFrame con datos
        species1: Nombre de especie 1
        species2: Nombre de especie 2
    
    Returns:
        dict: Análisis de competencia
    """
    overlap_result = analyze_temporal_overlap(df, species1, species2)
    
    if not overlap_result['success']:
        return overlap_result
    
    # Interpretar resultados
    ridout_coef = overlap_result['ridout_linkie']['coefficient']
    
    if ridout_coef < 0.5:
        interpretation = "Bajo solapamiento temporal. Los competidores podrían estar evitándose mediante partición temporal del hábitat."
    elif ridout_coef < 0.75:
        interpretation = "Solapamiento temporal moderado. Existe cierta coexistencia temporal entre competidores."
    else:
        interpretation = "Alto solapamiento temporal. Los competidores comparten los mismos períodos de actividad, lo que podría indicar competencia directa o abundancia de recursos."
    
    overlap_result['interpretation'] = interpretation
    overlap_result['interaction_type'] = 'competition'
    
    return overlap_result
