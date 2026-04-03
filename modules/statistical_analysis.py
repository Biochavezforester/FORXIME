"""
Módulo de análisis estadístico para FORXIME/2
Incluye índices de biodiversidad, análisis de ocupación y modelo Royle-Nichols
"""
# Imports pesados movidos dentro de las funciones (Lazy Loading)
# Dejar solo pandas y numpy como imports base
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


def calculate_shannon_index(abundance_data):
    """
    Calcula el índice de Shannon-Wiener
    
    Args:
        abundance_data: Series o array con abundancias por especie
    
    Returns:
        float: Índice de Shannon
    """
    abundance_data = np.array(abundance_data)
    abundance_data = abundance_data[abundance_data > 0]  # Remover ceros
    
    if len(abundance_data) == 0:
        return 0
    
    proportions = abundance_data / abundance_data.sum()
    shannon = -np.sum(proportions * np.log(proportions))
    
    return shannon


def calculate_simpson_index(abundance_data):
    """
    Calcula el índice de Simpson
    
    Args:
        abundance_data: Series o array con abundancias por especie
    
    Returns:
        float: Índice de Simpson (1 - D)
    """
    abundance_data = np.array(abundance_data)
    abundance_data = abundance_data[abundance_data > 0]
    
    if len(abundance_data) == 0:
        return 0
    
    n = abundance_data.sum()
    
    if n <= 1:
        return 0
    
    d = np.sum(abundance_data * (abundance_data - 1)) / (n * (n - 1))
    simpson = 1 - d
    
    return simpson


def calculate_species_richness(species_list):
    """
    Calcula la riqueza de especies
    
    Args:
        species_list: Lista o Series con nombres de especies
    
    Returns:
        int: Número de especies únicas
    """
    return len(set(species_list))


def calculate_pielou_evenness(abundance_data):
    """
    Calcula la equitatividad de Pielou
    
    Args:
        abundance_data: Series o array con abundancias por especie
    
    Returns:
        float: Índice de Pielou (J)
    """
    shannon = calculate_shannon_index(abundance_data)
    richness = len(abundance_data[abundance_data > 0])
    
    if richness <= 1:
        return 0
    
    max_shannon = np.log(richness)
    pielou = shannon / max_shannon if max_shannon > 0 else 0
    
    return pielou


def calculate_biodiversity_indices(df):
    """
    Calcula todos los índices de biodiversidad
    
    Args:
        df: DataFrame con datos de especies
    
    Returns:
        dict: Diccionario con todos los índices
    """
    # Obtener abundancias por especie
    abundance = df.groupby('Especie_Categoria')['Eventos_Independientes'].sum()
    
    indices = {
        'Shannon': calculate_shannon_index(abundance.values),
        'Simpson': calculate_simpson_index(abundance.values),
        'Richness': calculate_species_richness(df['Especie_Categoria']),
        'Pielou_Evenness': calculate_pielou_evenness(abundance.values),
        'Total_Individuals': abundance.sum()
    }
    
    return indices


def calculate_biodiversity_by_site(df):
    """
    Calcula índices de biodiversidad por sitio
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Índices por sitio
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    results = []
    
    for site in df[site_column].unique():
        site_data = df[df[site_column] == site]
        abundance = site_data.groupby('Especie_Categoria')['Eventos_Independientes'].sum()
        
        site_indices = {
            'Sitio': site,
            'Shannon': calculate_shannon_index(abundance.values),
            'Simpson': calculate_simpson_index(abundance.values),
            'Richness': calculate_species_richness(site_data['Especie_Categoria']),
            'Pielou': calculate_pielou_evenness(abundance.values),
            'Total_Eventos': abundance.sum()
        }
        
        results.append(site_indices)
    
    return pd.DataFrame(results)


def calculate_bray_curtis_matrix(df):
    """
    Calcula matriz de disimilitud de Bray-Curtis
    
    Args:
        df: DataFrame con datos
    
    Returns:
        tuple: (distance_matrix, site_names)
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Crear matriz sitio x especie
    abundance_matrix = df.pivot_table(
        index=site_column,
        columns='Especie_Categoria',
        values='Eventos_Independientes',
        aggfunc='sum',
        fill_value=0
    )
    
    # Calcular distancia de Bray-Curtis
    from sklearn.metrics import pairwise_distances
    distance_matrix = pairwise_distances(abundance_matrix.values, metric='braycurtis')
    
    return distance_matrix, abundance_matrix.index.tolist()


def create_bray_curtis_dendrogram(df):
    """
    Crea dendrograma de Bray-Curtis
    
    Args:
        df: DataFrame con datos
    
    Returns:
        dict: Información del dendrograma
    """
    distance_matrix, site_names = calculate_bray_curtis_matrix(df)
    
    # Convertir a forma condensada para linkage
    from scipy.spatial.distance import squareform
    condensed_dist = squareform(distance_matrix)
    
    # Realizar clustering jerárquico
    from scipy.cluster.hierarchy import linkage
    linkage_matrix = linkage(condensed_dist, method='average')
    
    return {
        'linkage_matrix': linkage_matrix,
        'site_names': site_names,
        'distance_matrix': distance_matrix
    }


def calculate_relative_abundance_index(df):
    """
    Calcula el Índice de Abundancia Relativa (RAI)
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: RAI por especie
    """
    # Calcular días-trampa totales
    trap_nights = df.groupby('Camara')['Fecha'].agg(
        lambda x: (pd.to_datetime(x).max() - pd.to_datetime(x).min()).days + 1
    ).sum()
    
    # Calcular eventos y días-trampa por especie
    species_stats = df.groupby('Especie_Categoria').agg({
        'Eventos_Independientes': 'sum',
        'Camara': 'nunique'
    }).reset_index()
    
    # Calcular días-trampa por especie (aproximación: cámaras únicas * días promedio)
    avg_days_per_camera = trap_nights / df['Camara'].nunique()
    species_stats['Dias_Trampa'] = (species_stats['Camara'] * avg_days_per_camera).astype(int)
    
    # Calcular RAI (eventos por 100 días-trampa)
    species_stats['RAI'] = (species_stats['Eventos_Independientes'] / trap_nights) * 100
    
    rai_df = pd.DataFrame({
        'Especie': species_stats['Especie_Categoria'],
        'Eventos_Independientes': species_stats['Eventos_Independientes'],
        'Dias_Trampa': species_stats['Dias_Trampa'],
        'RAI': species_stats['RAI']
    }).sort_values('RAI', ascending=False)
    
    return rai_df



def calculate_naive_occupancy(df):
    """
    Calcula ocupación naive (proporción de sitios con presencia)
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Ocupación naive por especie
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    total_sites = df[site_column].nunique()
    
    occupancy = df.groupby('Especie_Categoria')[site_column].nunique() / total_sites
    
    occupancy_df = pd.DataFrame({
        'Especie': occupancy.index,
        'Sitios_Ocupados': df.groupby('Especie_Categoria')[site_column].nunique().values,
        'Total_Sitios': total_sites,
        'Ocupacion_Naive': occupancy.values
    }).sort_values('Ocupacion_Naive', ascending=False)
    
    return occupancy_df


def check_royle_nichols_assumptions(detection_history):
    """
    Verifica si se cumplen los supuestos del modelo Royle-Nichols
    
    Args:
        detection_history: Matriz de detección (sitios x ocasiones)
    
    Returns:
        dict: Resultados de verificación de supuestos
    """
    n_sites = detection_history.shape[0]
    n_occasions = detection_history.shape[1]
    
    assumptions = {
        'sufficient_sites': n_sites >= 10,
        'sufficient_occasions': n_occasions >= 3,
        'n_sites': n_sites,
        'n_occasions': n_occasions,
        'meets_requirements': n_sites >= 10 and n_occasions >= 3,
        'warnings': []
    }
    
    if n_sites < 10:
        assumptions['warnings'].append(
            f"Número de sitios ({n_sites}) es menor al recomendado (≥10)"
        )
    
    if n_occasions < 3:
        assumptions['warnings'].append(
            f"Número de ocasiones ({n_occasions}) es menor al recomendado (≥3)"
        )
    
    # Verificar si hay suficientes detecciones
    total_detections = detection_history.sum()
    if total_detections < 10:
        assumptions['warnings'].append(
            f"Pocas detecciones totales ({total_detections}). El modelo puede ser inestable."
        )
        assumptions['meets_requirements'] = False
    
    return assumptions


def estimate_royle_nichols_simple(detection_history):
    """
    Estimación simplificada del modelo Royle-Nichols
    (Versión básica sin PyMC para evitar dependencias complejas)
    
    Args:
        detection_history: Matriz binaria de detección (sitios x ocasiones)
    
    Returns:
        dict: Estimaciones del modelo
    """
    # Verificar supuestos
    assumptions = check_royle_nichols_assumptions(detection_history)
    
    if not assumptions['meets_requirements']:
        return {
            'success': False,
            'message': 'No se cumplen los supuestos del modelo',
            'assumptions': assumptions
        }
    
    # Estimación simple usando método de momentos
    n_sites = detection_history.shape[0]
    n_occasions = detection_history.shape[1]
    
    # Probabilidad de detección por sitio
    p_site = detection_history.sum(axis=1) / n_occasions
    
    # Ocupación observada
    psi_obs = (p_site > 0).sum() / n_sites
    
    # Probabilidad de detección promedio (cuando presente)
    p_mean = p_site[p_site > 0].mean() if (p_site > 0).any() else 0
    
    # Estimación de lambda (abundancia relativa)
    # Usando relación: p = 1 - (1-r)^lambda
    # Aproximación: lambda ≈ -log(1-p) / log(1-r)
    # Asumiendo r ≈ 0.3 (valor típico)
    r_assumed = 0.3
    
    lambda_estimates = []
    for p in p_site[p_site > 0]:
        if p < 0.99:  # Evitar log(0)
            lambda_est = -np.log(1 - p) / np.log(1 - r_assumed)
            lambda_estimates.append(lambda_est)
    
    lambda_mean = np.mean(lambda_estimates) if lambda_estimates else 0
    
    results = {
        'success': True,
        'psi': psi_obs,  # Ocupación
        'lambda': lambda_mean,  # Abundancia relativa media
        'p_detection': p_mean,  # Probabilidad de detección media
        'n_sites': n_sites,
        'n_occasions': n_occasions,
        'assumptions': assumptions,
        'method': 'Simplified moment estimation',
        'note': 'Esta es una estimación simplificada. Para análisis más robustos, use software especializado como PRESENCE o unmarked en R.'
    }
    
    return results


def run_occupancy_analysis(df):
    """
    Ejecuta análisis completo de ocupación
    
    Args:
        df: DataFrame con datos procesados
    
    Returns:
        dict: Resultados de análisis de ocupación
    """
    results = {}
    
    # Ocupación naive
    results['naive_occupancy'] = calculate_naive_occupancy(df)
    
    # Preparar historias de detección
    from modules.data_processing import prepare_detection_history
    detection_histories = prepare_detection_history(df)
    
    # Intentar modelo Royle-Nichols para cada especie
    results['royle_nichols'] = {}
    
    for species, history_data in detection_histories.items():
        binary_history = history_data['binary'].values
        
        rn_results = estimate_royle_nichols_simple(binary_history)
        results['royle_nichols'][species] = rn_results
    
    return results


def calculate_species_accumulation_curve(df):
    """
    Calcula curva de acumulación de especies
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Curva de acumulación
    """
    df = df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')
    
    cumulative_species = []
    seen_species = set()
    dates = []
    
    for date in df['Fecha'].unique():
        date_data = df[df['Fecha'] == date]
        seen_species.update(date_data['Especie_Categoria'].unique())
        cumulative_species.append(len(seen_species))
        dates.append(date)
    
    accumulation_df = pd.DataFrame({
        'Fecha': dates,
        'Especies_Acumuladas': cumulative_species
    })
    
    return accumulation_df


def calculate_co_occurrence_matrix(df):
    """
    Calcula matriz de co-ocurrencia de especies
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Matriz de co-ocurrencia
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Crear matriz presencia/ausencia
    presence_matrix = df.pivot_table(
        index=site_column,
        columns='Especie_Categoria',
        values='Eventos_Independientes',
        aggfunc='sum',
        fill_value=0
    )
    
    presence_matrix = (presence_matrix > 0).astype(int)
    
    # Calcular co-ocurrencia
    co_occurrence = presence_matrix.T.dot(presence_matrix)
    
    return co_occurrence


def calculate_rarefaction_curve(df, method='individual', n_iterations=50):
    """
    Calcula curva de rarefacción basada en individuos o muestras
    OPTIMIZADO: Reducido a 50 iteraciones para mejor rendimiento
    
    Args:
        df: DataFrame con datos
        method: 'individual' o 'sample'
        n_iterations: Número de iteraciones para bootstrap (default: 50)
    
    Returns:
        DataFrame: Curva de rarefacción con intervalos de confianza
    """
    # Importante: scipy.stats.sem no se usa directamente en este bloque pero se deja aquí por si acaso
    # aunque np.std suele bastar para los CIs calculados abajo.
    
    if method == 'individual':
        # Rarefacción basada en individuos
        total_individuals = df['Eventos_Independientes'].sum()
        
        # OPTIMIZACIÓN: Crear array de individuos de forma más eficiente
        individuals = []
        for idx, row in df.iterrows():
            individuals.extend([row['Especie_Categoria']] * int(row['Eventos_Independientes']))
        
        individuals = np.array(individuals)  # Convertir a numpy array para mejor rendimiento
        
        # Calcular rarefacción para diferentes tamaños de muestra
        # OPTIMIZACIÓN: Reducir puntos de muestreo para datasets grandes
        n_points = min(40, len(individuals))
        sample_sizes = np.linspace(1, len(individuals), n_points).astype(int)
        sample_sizes = np.unique(sample_sizes)  # Eliminar duplicados
        
        rarefaction_results = []
        
        for sample_size in sample_sizes:
            species_counts = []
            
            # OPTIMIZACIÓN: Usar vectorización cuando sea posible
            for _ in range(n_iterations):
                # Muestreo aleatorio sin reemplazo
                sample = np.random.choice(individuals, size=sample_size, replace=False)
                n_species = len(np.unique(sample))
                species_counts.append(n_species)
            
            rarefaction_results.append({
                'Sample_Size': sample_size,
                'Mean_Species': np.mean(species_counts),
                'SD': np.std(species_counts),
                'CI_Lower': np.percentile(species_counts, 2.5),
                'CI_Upper': np.percentile(species_counts, 97.5)
            })
        
        return pd.DataFrame(rarefaction_results)
    
    else:  # sample-based
        # Rarefacción basada en muestras (fechas)
        df_copy = df.copy()
        df_copy['Fecha'] = pd.to_datetime(df_copy['Fecha'])
        unique_dates = df_copy['Fecha'].unique()
        
        # OPTIMIZACIÓN: Reducir puntos de muestreo
        n_points = min(25, len(unique_dates))
        sample_sizes = np.linspace(1, len(unique_dates), n_points).astype(int)
        sample_sizes = np.unique(sample_sizes)
        
        rarefaction_results = []
        
        for sample_size in sample_sizes:
            species_counts = []
            
            for _ in range(n_iterations):
                # Muestreo aleatorio de fechas
                sampled_dates = np.random.choice(unique_dates, size=sample_size, replace=False)
                sampled_data = df_copy[df_copy['Fecha'].isin(sampled_dates)]
                n_species = sampled_data['Especie_Categoria'].nunique()
                species_counts.append(n_species)
            
            rarefaction_results.append({
                'Sample_Size': sample_size,
                'Mean_Species': np.mean(species_counts),
                'SD': np.std(species_counts),
                'CI_Lower': np.percentile(species_counts, 2.5),
                'CI_Upper': np.percentile(species_counts, 97.5)
            })
        
        return pd.DataFrame(rarefaction_results)


def estimate_sampling_completeness(df, method='chao1'):
    """
    Estima la completitud del muestreo usando estimadores no paramétricos
    
    Args:
        df: DataFrame con datos
        method: 'chao1', 'chao2', 'ace', o 'ice'
    
    Returns:
        dict: Estimaciones de completitud
    """
    # Calcular riqueza observada
    observed_richness = df['Especie_Categoria'].nunique()
    
    # Contar singletons y doubletons
    species_counts = df.groupby('Especie_Categoria')['Eventos_Independientes'].sum()
    singletons = (species_counts == 1).sum()
    doubletons = (species_counts == 2).sum()
    
    # Estimador Chao1 (basado en abundancia)
    if method == 'chao1':
        if doubletons > 0:
            estimated_richness = observed_richness + (singletons ** 2) / (2 * doubletons)
        else:
            estimated_richness = observed_richness + (singletons * (singletons - 1)) / 2
    
    # Estimador Chao2 (basado en incidencia)
    elif method == 'chao2':
        # Contar especies por sitio
        site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        species_by_site = df.groupby('Especie_Categoria')[site_column].nunique()
        
        uniques = (species_by_site == 1).sum()  # Especies en 1 solo sitio
        duplicates = (species_by_site == 2).sum()  # Especies en 2 sitios
        
        if duplicates > 0:
            estimated_richness = observed_richness + (uniques ** 2) / (2 * duplicates)
        else:
            estimated_richness = observed_richness + (uniques * (uniques - 1)) / 2
    
    else:
        # Default a Chao1
        if doubletons > 0:
            estimated_richness = observed_richness + (singletons ** 2) / (2 * doubletons)
        else:
            estimated_richness = observed_richness + (singletons * (singletons - 1)) / 2
    
    # Calcular completitud
    completeness = (observed_richness / estimated_richness) * 100 if estimated_richness > 0 else 100
    completeness = min(completeness, 100)  # No puede ser > 100%
    
    # Determinar estado
    if completeness >= 90:
        status = "Excelente"
        recommendation = "El muestreo ha capturado la mayoría de las especies presentes."
    elif completeness >= 75:
        status = "Bueno"
        recommendation = "El muestreo es adecuado, aunque podrían detectarse algunas especies adicionales."
    elif completeness >= 60:
        status = "Moderado"
        recommendation = "Se recomienda extender el muestreo para detectar más especies."
    else:
        status = "Insuficiente"
        recommendation = "El muestreo es insuficiente. Se requiere mayor esfuerzo para caracterizar la comunidad."
    
    return {
        'observed_richness': int(observed_richness),
        'estimated_richness': round(estimated_richness, 1),
        'completeness_percent': round(completeness, 1),
        'status': status,
        'recommendation': recommendation,
        'singletons': int(singletons),
        'doubletons': int(doubletons),
        'method': method.upper()
    }

