"""
Funciones de validación para FORXIME/2
"""
import re
from datetime import datetime
import pandas as pd
import numpy as np


def validate_utm_coordinates(x, y, zone):
    """
    Valida coordenadas UTM
    
    Args:
        x: Coordenada Este (X)
        y: Coordenada Norte (Y)
        zone: Zona UTM (ej: '12N', '13S')
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Validar que sean números
        x = float(x)
        y = float(y)
        
        # Validar rango de coordenadas UTM
        if not (166000 <= x <= 834000):
            return False, "Coordenada X fuera de rango válido (166000-834000)"
        
        if not (0 <= y <= 10000000):
            return False, "Coordenada Y fuera de rango válido (0-10000000)"
        
        # Validar formato de zona UTM
        zone_pattern = r'^([1-9]|[1-5][0-9]|60)[N|S]$'
        if not re.match(zone_pattern, str(zone).upper()):
            return False, "Formato de zona UTM inválido (debe ser 1-60 seguido de N o S)"
        
        return True, ""
    
    except (ValueError, TypeError):
        return False, "Las coordenadas deben ser números válidos"


def validate_date(date_str):
    """
    Valida formato de fecha
    
    Args:
        date_str: Fecha en string, pandas Timestamp, o datetime object
    
    Returns:
        tuple: (is_valid, datetime_object or error_message)
    """
    # Si ya es un objeto datetime o pandas Timestamp, retornar directamente
    if isinstance(date_str, datetime):
        return True, date_str
    
    if pd.notna(date_str) and hasattr(date_str, 'to_pydatetime'):
        # Es un pandas Timestamp
        try:
            return True, date_str.to_pydatetime()
        except:
            pass
    
    # Si es numpy datetime64
    if isinstance(date_str, np.datetime64):
        try:
            return True, pd.Timestamp(date_str).to_pydatetime()
        except:
            pass
    
    # Intentar parsear como string
    date_formats = [
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%m/%d/%Y',  # Formato americano
        '%Y%m%d'     # Formato compacto
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(str(date_str).strip(), fmt)
            return True, date_obj
        except (ValueError, AttributeError):
            continue
    
    # Intentar con pd.to_datetime como último recurso
    try:
        date_obj = pd.to_datetime(date_str)
        if pd.notna(date_obj):
            return True, date_obj.to_pydatetime()
    except:
        pass
    
    return False, "Formato de fecha inválido. Use DD/MM/AAAA o AAAA-MM-DD"


def validate_time(time_str):
    """
    Valida formato de hora
    
    Args:
        time_str: Hora en string, datetime.time, o pandas Timestamp
    
    Returns:
        tuple: (is_valid, time_object or error_message)
    """
    # Si ya es un objeto time
    if hasattr(time_str, 'hour') and hasattr(time_str, 'minute'):
        try:
            if isinstance(time_str, datetime):
                return True, time_str.time()
            else:
                return True, time_str
        except:
            pass
    
    # Si es pandas Timestamp
    if pd.notna(time_str) and hasattr(time_str, 'to_pydatetime'):
        try:
            return True, time_str.to_pydatetime().time()
        except:
            pass
    
    # Intentar parsear como string
    time_formats = [
        '%H:%M:%S',
        '%H:%M',
        '%I:%M:%S %p',
        '%I:%M %p'
    ]
    
    for fmt in time_formats:
        try:
            time_obj = datetime.strptime(str(time_str).strip(), fmt).time()
            return True, time_obj
        except (ValueError, AttributeError):
            continue
    
    # Intentar con pd.to_datetime como último recurso
    try:
        time_obj = pd.to_datetime(time_str, format='mixed')
        if pd.notna(time_obj):
            return True, time_obj.time()
    except:
        pass
    
    return False, "Formato de hora inválido. Use HH:MM:SS o HH:MM"


def validate_excel_format(df):
    """
    Valida que el DataFrame del Excel tenga las columnas requeridas.
    TOLERANTE: No bloquea la carga por registros individuales con errores.
    Los registros con fechas u horas inválidas se eliminan más adelante en el pipeline.
    
    Args:
        df: DataFrame de pandas
    
    Returns:
        tuple: (is_valid, error_message or validated_df)
    """
    # Columnas absolutamente requeridas
    required_columns = [
        'Sitio',
        'Camara',
        'Especie_Categoria',
        'Fecha',
        'Hora',
        'Eventos_Independientes'
    ]
    
    # Verificar columnas requeridas (esto SÍ debe bloquear — es un error de estructura)
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Columnas faltantes: {', '.join(missing_columns)}"
    
    # Todo lo demás es tolerante: solo verificar estructura, NO rechazar por datos individuales
    return True, df




def validate_species_name(species_name):
    """
    Valida nombre de especie
    
    Args:
        species_name: Nombre de la especie
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not species_name or str(species_name).strip() == "":
        return False, "El nombre de especie no puede estar vacío"
    
    if len(str(species_name)) > 100:
        return False, "El nombre de especie es demasiado largo (máximo 100 caracteres)"
    
    return True, ""


def validate_independent_events(events):
    """
    Valida número de eventos independientes
    
    Args:
        events: Número de eventos
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        events = int(events)
        if events < 0:
            return False, "El número de eventos no puede ser negativo"
        if events > 10000:
            return False, "El número de eventos parece excesivo (máximo 10000)"
        return True, ""
    except (ValueError, TypeError):
        return False, "El número de eventos debe ser un número entero"


def check_missing_data(df):
    """
    Verifica datos faltantes en el DataFrame
    
    Args:
        df: DataFrame de pandas
    
    Returns:
        dict: Resumen de datos faltantes por columna
    """
    missing_summary = {}
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            missing_summary[col] = {
                'count': int(missing_count),
                'percentage': round((missing_count / len(df)) * 100, 2)
            }
    
    return missing_summary
