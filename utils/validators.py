"""
Validadores para FORXIME/2
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime

def validate_utm_coordinates(x, y, zone):
    """Valida coordenadas UTM básicas."""
    try:
        x = float(x)
        y = float(y)
        if not (166000 <= x <= 834000):
            return False, "Easting (X) fuera de rango"
        if not (0 <= y <= 10000000):
            return False, "Northing (Y) fuera de rango"
        if not re.match(r'^([1-9]|[1-5][0-9]|60)[N|S]$', str(zone).upper()):
            return False, "Zona UTM inválida"
        return True, "OK"
    except:
        return False, "Formato numérico inválido"

def validate_date(date_str):
    """Valida formato de fecha DD/MM/YYYY."""
    try:
        if isinstance(date_str, datetime):
            return True, "OK"
        datetime.strptime(str(date_str), '%d/%m/%Y')
        return True, "OK"
    except:
        return False, "Formato de fecha inválido. Use DD/MM/YYYY"

def validate_time(time_str):
    """Valida formato de hora HH:MM:SS."""
    try:
        if isinstance(time_str, (datetime, pd.Timestamp)):
            return True, "OK"
        # Intentar varios formatos
        for fmt in ('%H:%M:%S', '%H:%M'):
            try:
                datetime.strptime(str(time_str), fmt)
                return True, "OK"
            except:
                continue
        return False, "Formato de hora inválido"
    except:
        return False, "Formato de hora inválido"

def validate_excel_format(df):
    """
    Valida que el DataFrame del Excel tenga las columnas requeridas (Versión Estructural Ultra-Rápida)
    """
    # Columnas absolutamente requeridas
    required_columns = ['Sitio', 'Camara', 'Especie_Categoria', 'Fecha', 'Hora']
    
    # 1. Verificar presencia de columnas (Operación de milisegundos)
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Faltan columnas requeridas: {', '.join(missing_columns)}"
    
    # 2. CONFIANZA TOTAL: Para archivos grandes (5MB+), no validamos filas individuales aquí.
    # El procesador se encargará de esto durante la fase de análisis (Botón Cohete).
    
    return True, df

def validate_species_name(species_name):
    """Valida nombre de especie."""
    if pd.isna(species_name) or str(species_name).strip() == "":
        return False, "El nombre de la especie no puede estar vacío"
    return True, "OK"
