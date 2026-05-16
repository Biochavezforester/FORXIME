"""
Funciones auxiliares generales para FORXIME/2
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os


def load_translations(language='es'):
    """
    Carga las traducciones del archivo JSON
    
    Args:
        language: Código de idioma ('es' o 'en')
    
    Returns:
        dict: Diccionario con traducciones
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'config', 'translations.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        return translations.get(language, translations['es'])
    
    except Exception as e:
        print(f"Error cargando traducciones: {e}")
        return {}


def get_text(key, language='es'):
    """
    Obtiene texto traducido
    
    Args:
        key: Clave del texto
        language: Idioma
    
    Returns:
        str: Texto traducido
    """
    translations = load_translations(language)
    return translations.get(key, key)


def calculate_independent_events(df, time_threshold=30, grouping_col='Camara'):
    """
    Calcula eventos independientes basado en un umbral de tiempo y ubicación.
    OPTIMIZADO: Usa operaciones vectorizadas (groupby + diff) en lugar de loops fila por fila.
    Los resultados son matemáticamente idénticos a la versión anterior.

    Args:
        df: DataFrame con columnas 'Camara', 'Especie_Categoria', 'Fecha', 'Hora'
        time_threshold: Umbral en minutos (default: 30)
        grouping_col: Columna para agrupar (Camara o Sitio_Agrupado)

    Returns:
        DataFrame: DataFrame con columna 'Evento_Independiente' (True/False)
    """
    df = df.copy()

    # Asegurar que la columna de agrupamiento existe
    if grouping_col not in df.columns:
        grouping_col = 'Camara'

    # Combinar fecha y hora de forma vectorizada
    df['DateTime'] = pd.to_datetime(
        df['Fecha'].astype(str) + ' ' + df['Hora'].astype(str),
        errors='coerce'
    )

    # Ordenar para que diff sea correcto dentro de cada grupo
    df = df.sort_values([grouping_col, 'Especie_Categoria', 'DateTime'])

    # Calcular delta de tiempo entre filas CONSECUTIVAS dentro del mismo grupo (vectorizado)
    delta_minutes = (
        df.groupby([grouping_col, 'Especie_Categoria'])['DateTime']
        .diff()                          # NaT para el primer elemento de cada grupo
        .dt.total_seconds()
        .div(60)                         # Convertir a minutos
    )

    # Independiente si: es el primero del grupo (delta=NaN → fillna(inf)) o delta >= umbral
    df['Evento_Independiente'] = delta_minutes.fillna(float('inf')) >= time_threshold

    return df



def format_number(number, decimals=2):
    """
    Formatea un número con decimales
    
    Args:
        number: Número a formatear
        decimals: Número de decimales
    
    Returns:
        str: Número formateado
    """
    try:
        return f"{float(number):.{decimals}f}"
    except:
        return str(number)


def create_summary_table(data_dict):
    """
    Crea una tabla resumen a partir de un diccionario
    
    Args:
        data_dict: Diccionario con datos
    
    Returns:
        DataFrame: Tabla resumen
    """
    df = pd.DataFrame(list(data_dict.items()), columns=['Métrica', 'Valor'])
    return df


def export_to_excel(dataframes_dict, filename):
    """
    Exporta múltiples DataFrames a un archivo Excel con múltiples hojas
    
    Args:
        dataframes_dict: Diccionario {nombre_hoja: DataFrame}
        filename: Nombre del archivo de salida
    
    Returns:
        str: Ruta del archivo creado
    """
    try:
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'outputs', filename)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dataframes_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_path
    
    except Exception as e:
        print(f"Error exportando a Excel: {e}")
        return None


def get_time_of_day(hour):
    """
    Determina el período del día basado en la hora
    
    Args:
        hour: Hora (0-23)
    
    Returns:
        str: 'Día', 'Noche', 'Amanecer', 'Atardecer'
    """
    if 6 <= hour < 12:
        return 'Mañana'
    elif 12 <= hour < 18:
        return 'Tarde'
    elif 18 <= hour < 21:
        return 'Atardecer'
    else:
        return 'Noche'


def classify_activity_pattern(hours):
    """
    Clasifica el patrón de actividad basado en las horas de detección
    
    Args:
        hours: Lista o array de horas (0-23)
    
    Returns:
        str: 'Diurno', 'Nocturno', 'Crepuscular', 'Catémero'
    """
    hours = np.array(hours)
    
    # Definir períodos
    day_hours = ((hours >= 6) & (hours < 18)).sum()
    night_hours = ((hours < 6) | (hours >= 18)).sum()
    crepuscular_hours = (((hours >= 5) & (hours < 7)) | 
                        ((hours >= 17) & (hours < 19))).sum()
    
    total = len(hours)
    
    if total == 0:
        return 'Desconocido'
    
    day_pct = day_hours / total
    night_pct = night_hours / total
    crep_pct = crepuscular_hours / total
    
    # Clasificación
    if crep_pct > 0.5:
        return 'Crepuscular'
    elif day_pct > 0.7:
        return 'Diurno'
    elif night_pct > 0.7:
        return 'Nocturno'
    else:
        return 'Catémero'


def generate_color_palette(n_colors):
    """
    Genera una paleta de colores
    
    Args:
        n_colors: Número de colores
    
    Returns:
        list: Lista de colores en formato hex
    """
    import matplotlib.pyplot as plt
    
    cmap = plt.cm.get_cmap('tab20')
    colors = [plt.matplotlib.colors.rgb2hex(cmap(i)) for i in np.linspace(0, 1, n_colors)]
    
    return colors


def safe_divide(numerator, denominator, default=0):
    """
    División segura que maneja división por cero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si denominador es 0
    
    Returns:
        float: Resultado de la división o valor por defecto
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


from functools import lru_cache

@lru_cache(maxsize=1024)
def clean_species_name(name):
    """
    Limpia y estandariza nombres de especies.
    OPTIMIZADO: Usa lru_cache para evitar re-procesar las mismas cadenas en DataFrames masivos.
    
    Args:
        name: Nombre de especie
    
    Returns:
        str: Nombre limpio
    """

    if pd.isna(name):
        return "Desconocido"
    
    # Convertir a string y limpiar
    name = str(name).strip()
    
    # Capitalizar primera letra de cada palabra, excepto preposiciones comunes
    preposiciones = ['de', 'del', 'la', 'el', 'los', 'las', 'y']
    words = name.split()
    if not words:
        return "Desconocido"
        
    cleaned_words = [words[0].capitalize()]
    for word in words[1:]:
        if word.lower() in preposiciones:
            cleaned_words.append(word.lower())
        else:
            cleaned_words.append(word.capitalize())
    
    return ' '.join(cleaned_words)


def calculate_trap_nights(df):
    """
    Calcula el número de noches-trampa por cámara
    
    Args:
        df: DataFrame con datos de cámaras
    
    Returns:
        DataFrame: Resumen de noches-trampa por cámara
    """
    df = df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    trap_nights = df.groupby('Camara').agg({
        'Fecha': lambda x: (x.max() - x.min()).days + 1
    }).reset_index()
    
    trap_nights.columns = ['Camara', 'Noches_Trampa']
    
    return trap_nights
