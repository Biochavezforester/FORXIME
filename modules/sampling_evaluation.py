"""
Módulo de evaluación de muestreo para FORXIME/2
"""
import pandas as pd
import numpy as np


def identify_false_triggers(df):
    """
    Identifica posibles disparos falsos (fotos sin fauna)
    
    Args:
        df: DataFrame con datos
    
    Returns:
        dict: Análisis de falsos positivos
    """
    # Buscar registros que podrían ser falsos positivos
    false_trigger_keywords = ['vacio', 'empty', 'sin animal', 'no animal', 'vegetacion', 
                              'vegetation', 'viento', 'wind', 'lluvia', 'rain']
    
    mask = df['Especie_Categoria'].str.lower().str.contains('|'.join(false_trigger_keywords), na=False)
    false_triggers = df[mask]
    
    # Calcular por cámara
    false_by_camera = false_triggers.groupby('Camara').size() if len(false_triggers) > 0 else pd.Series()
    total_by_camera = df.groupby('Camara').size()
    
    false_pct_by_camera = (false_by_camera / total_by_camera * 100).fillna(0)
    
    results = {
        'total_false_triggers': len(false_triggers),
        'percentage': len(false_triggers) / len(df) * 100 if len(df) > 0 else 0,
        'by_camera': false_pct_by_camera.to_dict(),
        'cameras_with_high_false_rate': false_pct_by_camera[false_pct_by_camera > 20].index.tolist()
    }
    
    return results


def calculate_sampling_effort(df):
    """
    Calcula esfuerzo de muestreo
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Esfuerzo por cámara
    """
    df = df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    effort = df.groupby('Camara').agg({
        'Fecha': lambda x: (x.max() - x.min()).days + 1,
        'Especie_Categoria': 'nunique',
        'Eventos_Independientes': 'sum'
    }).reset_index()
    
    effort.columns = ['Camara', 'Dias_Trampa', 'Riqueza', 'Total_Eventos']
    
    # Calcular tasa de captura
    effort['Tasa_Captura'] = effort['Total_Eventos'] / effort['Dias_Trampa']
    
    # Clasificar esfuerzo
    def classify_effort(days):
        if days < 30:
            return 'Insuficiente'
        elif days < 60:
            return 'Aceptable'
        elif days < 90:
            return 'Bueno'
        else:
            return 'Excelente'
    
    effort['Clasificacion_Esfuerzo'] = effort['Dias_Trampa'].apply(classify_effort)
    
    return effort


def evaluate_camera_spacing(df):
    """
    Evalúa el espaciamiento entre cámaras
    
    Args:
        df: DataFrame con coordenadas
    
    Returns:
        dict: Evaluación del espaciamiento
    """
    from scipy.spatial.distance import pdist, squareform
    
    # Obtener coordenadas únicas de cámaras
    cameras = df[['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM']].drop_duplicates()
    
    if len(cameras) < 2:
        return {
            'evaluation': 'No hay suficientes cámaras para evaluar espaciamiento',
            'recommendations': []
        }
    
    # Calcular matriz de distancias
    coords = cameras[['Coordenada_X_UTM', 'Coordenada_Y_UTM']].values
    distances = pdist(coords, metric='euclidean')
    dist_matrix = squareform(distances)
    
    # Obtener distancias mínimas (excluyendo diagonal)
    np.fill_diagonal(dist_matrix, np.inf)
    min_distances = dist_matrix.min(axis=1)
    
    avg_min_distance = np.mean(min_distances)
    
    recommendations = []
    
    # Evaluar espaciamiento
    if avg_min_distance < 100:
        evaluation = "Cámaras muy cercanas"
        recommendations.append({
            'issue': 'Espaciamiento muy corto',
            'recommendation': f"La distancia promedio entre cámaras cercanas es {avg_min_distance:.0f}m. "
                            f"Para especies con rangos de hogar grandes, considere aumentar el espaciamiento "
                            f"a al menos 500m para asegurar independencia espacial."
        })
    elif avg_min_distance < 500:
        evaluation = "Espaciamiento adecuado para especies pequeñas"
        recommendations.append({
            'issue': 'Espaciamiento moderado',
            'recommendation': f"La distancia promedio es {avg_min_distance:.0f}m. "
                            f"Adecuado para especies pequeñas, pero considere aumentar para especies grandes."
        })
    elif avg_min_distance < 2000:
        evaluation = "Buen espaciamiento"
        recommendations.append({
            'issue': 'Espaciamiento apropiado',
            'recommendation': f"La distancia promedio es {avg_min_distance:.0f}m. "
                            f"Espaciamiento adecuado para la mayoría de especies."
        })
    else:
        evaluation = "Cámaras muy espaciadas"
        recommendations.append({
            'issue': 'Espaciamiento amplio',
            'recommendation': f"La distancia promedio es {avg_min_distance:.0f}m. "
                            f"Buen espaciamiento, pero podría dificultar la detección de especies raras."
        })
    
    return {
        'average_min_distance_m': avg_min_distance,
        'evaluation': evaluation,
        'recommendations': recommendations,
        'distance_matrix': dist_matrix
    }


def evaluate_paired_vs_single_sites(df):
    """
    Evalúa la efectividad de sitios dobles vs sencillos
    
    Args:
        df: DataFrame con datos agrupados
    
    Returns:
        dict: Evaluación de configuración de sitios
    """
    if 'Sitio_Agrupado' not in df.columns:
        return {
            'evaluation': 'No hay sitios agrupados para evaluar',
            'recommendation': 'No aplicable'
        }
    
    # Contar cámaras por sitio agrupado
    cameras_per_site = df.groupby('Sitio_Agrupado')['Camara'].nunique()
    
    single_sites = (cameras_per_site == 1).sum()
    paired_sites = (cameras_per_site == 2).sum()
    multiple_sites = (cameras_per_site > 2).sum()
    
    # Comparar detecciones
    single_site_names = cameras_per_site[cameras_per_site == 1].index
    paired_site_names = cameras_per_site[cameras_per_site == 2].index
    
    single_richness = df[df['Sitio_Agrupado'].isin(single_site_names)].groupby('Sitio_Agrupado')['Especie_Categoria'].nunique().mean()
    paired_richness = df[df['Sitio_Agrupado'].isin(paired_site_names)].groupby('Sitio_Agrupado')['Especie_Categoria'].nunique().mean()
    
    # Determinar recomendación
    if paired_richness > single_richness * 1.3:
        recommendation = "Los sitios dobles detectan significativamente más especies. Se recomienda usar configuración de sitios dobles."
    elif paired_richness > single_richness * 1.1:
        recommendation = "Los sitios dobles detectan ligeramente más especies. Considere sitios dobles si el presupuesto lo permite."
    else:
        recommendation = "No hay diferencia significativa. Los sitios sencillos son más costo-efectivos."
    
    return {
        'single_sites': int(single_sites),
        'paired_sites': int(paired_sites),
        'multiple_sites': int(multiple_sites),
        'avg_richness_single': float(single_richness) if not np.isnan(single_richness) else 0,
        'avg_richness_paired': float(paired_richness) if not np.isnan(paired_richness) else 0,
        'recommendation': recommendation
    }


def calculate_species_accumulation_completeness(df):
    """
    Evalúa completitud del muestreo usando curva de acumulación
    
    Args:
        df: DataFrame con datos
    
    Returns:
        dict: Evaluación de completitud
    """
    from modules.statistical_analysis import calculate_species_accumulation_curve
    
    accumulation = calculate_species_accumulation_curve(df)
    
    if len(accumulation) < 2:
        return {
            'completeness': 'Insuficiente',
            'recommendation': 'Se necesitan más datos para evaluar completitud'
        }
    
    # Verificar si la curva se está aplanando
    last_10_pct = accumulation.tail(int(len(accumulation) * 0.1))
    species_gain = last_10_pct['Especies_Acumuladas'].iloc[-1] - last_10_pct['Especies_Acumuladas'].iloc[0]
    
    total_species = accumulation['Especies_Acumuladas'].iloc[-1]
    gain_rate = species_gain / total_species if total_species > 0 else 0
    
    if gain_rate < 0.05:
        completeness = "Alta"
        recommendation = "La curva de acumulación se ha aplanado. El muestreo parece completo."
    elif gain_rate < 0.15:
        completeness = "Moderada"
        recommendation = "La curva aún está creciendo moderadamente. Considere extender el muestreo."
    else:
        completeness = "Baja"
        recommendation = "La curva sigue creciendo. Se recomienda continuar el muestreo para detectar más especies."
    
    return {
        'completeness': completeness,
        'gain_rate': gain_rate,
        'total_species': int(total_species),
        'recommendation': recommendation,
        'accumulation_curve': accumulation
    }


def generate_sampling_recommendations(df):
    """
    Genera recomendaciones completas de muestreo
    
    Args:
        df: DataFrame con datos
    
    Returns:
        dict: Recomendaciones completas
    """
    recommendations = []
    
    # Evaluar esfuerzo
    effort = calculate_sampling_effort(df)
    insufficient = effort[effort['Clasificacion_Esfuerzo'] == 'Insuficiente']
    
    if len(insufficient) > 0:
        recommendations.append({
            'category': 'Esfuerzo de Muestreo',
            'priority': 'Alta',
            'recommendation': f"{len(insufficient)} cámaras tienen esfuerzo insuficiente (<30 días). "
                            f"Se recomienda extender el período de muestreo."
        })
    
    # Evaluar falsos positivos
    false_triggers = identify_false_triggers(df)
    if false_triggers['percentage'] > 10:
        recommendations.append({
            'category': 'Falsos Positivos',
            'priority': 'Media',
            'recommendation': f"{false_triggers['percentage']:.1f}% de disparos son falsos positivos. "
                            f"Revise la colocación de cámaras y ajuste sensibilidad."
        })
    
    # Evaluar espaciamiento
    spacing = evaluate_camera_spacing(df)
    recommendations.extend([{
        'category': 'Espaciamiento',
        'priority': 'Media',
        'recommendation': rec['recommendation']
    } for rec in spacing.get('recommendations', [])])
    
    # Evaluar completitud
    completeness = calculate_species_accumulation_completeness(df)
    if completeness['completeness'] != 'Alta':
        recommendations.append({
            'category': 'Completitud del Muestreo',
            'priority': 'Media',
            'recommendation': completeness['recommendation']
        })
    
    return recommendations


def detect_camera_spacing_issues(df, min_distance=10):
    """
    Detecta cámaras que están muy cercanas entre sí (< min_distance metros)
    
    Args:
        df: DataFrame con datos de cámaras
        min_distance: Distancia mínima en metros (default: 10m)
    
    Returns:
        dict: Información detallada sobre cámaras cercanas
    """
    from scipy.spatial.distance import pdist, squareform
    
    # Obtener coordenadas únicas de cámaras
    cameras = df[['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Sitio_Agrupado']].drop_duplicates()
    
    if len(cameras) < 2:
        return {
            'has_issues': False,
            'n_groups': 0,
            'grouped_cameras': pd.DataFrame(),
            'recommendations': []
        }
    
    # Calcular matriz de distancias
    coords = cameras[['Coordenada_X_UTM', 'Coordenada_Y_UTM']].values
    distances = pdist(coords, metric='euclidean')
    dist_matrix = squareform(distances)
    
    # Encontrar pares de cámaras muy cercanas
    np.fill_diagonal(dist_matrix, np.inf)  # Ignorar diagonal
    
    close_pairs = []
    grouped_cameras_list = []
    
    for i in range(len(cameras)):
        for j in range(i + 1, len(cameras)):
            distance = dist_matrix[i, j]
            if distance < min_distance:
                cam1 = cameras.iloc[i]
                cam2 = cameras.iloc[j]
                close_pairs.append({
                    'Camara_1': cam1['Camara'],
                    'Camara_2': cam2['Camara'],
                    'Distancia_m': round(distance, 2),
                    'Sitio_Agrupado': cam1['Sitio_Agrupado']
                })
    
    # Agrupar cámaras por sitio
    if close_pairs:
        close_df = pd.DataFrame(close_pairs)
        
        # Contar grupos
        unique_groups = close_df['Sitio_Agrupado'].nunique()
        
        # Generar recomendaciones
        recommendations = []
        
        if unique_groups > 0:
            recommendations.append(
                f"⚠️ Se detectaron {len(close_pairs)} pares de cámaras a menos de {min_distance}m de distancia, "
                f"agrupadas en {unique_groups} sitios."
            )
            
            recommendations.append(
                f"💡 **Recomendación**: Para sitios independientes, separe las cámaras al menos 50-100 metros. "
                f"Si las cámaras cercanas son intencionales (ej: diferentes ángulos del mismo sendero), "
                f"esto es aceptable y serán tratadas como un solo sitio de muestreo."
            )
            
            # Calcular distancia promedio entre cámaras cercanas
            avg_close_distance = close_df['Distancia_m'].mean()
            recommendations.append(
                f"📏 La distancia promedio entre cámaras cercanas es {avg_close_distance:.1f}m. "
                f"Considere redistribuir para maximizar la cobertura espacial."
            )
        
        return {
            'has_issues': True,
            'n_groups': unique_groups,
            'n_close_pairs': len(close_pairs),
            'grouped_cameras': close_df,
            'avg_distance': close_df['Distancia_m'].mean(),
            'min_distance': close_df['Distancia_m'].min(),
            'recommendations': recommendations
        }
    else:
        return {
            'has_issues': False,
            'n_groups': 0,
            'grouped_cameras': pd.DataFrame(),
            'recommendations': ['✅ Todas las cámaras están bien espaciadas (> 10m de separación)']
        }

