"""
Módulo de Análisis Espacial
Funciones para interpolación espacial y mapas de abundancia relativa
"""

import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from scipy.spatial.distance import cdist
from sklearn.neighbors import KernelDensity


def calculate_rai_by_location(df, species):
    """
    Calcula el RAI (Relative Abundance Index) para cada ubicación de cámara
    
    Args:
        df: DataFrame con datos de cámaras trampa
        species: Nombre de la especie a analizar
        
    Returns:
        DataFrame con coordenadas y RAI por cámara
    """
    # Filtrar por especie
    species_df = df[df['Especie_Categoria'] == species].copy()
    
    if len(species_df) == 0:
        return None
    
    # Calcular días de muestreo por cámara
    camera_days = df.groupby(['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM']).agg({
        'Fecha': lambda x: (pd.to_datetime(x.max()) - pd.to_datetime(x.min())).days + 1
    }).reset_index()
    camera_days.columns = ['Camara', 'X', 'Y', 'Dias_Muestreo']
    
    # Contar eventos independientes por cámara para la especie
    species_events = species_df.groupby(['Camara']).agg({
        'Eventos_Independientes': 'sum'
    }).reset_index()
    species_events.columns = ['Camara', 'Eventos']
    
    # Combinar datos
    rai_data = camera_days.merge(species_events, on='Camara', how='left')
    rai_data['Eventos'] = rai_data['Eventos'].fillna(0)
    
    # Calcular RAI (eventos por 100 días-trampa)
    rai_data['RAI'] = (rai_data['Eventos'] / rai_data['Dias_Muestreo']) * 100
    
    # Asegurar que no haya valores infinitos o NaN
    rai_data['RAI'] = rai_data['RAI'].replace([np.inf, -np.inf], 0).fillna(0)
    
    return rai_data[['Camara', 'X', 'Y', 'RAI', 'Eventos', 'Dias_Muestreo']]


def calculate_optimal_bandwidth(points, method='scott'):
    """
    Calcula el bandwidth óptimo para KDE
    
    Args:
        points: Array de coordenadas (N x 2)
        method: 'scott' o 'silverman'
        
    Returns:
        float: Bandwidth óptimo
    """
    n = len(points)
    d = 2  # Dimensiones (X, Y)
    
    # Calcular desviación estándar de cada dimensión
    std_x = np.std(points[:, 0])
    std_y = np.std(points[:, 1])
    std_avg = (std_x + std_y) / 2
    
    if method == 'scott':
        # Regla de Scott
        bandwidth = std_avg * (n ** (-1.0 / (d + 4)))
    elif method == 'silverman':
        # Regla de Silverman
        bandwidth = std_avg * ((n * (d + 2) / 4.0) ** (-1.0 / (d + 4)))
    else:
        # Default: usar Scott
        bandwidth = std_avg * (n ** (-1.0 / (d + 4)))
    
    return bandwidth


def perform_kde_interpolation(points, values, grid_x, grid_y, bandwidth='auto'):
    """
    Realiza interpolación KDE sobre una grilla espacial
    
    Args:
        points: Array de coordenadas (N x 2)
        values: Array de valores RAI (N,)
        grid_x: Grilla de coordenadas X
        grid_y: Grilla de coordenadas Y
        bandwidth: 'auto' o valor numérico
        
    Returns:
        Array 2D con valores interpolados
    """
    if len(points) < 2:
        # No hay suficientes puntos para interpolar
        return np.zeros_like(grid_x)
    
    # Calcular bandwidth si es automático
    if bandwidth == 'auto':
        bandwidth = calculate_optimal_bandwidth(points, method='scott')
    
    # Crear grilla de evaluación
    grid_points = np.c_[grid_x.ravel(), grid_y.ravel()]
    
    # Usar KernelDensity de sklearn para mayor control
    kde = KernelDensity(bandwidth=bandwidth, kernel='gaussian')
    
    # Ponderar puntos por sus valores RAI
    # Repetir puntos según su valor RAI (normalizado)
    if np.sum(values) > 0:
        # Normalizar valores para que sumen a 1
        weights = values / np.sum(values)
        
        # Crear puntos ponderados (repetir puntos según peso)
        n_samples = 1000  # Número de muestras para representar la distribución
        weighted_points = []
        
        for i, (point, weight) in enumerate(zip(points, weights)):
            n_repeats = max(1, int(weight * n_samples))
            # Añadir pequeña variación gaussiana para suavizar
            noise = np.random.normal(0, bandwidth * 0.1, (n_repeats, 2))
            repeated = np.tile(point, (n_repeats, 1)) + noise
            weighted_points.append(repeated)
        
        weighted_points = np.vstack(weighted_points)
        
        # Ajustar KDE
        kde.fit(weighted_points)
        
        # Evaluar en la grilla
        log_density = kde.score_samples(grid_points)
        density = np.exp(log_density)
        
        # Reshape a grilla 2D
        z = density.reshape(grid_x.shape)
        
        # Normalizar a escala de RAI
        if np.max(z) > 0:
            z = z / np.max(z) * np.max(values)
    else:
        z = np.zeros_like(grid_x)
    
    return z


def create_abundance_grid(df, species, grid_resolution=100, bandwidth='auto'):
    """
    Genera grilla de abundancia interpolada para una especie
    
    Args:
        df: DataFrame con datos de cámaras trampa
        species: Nombre de la especie
        grid_resolution: Número de puntos en cada dimensión de la grilla
        bandwidth: 'auto' o valor numérico para KDE
        
    Returns:
        dict con grillas X, Y, Z y datos de cámaras
    """
    # Calcular RAI por ubicación
    rai_data = calculate_rai_by_location(df, species)
    
    if rai_data is None or len(rai_data) == 0:
        return None
    
    # Extraer coordenadas y valores
    points = rai_data[['X', 'Y']].values
    values = rai_data['RAI'].values
    
    # Definir límites de la grilla con margen
    x_min, x_max = points[:, 0].min(), points[:, 0].max()
    y_min, y_max = points[:, 1].min(), points[:, 1].max()
    
    # Añadir margen del 10%
    x_margin = (x_max - x_min) * 0.1
    y_margin = (y_max - y_min) * 0.1
    
    x_min -= x_margin
    x_max += x_margin
    y_min -= y_margin
    y_max += y_margin
    
    # Crear grilla
    grid_x, grid_y = np.meshgrid(
        np.linspace(x_min, x_max, grid_resolution),
        np.linspace(y_min, y_max, grid_resolution)
    )
    
    # Realizar interpolación KDE
    grid_z = perform_kde_interpolation(points, values, grid_x, grid_y, bandwidth)
    
    return {
        'grid_x': grid_x,
        'grid_y': grid_y,
        'grid_z': grid_z,
        'camera_data': rai_data,
        'species': species,
        'bounds': {
            'x_min': x_min,
            'x_max': x_max,
            'y_min': y_min,
            'y_max': y_max
        }
    }


def get_species_abundance_data(df, species_list):
    """
    Prepara datos de abundancia para múltiples especies
    
    Args:
        df: DataFrame con datos de cámaras trampa
        species_list: Lista de nombres de especies
        
    Returns:
        dict con datos de abundancia por especie
    """
    abundance_data = {}
    
    for species in species_list:
        data = create_abundance_grid(df, species)
        if data is not None:
            abundance_data[species] = data
    
    return abundance_data


def calculate_hotspot_statistics(grid_data, threshold_percentile=75):
    """
    Calcula estadísticas de hotspots en el mapa de abundancia
    
    Args:
        grid_data: Diccionario con datos de grilla
        threshold_percentile: Percentil para definir hotspots
        
    Returns:
        dict con estadísticas de hotspots
    """
    if grid_data is None:
        return None
    
    z = grid_data['grid_z']
    
    # Calcular umbral para hotspots
    threshold = np.percentile(z[z > 0], threshold_percentile) if np.any(z > 0) else 0
    
    # Identificar hotspots
    hotspots = z >= threshold
    n_hotspots = np.sum(hotspots)
    
    # Calcular área de hotspots (aproximada)
    total_cells = z.size
    hotspot_percentage = (n_hotspots / total_cells) * 100 if total_cells > 0 else 0
    
    # Valor máximo y promedio
    max_value = np.max(z)
    mean_value = np.mean(z[z > 0]) if np.any(z > 0) else 0
    
    return {
        'n_hotspots': int(n_hotspots),
        'hotspot_percentage': hotspot_percentage,
        'max_rai': max_value,
        'mean_rai': mean_value,
        'threshold': threshold
    }
