"""
Módulo de procesamiento de datos para FORXIME/2
"""
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from utils.validators import (validate_utm_coordinates, validate_date, 
                              validate_time, validate_excel_format)
from utils.geospatial import group_cameras_by_distance, add_latlon_columns
from utils.helpers import calculate_independent_events, clean_species_name


def create_excel_template():
    """
    Crea un DataFrame de ejemplo para la plantilla Excel
    
    Returns:
        DataFrame: Plantilla con datos de ejemplo
    """
    template_data = {
        'Sitio': ['Sitio_A', 'Sitio_A', 'Sitio_B', 'Sitio_B'],
        'Camara': ['CAM001', 'CAM001', 'CAM002', 'CAM002'],
        'Coordenada_X_UTM': [500000, 500000, 501000, 501000],
        'Coordenada_Y_UTM': [2500000, 2500000, 2501000, 2501000],
        'Zona_UTM': ['12N', '12N', '12N', '12N'],
        'Especie_Categoria': ['Panthera onca', 'Tapirus bairdii', 'Panthera onca', 'Pecari tajacu'],
        'Fecha': ['01/01/2026', '02/01/2026', '01/01/2026', '03/01/2026'],
        'Hora': ['08:30:00', '14:45:00', '22:15:00', '06:20:00'],
        'Eventos_Independientes': [1, 1, 1, 2],
        'Es_Cria': ['No', 'No', 'No', 'Sí'],
        'Lactante': ['No', 'No', 'No', 'No'],
        'Periodo_Ensenanza': ['No', 'No', 'No', 'Sí'],
        'Rascando_Arboles': ['No', 'No', 'Sí', 'No'],
        'Usando_Letrina': ['No', 'No', 'No', 'No'],
        'Salud_Fisica': ['Buena', 'Buena', 'Buena', 'Buena'],
        'Observaciones': ['', '', 'Marcaje territorial', 'Grupo familiar']
    }
    
    return pd.DataFrame(template_data)


def process_manual_data(manual_data):
    """
    Procesa datos ingresados manualmente
    
    Args:
        manual_data: Lista de diccionarios con datos manuales
    
    Returns:
        DataFrame: Datos procesados
    """
    if not manual_data:
        return None
    
    df = pd.DataFrame(manual_data)
    
    # Limpiar nombres de especies
    if 'Especie_Categoria' in df.columns:
        df['Especie_Categoria'] = df['Especie_Categoria'].apply(clean_species_name)
    
    # Agregar columnas de lat/lon
    df = add_latlon_columns(df)
    
    return df


def process_excel_data(uploaded_file):
    """
    Procesa archivo Excel cargado
    
    Args:
        uploaded_file: Archivo Excel cargado
    
    Returns:
        tuple: (success, DataFrame or error_message)
    """
    try:
        # Leer Excel
        df = pd.read_excel(uploaded_file)
        
        # Validar formato
        is_valid, result = validate_excel_format(df)
        
        if not is_valid:
            return False, result
        
        # Limpiar nombres de especies
        df['Especie_Categoria'] = df['Especie_Categoria'].apply(clean_species_name)
        
        # Agregar columnas de lat/lon — OPTIMIZADO: solo calcular para ubicaciones únicas
        loc_cols = ['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']
        if all(c in df.columns for c in loc_cols):
            unique_locs = df[loc_cols].drop_duplicates(subset=['Camara'])
            unique_locs = add_latlon_columns(unique_locs)
            # Merge lat/lon back to the main df by camera name
            df = df.merge(
                unique_locs[['Camara', 'Latitud', 'Longitud']].drop_duplicates(),
                on='Camara', how='left'
            )
        else:
            df['Latitud'] = None
            df['Longitud'] = None

        
        # Calcular eventos independientes si no están especificados
        if 'Eventos_Independientes' not in df.columns or df['Eventos_Independientes'].isna().all():
            df = calculate_independent_events(df)
            df['Eventos_Independientes'] = df['Evento_Independiente'].astype(int)
        
        return True, df
    
    except Exception as e:
        return False, f"Error procesando archivo Excel: {str(e)}"


def group_sites(df, max_distance=10):
    """
    Agrupa sitios basado en distancia entre cámaras
    
    Args:
        df: DataFrame con datos de cámaras
        max_distance: Distancia máxima en metros para agrupar
    
    Returns:
        DataFrame: DataFrame con sitios agrupados
    """
    # Obtener cámaras únicas
    cameras_unique = df[['Camara', 'Coordenada_X_UTM', 'Coordenada_Y_UTM', 'Zona_UTM']].drop_duplicates()
    
    # Agrupar cámaras
    cameras_grouped = group_cameras_by_distance(cameras_unique, max_distance)
    
    # Merge con datos originales
    df = df.merge(cameras_grouped[['Camara', 'Sitio_Agrupado']], on='Camara', how='left')
    
    return df


def prepare_detection_history(df, period_days=7):
    """
    Prepara matriz de historia de detección para análisis de ocupación
    
    Args:
        df: DataFrame con datos procesados
        period_days: Duración de cada ocasión de muestreo en días (default: 7)
    
    Returns:
        dict: Diccionario con matrices de detección por especie
    """
    detection_histories = {}
    
    # Convertir fecha a datetime de forma segura
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df = df.dropna(subset=['Fecha'])
    
    # Agrupar por periodos dinámicos en base a la fecha de inicio general
    min_date = df['Fecha'].min()
    df['Dias_Desde_Inicio'] = (df['Fecha'] - min_date).dt.days
    df['Ocasiones'] = (df['Dias_Desde_Inicio'] // period_days) + 1
    
    for species in df['Especie_Categoria'].unique():
        species_data = df[df['Especie_Categoria'] == species]
        
        # Crear matriz de detección (sitios x ocasiones)
        detection_matrix = species_data.pivot_table(
            index='Sitio_Agrupado' if 'Sitio_Agrupado' in species_data.columns else 'Sitio',
            columns='Ocasiones',
            values='Eventos_Independientes',
            aggfunc='sum',
            fill_value=0
        )
        
        # Convertir a binario (1 si hubo detección, 0 si no)
        detection_binary = (detection_matrix > 0).astype(int)
        
        detection_histories[species] = {
            'counts': detection_matrix,
            'binary': detection_binary
        }
    
    return detection_histories


def calculate_basic_metrics(df):
    """
    Calcula métricas básicas del dataset
    
    Args:
        df: DataFrame con datos procesados
    
    Returns:
        dict: Diccionario con métricas básicas
    """
    metrics = {
        'total_records': len(df),
        'total_cameras': df['Camara'].nunique(),
        'total_sites': df['Sitio_Agrupado'].nunique() if 'Sitio_Agrupado' in df.columns else df['Sitio'].nunique(),
        'total_species': df['Especie_Categoria'].nunique(),
        'date_range': {
            'start': df['Fecha'].min(),
            'end': df['Fecha'].max(),
            'days': (pd.to_datetime(df['Fecha'].max(), errors='coerce') - pd.to_datetime(df['Fecha'].min(), errors='coerce')).days if not df.empty else 0
        },
        'total_independent_events': df['Eventos_Independientes'].sum() if 'Eventos_Independientes' in df.columns else len(df)
    }
    
    return metrics


def identify_non_wildlife(df):
    """
    Identifica registros que no son fauna silvestre
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Registros no-fauna silvestre
    """
    # Cargar configuración centralizada
    import os, json
    # Determinar ruta raíz (TANIA/)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(root_dir, 'config', 'species_config.json')
    
    non_wildlife_keywords = [
        'humano', 'human', 'persona', 'person', 'gente', 'people',
        'perro', 'dog', 'can', 'domestico', 'domestic',
        'gato', 'cat', 'feline domestic',
        'vaca', 'cow', 'ganado', 'cattle', 'bovino',
        'caballo', 'horse', 'equino',
        'vehiculo', 'vehicle', 'carro', 'car', 'moto', 'motorcycle',
        'bicicleta', 'bicycle', 'bike'
    ]
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                exclude = config.get("categories", {}).get("exclude", {}).get("keywords", [])
                anthro = config.get("categories", {}).get("anthropogenic", {}).get("keywords", [])
                domestic = config.get("categories", {}).get("domestic", {}).get("keywords", [])
                non_wildlife_keywords = list(set(non_wildlife_keywords + exclude + anthro + domestic))
        except:
            pass
    
    # Crear máscara para identificar no-fauna
    mask = df['Especie_Categoria'].str.lower().str.contains('|'.join(non_wildlife_keywords), na=False)
    
    non_wildlife_df = df[mask].copy()
    non_wildlife_df['Categoria_Antropogenica'] = non_wildlife_df['Especie_Categoria'].apply(
        lambda x: categorize_anthropogenic(x)
    )
    
    return non_wildlife_df


def categorize_anthropogenic(species_name):
    """
    Categoriza registros antropogénicos
    
    Args:
        species_name: Nombre de la especie/categoría
    
    Returns:
        str: Categoría antropogénica
    """
    species_lower = species_name.lower()
    
    if any(word in species_lower for word in ['vacio', 'vacío', 'empty', 'desconocido', 'unknown', 'sin identificar']):
        return 'Excluido'
    elif any(word in species_lower for word in ['humano', 'human', 'persona', 'person', 'gente', 'people']):
        return 'Humano'
    elif any(word in species_lower for word in ['perro', 'dog']):
        return 'Perro Doméstico'
    elif any(word in species_lower for word in ['gato', 'cat']):
        return 'Gato Doméstico'
    elif any(word in species_lower for word in ['vaca', 'cow', 'ganado', 'cattle', 'bovino']):
        return 'Ganado'
    elif any(word in species_lower for word in ['vehiculo', 'vehicle', 'carro', 'car', 'moto']):
        return 'Vehículo'
    else:
        return 'Otro Antropogénico'


def filter_wildlife_only(df):
    """
    Filtra solo registros de fauna silvestre
    
    Args:
        df: DataFrame con todos los datos
    
    Returns:
        DataFrame: Solo fauna silvestre
    """
    non_wildlife = identify_non_wildlife(df)
    wildlife_df = df[~df.index.isin(non_wildlife.index)].copy()
    
    return wildlife_df


def add_behavior_data(df, behavior_records):
    """
    Agrega datos de comportamiento al DataFrame
    
    Args:
        df: DataFrame principal
        behavior_records: Lista de diccionarios con observaciones de comportamiento
    
    Returns:
        DataFrame: DataFrame con datos de comportamiento agregados
    """
    if not behavior_records:
        return df
    
    behavior_df = pd.DataFrame(behavior_records)
    
    # Merge con DataFrame principal
    # Asumiendo que behavior_records tiene identificadores únicos para cada registro
    df = df.merge(behavior_df, how='left', left_index=True, right_on='record_id')
    
    return df


def summarize_by_camera(df):
    """
    Resume datos por cámara
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Resumen por cámara
    """
    summary = df.groupby('Camara', observed=True).agg({

        'Especie_Categoria': 'nunique',
        'Eventos_Independientes': 'sum',
        'Fecha': lambda x: (x.max() - x.min()).days + 1
    }).reset_index()
    
    summary.columns = ['Camara', 'Riqueza_Especies', 'Total_Eventos', 'Dias_Activa']
    
    # Calcular tasa de captura
    summary['Tasa_Captura_100dias'] = (summary['Total_Eventos'] / summary['Dias_Activa']) * 100
    
    return summary


def summarize_by_species(df):
    """
    Resume datos por especie
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Resumen por especie
    """
    summary = df.groupby('Especie_Categoria', observed=True).agg({

        'Camara': 'nunique',
        'Eventos_Independientes': 'sum',
        'Sitio_Agrupado': 'nunique' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    }).reset_index()
    
    summary.columns = ['Especie', 'N_Camaras', 'Total_Eventos', 'N_Sitios']
    
    # Calcular ocupación naive
    total_sites = df['Sitio_Agrupado'].nunique() if 'Sitio_Agrupado' in df.columns else df['Sitio'].nunique()
    summary['Ocupacion_Naive'] = summary['N_Sitios'] / total_sites
    
    # Ordenar por total de eventos
    summary = summary.sort_values('Total_Eventos', ascending=False)
    
    return summary
