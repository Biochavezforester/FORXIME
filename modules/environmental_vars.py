"""
Módulo de variables ambientales para FORXIME/2
Extrae variables ambientales basadas en coordenadas geográficas
"""
import pandas as pd
import numpy as np
import requests
from geopy.distance import geodesic
import warnings
warnings.filterwarnings('ignore')


def query_overpass_api(lat, lon, radius=5000, feature_type='waterway'):
    """
    Consulta Overpass API de OpenStreetMap
    
    Args:
        lat: Latitud
        lon: Longitud
        radius: Radio de búsqueda en metros
        feature_type: Tipo de característica ('waterway', 'place', etc.)
    
    Returns:
        dict: Resultados de la consulta
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    if feature_type == 'waterway':
        query = f"""
        [out:json];
        (
          way["waterway"](around:{radius},{lat},{lon});
          relation["waterway"](around:{radius},{lat},{lon});
        );
        out center;
        """
    elif feature_type == 'city':
        query = f"""
        [out:json];
        (
          node["place"~"city|town|village"](around:{radius},{lat},{lon});
        );
        out;
        """
    else:
        return None
    
    try:
        response = requests.post(overpass_url, data={'data': query}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error consultando Overpass API: {e}")
        return None


def calculate_distance_to_nearest_river(lat, lon):
    """
    Calcula distancia al río más cercano usando OpenStreetMap
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        float: Distancia en metros (None si no se encuentra)
    """
    # Buscar ríos en un radio de 50km
    result = query_overpass_api(lat, lon, radius=50000, feature_type='waterway')
    
    if not result or 'elements' not in result or len(result['elements']) == 0:
        return None
    
    min_distance = float('inf')
    
    for element in result['elements']:
        if 'center' in element:
            river_lat = element['center']['lat']
            river_lon = element['center']['lon']
        elif 'lat' in element and 'lon' in element:
            river_lat = element['lat']
            river_lon = element['lon']
        else:
            continue
        
        distance = geodesic((lat, lon), (river_lat, river_lon)).meters
        min_distance = min(min_distance, distance)
    
    return min_distance if min_distance != float('inf') else None


def calculate_distance_to_nearest_city(lat, lon):
    """
    Calcula distancia a la ciudad más cercana usando OpenStreetMap
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        dict: Información de la ciudad más cercana
    """
    # Buscar ciudades en un radio de 100km
    result = query_overpass_api(lat, lon, radius=100000, feature_type='city')
    
    if not result or 'elements' not in result or len(result['elements']) == 0:
        return None
    
    min_distance = float('inf')
    nearest_city = None
    
    for element in result['elements']:
        if 'lat' not in element or 'lon' not in element:
            continue
        
        city_lat = element['lat']
        city_lon = element['lon']
        
        distance = geodesic((lat, lon), (city_lat, city_lon)).meters
        
        if distance < min_distance:
            min_distance = distance
            nearest_city = {
                'name': element.get('tags', {}).get('name', 'Unknown'),
                'place_type': element.get('tags', {}).get('place', 'unknown'),
                'distance_m': distance,
                'distance_km': distance / 1000
            }
    
    return nearest_city


def get_elevation_from_api(lat, lon):
    """
    Obtiene elevación usando API gratuita
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        float: Elevación en metros
    """
    try:
        # Usar Open-Elevation API
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                return data['results'][0]['elevation']
        
        return None
    except Exception as e:
        print(f"Error obteniendo elevación: {e}")
        return None


def estimate_biome(lat, lon, elevation=None):
    """
    Estima el bioma basado en coordenadas y elevación
    (Estimación simplificada basada en latitud y elevación)
    
    Args:
        lat: Latitud
        lon: Longitud
        elevation: Elevación en metros (opcional)
    
    Returns:
        str: Tipo de bioma estimado
    """
    abs_lat = abs(lat)
    
    # Estimación muy simplificada
    if elevation and elevation > 3000:
        return "Montaña Alta"
    elif elevation and elevation > 1500:
        return "Bosque Montano"
    elif abs_lat < 10:
        return "Bosque Tropical"
    elif abs_lat < 23.5:
        if elevation and elevation > 1000:
            return "Bosque Nuboso"
        else:
            return "Bosque Subtropical"
    elif abs_lat < 35:
        return "Bosque Templado"
    elif abs_lat < 50:
        return "Bosque Boreal"
    else:
        return "Tundra"


def calculate_forest_cover_estimate(lat, lon):
    """
    Estimación de cobertura forestal
    (Versión simplificada - idealmente usar Google Earth Engine)
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        dict: Estimación de cobertura forestal
    """
    # Esta es una función placeholder
    # En producción, se usaría Google Earth Engine o similar
    
    return {
        'forest_cover_pct': None,
        'note': 'Requiere integración con Google Earth Engine para datos precisos',
        'method': 'placeholder'
    }


def calculate_human_modification_index(lat, lon):
    """
    Calcula índice de modificación humana basado en distancia a ciudades
    (Versión simplificada)
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        dict: Índice de modificación humana
    """
    city_info = calculate_distance_to_nearest_city(lat, lon)
    
    if not city_info:
        return {
            'hmi_score': 0,
            'category': 'Remoto',
            'note': 'No se encontraron ciudades cercanas'
        }
    
    distance_km = city_info['distance_km']
    
    # Calcular score (0-100, donde 100 es alta modificación)
    if distance_km < 5:
        score = 90
        category = 'Muy Alta Modificación'
    elif distance_km < 20:
        score = 70
        category = 'Alta Modificación'
    elif distance_km < 50:
        score = 50
        category = 'Modificación Moderada'
    elif distance_km < 100:
        score = 30
        category = 'Baja Modificación'
    else:
        score = 10
        category = 'Muy Baja Modificación'
    
    return {
        'hmi_score': score,
        'category': category,
        'distance_to_city_km': distance_km,
        'nearest_city': city_info['name']
    }


def extract_environmental_variables(lat, lon):
    """
    Extrae todas las variables ambientales para una ubicación
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        dict: Todas las variables ambientales
    """
    print(f"Extrayendo variables ambientales para ({lat:.4f}, {lon:.4f})...")
    
    variables = {}
    
    # Distancia a río
    try:
        river_dist = calculate_distance_to_nearest_river(lat, lon)
        variables['distance_to_river_m'] = river_dist
        variables['distance_to_river_km'] = river_dist / 1000 if river_dist else None
    except Exception as e:
        print(f"Error calculando distancia a río: {e}")
        variables['distance_to_river_m'] = None
        variables['distance_to_river_km'] = None
    
    # Distancia a ciudad
    try:
        city_info = calculate_distance_to_nearest_city(lat, lon)
        if city_info:
            variables['distance_to_city_km'] = city_info['distance_km']
            variables['nearest_city'] = city_info['name']
            variables['city_type'] = city_info['place_type']
        else:
            variables['distance_to_city_km'] = None
            variables['nearest_city'] = None
            variables['city_type'] = None
    except Exception as e:
        print(f"Error calculando distancia a ciudad: {e}")
        variables['distance_to_city_km'] = None
        variables['nearest_city'] = None
    
    # Elevación
    try:
        elevation = get_elevation_from_api(lat, lon)
        variables['elevation_m'] = elevation
    except Exception as e:
        print(f"Error obteniendo elevación: {e}")
        variables['elevation_m'] = None
    
    # Bioma
    try:
        biome = estimate_biome(lat, lon, variables.get('elevation_m'))
        variables['biome'] = biome
    except Exception as e:
        print(f"Error estimando bioma: {e}")
        variables['biome'] = None
    
    # Índice de modificación humana
    try:
        hmi = calculate_human_modification_index(lat, lon)
        variables['human_modification_index'] = hmi['hmi_score']
        variables['hmi_category'] = hmi['category']
    except Exception as e:
        print(f"Error calculando HMI: {e}")
        variables['human_modification_index'] = None
        variables['hmi_category'] = None
    
    # Cobertura forestal (placeholder)
    variables['forest_cover_pct'] = None
    variables['forest_cover_note'] = 'Requiere Google Earth Engine'
    
    return variables


def extract_variables_for_all_sites(df):
    """
    Extrae variables ambientales para todos los sitios
    
    Args:
        df: DataFrame con coordenadas
    
    Returns:
        DataFrame: Variables ambientales por sitio
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Obtener coordenadas únicas por sitio
    site_coords = df.groupby(site_column).agg({
        'Latitud': 'first',
        'Longitud': 'first'
    }).reset_index()
    
    # Extraer variables para cada sitio
    all_variables = []
    
    for idx, row in site_coords.iterrows():
        site = row[site_column]
        lat = row['Latitud']
        lon = row['Longitud']
        
        if pd.isna(lat) or pd.isna(lon):
            continue
        
        print(f"Procesando sitio {site}...")
        
        variables = extract_environmental_variables(lat, lon)
        variables['Sitio'] = site
        
        all_variables.append(variables)
    
    variables_df = pd.DataFrame(all_variables)
    
    return variables_df


def analyze_environmental_influence(df, variables_df):
    """
    Analiza la influencia de variables ambientales en ocupación/abundancia
    
    Args:
        df: DataFrame con datos de especies
        variables_df: DataFrame con variables ambientales
    
    Returns:
        dict: Resultados del análisis
    """
    from scipy.stats import spearmanr
    
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Calcular métricas por sitio
    site_metrics = df.groupby(site_column).agg({
        'Especie_Categoria': 'nunique',
        'Eventos_Independientes': 'sum'
    }).reset_index()
    
    site_metrics.columns = ['Sitio', 'Riqueza', 'Abundancia']
    
    # Merge con variables ambientales
    merged = site_metrics.merge(variables_df, on='Sitio', how='inner')
    
    # Calcular correlaciones
    correlations = {}
    
    env_vars = ['distance_to_river_km', 'distance_to_city_km', 'elevation_m', 
                'human_modification_index']
    
    for var in env_vars:
        if var in merged.columns and merged[var].notna().sum() > 3:
            # Correlación con riqueza
            valid_data = merged[[var, 'Riqueza']].dropna()
            if len(valid_data) > 3:
                corr_r, p_val_r = spearmanr(valid_data[var], valid_data['Riqueza'])
                
                # Correlación con abundancia
                valid_data_a = merged[[var, 'Abundancia']].dropna()
                corr_a, p_val_a = spearmanr(valid_data_a[var], valid_data_a['Abundancia'])
                
                correlations[var] = {
                    'richness_correlation': corr_r,
                    'richness_pvalue': p_val_r,
                    'abundance_correlation': corr_a,
                    'abundance_pvalue': p_val_a
                }
    
    return {
        'correlations': correlations,
        'merged_data': merged
    }
