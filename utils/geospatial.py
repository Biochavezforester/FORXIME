"""
Funciones geoespaciales para FORXIME/2
"""
import numpy as np
import pandas as pd
# Heavy geospatial imports moved inside functions (Lazy Loading)


def utm_to_latlon(x, y, zone_number, zone_letter):
    """
    Convierte coordenadas UTM a latitud/longitud
    
    Args:
        x: Coordenada Este (X) en UTM
        y: Coordenada Norte (Y) en UTM
        zone_number: Número de zona UTM (1-60)
        zone_letter: Letra de zona UTM (N o S)
    
    Returns:
        tuple: (latitude, longitude)
    """
    try:
        # Determinar hemisferio
        northern = zone_letter.upper() >= 'N'
        
        # Convertir usando utm library
        import utm
        lat, lon = utm.to_latlon(x, y, zone_number, northern=northern)
        
        return lat, lon
    
    except Exception as e:
        print(f"Error en conversión UTM a lat/lon: {e}")
        return None, None


def latlon_to_utm(lat, lon):
    """
    Convierte latitud/longitud a coordenadas UTM
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        tuple: (x, y, zone_number, zone_letter)
    """
    try:
        import utm
        x, y, zone_number, zone_letter = utm.from_latlon(lat, lon)
        return x, y, zone_number, zone_letter
    
    except Exception as e:
        print(f"Error en conversión lat/lon a UTM: {e}")
        return None, None, None, None


def calculate_distance(coord1, coord2):
    """
    Calcula distancia euclidiana entre dos puntos en metros
    
    Args:
        coord1: tuple (x, y) en UTM
        coord2: tuple (x, y) en UTM
    
    Returns:
        float: Distancia en metros
    """
    x1, y1 = coord1
    x2, y2 = coord2
    
    distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance


def group_cameras_by_distance(cameras_df, max_distance=10):
    """
    Agrupa cámaras que están a menos de max_distance metros
    
    Args:
        cameras_df: DataFrame con columnas ['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']
        max_distance: Distancia máxima en metros para agrupar (default: 10)
    
    Returns:
        DataFrame: DataFrame original con columna adicional 'Sitio_Agrupado'
    """
    # Crear copia del DataFrame
    df = cameras_df.copy()
    
    # Agrupar por zona UTM (solo se pueden comparar distancias en la misma zona)
    df['Sitio_Agrupado'] = df['Camara']  # Inicialmente cada cámara es su propio sitio
    
    for zone in df['Zona_UTM'].unique():
        zone_mask = df['Zona_UTM'] == zone
        zone_cameras = df[zone_mask].copy()
        
        if len(zone_cameras) < 2:
            continue
        
        # Extraer coordenadas
        coords = zone_cameras[['Coordenada_X_UTM', 'Coordenada_Y_UTM']].values
        
        # Calcular matriz de distancias
        from scipy.spatial.distance import cdist
        dist_matrix = cdist(coords, coords, metric='euclidean')
        
        # Agrupar cámaras cercanas
        groups = {}
        group_id = 0
        assigned = set()
        
        for i in range(len(zone_cameras)):
            if i in assigned:
                continue
            
            # Encontrar todas las cámaras a menos de max_distance
            close_cameras = np.where(dist_matrix[i] <= max_distance)[0]
            
            # Crear nuevo grupo
            group_name = f"Sitio_Grupo_{zone}_{group_id}"
            for cam_idx in close_cameras:
                if cam_idx not in assigned:
                    groups[zone_cameras.index[cam_idx]] = group_name
                    assigned.add(cam_idx)
            
            group_id += 1
        
        # Asignar grupos al DataFrame
        for idx, group_name in groups.items():
            df.loc[idx, 'Sitio_Agrupado'] = group_name
    
    return df


def calculate_centroid(cameras_df):
    """
    Calcula el centroide de un conjunto de cámaras
    
    Args:
        cameras_df: DataFrame con coordenadas UTM
    
    Returns:
        tuple: (centroid_x, centroid_y)
    """
    centroid_x = cameras_df['Coordenada_X_UTM'].mean()
    centroid_y = cameras_df['Coordenada_Y_UTM'].mean()
    
    return centroid_x, centroid_y


def get_bounding_box(cameras_df):
    """
    Obtiene el bounding box de las cámaras
    
    Args:
        cameras_df: DataFrame con coordenadas
    
    Returns:
        dict: {'min_lat', 'max_lat', 'min_lon', 'max_lon'}
    """
    # Convertir todas las coordenadas a lat/lon
    lats = []
    lons = []
    
    for idx, row in cameras_df.iterrows():
        zone_number = int(row['Zona_UTM'][:-1])
        zone_letter = row['Zona_UTM'][-1]
        
        lat, lon = utm_to_latlon(
            row['Coordenada_X_UTM'],
            row['Coordenada_Y_UTM'],
            zone_number,
            zone_letter
        )
        
        if lat is not None and lon is not None:
            lats.append(lat)
            lons.append(lon)
    
    if not lats or not lons:
        return None
    
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons),
        'center_lat': np.mean(lats),
        'center_lon': np.mean(lons)
    }


def calculate_study_area(cameras_df):
    """
    Calcula el área aproximada del estudio en km²
    
    Args:
        cameras_df: DataFrame con coordenadas UTM
    
    Returns:
        float: Área en km²
    """
    if len(cameras_df) < 3:
        return 0
    
    # Obtener coordenadas
    coords = cameras_df[['Coordenada_X_UTM', 'Coordenada_Y_UTM']].values
    
    # Calcular convex hull area (aproximación simple)
    from scipy.spatial import ConvexHull
    
    try:
        hull = ConvexHull(coords)
        area_m2 = hull.area  # En 2D, area es el área superficial; volume es el área para hulls 2D en versiones recientes.
        area_km2 = area_m2 / 1_000_000  # Convertir a km²
        return area_km2
    except:
        return 0


def add_latlon_columns(df):
    """
    Agrega columnas de latitud y longitud al DataFrame de forma optimizada.
    Mapea solo coordenadas únicas para evitar miles de cálculos redundantes.
    """
    df = df.copy()
    
    # Columnas necesarias
    if not all(col in df.columns for col in ['Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']):
        return df
        
    # 1. Identificar combinaciones únicas de coordenadas (Súper rápido)
    unique_coords = df[['Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']].drop_duplicates().copy()
    
    # 2. Calcular Lat/Lon solo para los únicos (Ej: de 50,000 pasamos a 50 cálculos)
    lats = []
    lons = []
    
    import utm
    for _, row in unique_coords.iterrows():
        try:
            zone_str = str(row['Zona_UTM']).strip()
            zone_number = int(zone_str[:-1])
            zone_letter = zone_str[-1].upper()
            northern = zone_letter >= 'N'
            
            lat, lon = utm.to_latlon(
                row['Coordenada_X_UTM'], 
                row['Coordenada_Y_UTM'], 
                zone_number, 
                northern=northern
            )
            lats.append(lat)
            lons.append(lon)
        except:
            lats.append(None)
            lons.append(None)
            
    unique_coords['Latitud'] = lats
    unique_coords['Longitud'] = lons
    
    # 3. Mapear de vuelta al DataFrame original (Operación vectorial instantánea)
    df = df.merge(unique_coords, on=['Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM'], how='left')
    
    return df
