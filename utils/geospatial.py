"""
Funciones geoespaciales para FORXIME/2
"""
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial.distance import cdist
import utm


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
            group_name = f"Sitio_{group_id + 1}"
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
    Obtiene el bounding box de las cámaras.
    OPTIMIZADO: Usa pyproj vectorizado en lugar de iterar fila por fila.
    
    Args:
        cameras_df: DataFrame con coordenadas
    
    Returns:
        dict: {'min_lat', 'max_lat', 'min_lon', 'max_lon'}
    """
    # CRITICAL: DataFrame-level check (faster and safer)
    required = ['Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']
    if not all(col in cameras_df.columns for col in required):
        return None
    
    # Filter valid rows
    valid = cameras_df[required].dropna()
    valid = valid[valid['Zona_UTM'].astype(str).str.len() >= 2]
    
    if valid.empty:
        return None
    
    all_lats = []
    all_lons = []
    
    for zone, group in valid.groupby('Zona_UTM'):
        val_zona = str(zone).strip().upper()
        if len(val_zona) < 2:
            continue
        try:
            zone_number = int(val_zona[:-1])
            zone_letter = val_zona[-1]
            northern = zone_letter >= 'N'
            
            epsg_code = 32600 + zone_number if northern else 32700 + zone_number
            transformer = Transformer.from_crs(f"epsg:{epsg_code}", "epsg:4326", always_xy=True)
            
            lons, lats = transformer.transform(
                group['Coordenada_X_UTM'].values,
                group['Coordenada_Y_UTM'].values
            )
            all_lats.extend(lats)
            all_lons.extend(lons)
        except Exception:
            continue
    
    if not all_lats or not all_lons:
        return None
    
    return {
        'min_lat': min(all_lats),
        'max_lat': max(all_lats),
        'min_lon': min(all_lons),
        'max_lon': max(all_lons),
        'center_lat': np.mean(all_lats),
        'center_lon': np.mean(all_lons)
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
        area_m2 = hull.volume  # En 2D, volume es el área
        area_km2 = area_m2 / 1_000_000  # Convertir a km²
        return area_km2
    except:
        return 0


def add_latlon_columns(df):
    """
    Agrega columnas de latitud y longitud al DataFrame.
    OPTIMIZADO: Usa pyproj vectorizado en lugar de iterar fila por fila.
    
    Args:
        df: DataFrame con coordenadas UTM
    
    Returns:
        DataFrame: DataFrame con columnas 'Latitud' y 'Longitud' agregadas
    """
    df = df.copy()
    
    # Initialize with NaNs
    df['Latitud'] = np.nan
    df['Longitud'] = np.nan
    
    # Check for required columns
    required_cols = ['Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']
    if not all(col in df.columns for col in required_cols):
        return df
        
    # Drop rows with missing critical UTM data just for the conversion
    valid_mask = df[required_cols].notna().all(axis=1) & (df['Zona_UTM'].astype(str).str.len() >= 2)
    
    if not valid_mask.any():
        return df
        
    # Group by Zone to minimize Transformer creations (since zone defines the projection)
    for zone, group in df[valid_mask].groupby('Zona_UTM'):
        val_zona = str(zone).strip().upper()
        if len(val_zona) < 2: continue
        
        try:
            zone_number = int(val_zona[:-1])
            zone_letter = val_zona[-1]
            northern = zone_letter >= 'N'
            
            # Create a vectorised pyproj Transformer for this specific zone
            # EPSG: 326xx for North, 327xx for South (xx = zone number)
            epsg_code = 32600 + zone_number if northern else 32700 + zone_number
            transformer = Transformer.from_crs(f"epsg:{epsg_code}", "epsg:4326", always_xy=True)
            
            # Apply transformation in bulk
            lons, lats = transformer.transform(
                group['Coordenada_X_UTM'].values, 
                group['Coordenada_Y_UTM'].values
            )
            
            # Assign back to main dataframe
            df.loc[group.index, 'Longitud'] = lons
            df.loc[group.index, 'Latitud'] = lats
            
        except Exception as e:
            print(f"Error vectorizando zona {zone}: {e}")
            
    return df

