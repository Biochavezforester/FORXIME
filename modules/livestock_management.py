"""
Módulo de recomendaciones de manejo ganadero y coexistencia fauna-ganado para FORXIME/2
"""
import pandas as pd
import numpy as np
from modules.temporal_analysis import analyze_temporal_overlap, calculate_activity_pattern


def identify_livestock_predators(species_list):
    """
    Identifica depredadores potenciales de ganado
    
    Args:
        species_list: Lista de especies detectadas
    
    Returns:
        dict: Depredadores categorizados por riesgo
    """
    # Depredadores de alto riesgo
    high_risk = [
        'panthera onca', 'jaguar',
        'puma concolor', 'puma', 'cougar',
        'panthera leo', 'leon', 'lion',
        'canis lupus', 'lobo', 'wolf',
        'lycaon pictus', 'perro salvaje africano'
    ]
    
    # Depredadores de riesgo moderado
    moderate_risk = [
        'leopardus pardalis', 'ocelote', 'ocelot',
        'lynx', 'lince',
        'coyote', 'canis latrans',
        'vulpes', 'zorro', 'fox'
    ]
    
    # Depredadores de bajo riesgo (carroñeros)
    low_risk = [
        'vultur', 'buitre', 'vulture',
        'coragyps', 'zopilote',
        'caracara'
    ]
    
    detected_predators = {
        'high_risk': [],
        'moderate_risk': [],
        'low_risk': []
    }
    
    for species in species_list:
        species_lower = species.lower()
        
        if any(pred in species_lower for pred in high_risk):
            detected_predators['high_risk'].append(species)
        elif any(pred in species_lower for pred in moderate_risk):
            detected_predators['moderate_risk'].append(species)
        elif any(pred in species_lower for pred in low_risk):
            detected_predators['low_risk'].append(species)
    
    return detected_predators


def identify_livestock_in_data(df):
    """
    Identifica registros de ganado en los datos
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Registros de ganado
    """
    livestock_keywords = [
        'vaca', 'cow', 'ganado', 'cattle', 'bovino',
        'caballo', 'horse', 'equino',
        'oveja', 'sheep', 'ovino',
        'cabra', 'goat', 'caprino',
        'cerdo', 'pig', 'porcino'
    ]
    
    mask = df['Especie_Categoria'].str.lower().str.contains('|'.join(livestock_keywords), na=False)
    livestock_df = df[mask].copy()
    
    return livestock_df


def analyze_predator_livestock_overlap(df, predator_species, livestock_species='ganado'):
    """
    Analiza solapamiento temporal entre depredador y ganado
    
    Args:
        df: DataFrame con datos
        predator_species: Nombre del depredador
        livestock_species: Nombre del ganado (por defecto 'ganado')
    
    Returns:
        dict: Análisis de solapamiento
    """
    # Verificar si hay datos de ganado
    livestock_data = identify_livestock_in_data(df)
    
    if len(livestock_data) == 0:
        # Si no hay datos de ganado, asumir actividad diurna típica
        return {
            'has_livestock_data': False,
            'predator_species': predator_species,
            'assumed_livestock_pattern': 'Diurno (6:00-18:00)',
            'recommendation_based_on': 'Patrón típico de pastoreo'
        }
    
    # Si hay datos de ganado, hacer análisis de solapamiento
    overlap_result = analyze_temporal_overlap(df, predator_species, livestock_species)
    
    if overlap_result['success']:
        overlap_result['has_livestock_data'] = True
        return overlap_result
    else:
        return {
            'has_livestock_data': False,
            'predator_species': predator_species,
            'error': overlap_result.get('message', 'Datos insuficientes')
        }


def generate_grazing_recommendations(df, language='es'):
    """
    Genera recomendaciones de pastoreo basadas en actividad de depredadores
    
    Args:
        df: DataFrame con datos
        language: Idioma ('es' o 'en')
    
    Returns:
        list: Lista de recomendaciones
    """
    recommendations = []
    
    # Identificar depredadores
    species_list = df['Especie_Categoria'].unique()
    predators = identify_livestock_predators(species_list)
    
    # Analizar cada depredador de alto y moderado riesgo
    all_predators = predators['high_risk'] + predators['moderate_risk']
    
    for predator in all_predators:
        # Obtener patrón de actividad del depredador
        activity_pattern = calculate_activity_pattern(df, predator)
        
        if not activity_pattern:
            continue
        
        # Determinar nivel de riesgo
        risk_level = 'Alto' if predator in predators['high_risk'] else 'Moderado'
        
        # Identificar horas de mayor actividad
        density = activity_pattern['density']
        hours = activity_pattern['grid_hours']
        
        # Encontrar picos de actividad (densidad > 75% del máximo)
        threshold = np.max(density) * 0.75
        high_activity_mask = density > threshold
        high_activity_hours = hours[high_activity_mask]
        
        if len(high_activity_hours) == 0:
            continue
        
        # Determinar rangos de horas
        hour_ranges = []
        start_hour = None
        
        for i, hour in enumerate(high_activity_hours):
            if start_hour is None:
                start_hour = hour
            
            # Si es la última hora o hay un salto
            if i == len(high_activity_hours) - 1 or high_activity_hours[i+1] - hour > 1:
                end_hour = hour
                hour_ranges.append((start_hour, end_hour))
                start_hour = None
        
        # Generar recomendación
        if language == 'es':
            rec = {
                'species': predator,
                'risk_level': risk_level,
                'activity_pattern': activity_pattern['pattern'],
                'peak_hours': hour_ranges,
                'recommendation': generate_spanish_recommendation(
                    predator, risk_level, hour_ranges, activity_pattern['pattern']
                ),
                'priority': 'Alta' if risk_level == 'Alto' else 'Media'
            }
        else:
            rec = {
                'species': predator,
                'risk_level': risk_level,
                'activity_pattern': activity_pattern['pattern'],
                'peak_hours': hour_ranges,
                'recommendation': generate_english_recommendation(
                    predator, risk_level, hour_ranges, activity_pattern['pattern']
                ),
                'priority': 'High' if risk_level == 'Alto' else 'Medium'
            }
        
        recommendations.append(rec)
    
    return recommendations


def generate_spanish_recommendation(predator, risk_level, hour_ranges, pattern):
    """
    Genera recomendación en español
    """
    hours_text = ", ".join([f"{int(start):02d}:00-{int(end):02d}:00" for start, end in hour_ranges])
    
    recommendation = f"""
**{predator}** (Riesgo: {risk_level})

🕐 **Patrón de actividad:** {pattern}

⚠️ **Horas de mayor riesgo:** {hours_text}

📋 **Recomendaciones:**
- Evitar pastoreo en estas horas para reducir encuentros con depredadores
- Mantener ganado en corrales o áreas cercadas durante períodos de alto riesgo
- Implementar vigilancia adicional si el pastoreo es necesario en estos horarios
- Considerar uso de perros guardianes durante horas de riesgo
"""
    
    if pattern == 'Nocturno':
        recommendation += "\n- El depredador es principalmente nocturno. Se recomienda encerrar el ganado al atardecer."
    elif pattern == 'Crepuscular':
        recommendation += "\n- El depredador es más activo al amanecer y atardecer. Extremar precauciones en estos períodos."
    
    return recommendation


def generate_english_recommendation(predator, risk_level, hour_ranges, pattern):
    """
    Genera recomendación en inglés
    """
    hours_text = ", ".join([f"{int(start):02d}:00-{int(end):02d}:00" for start, end in hour_ranges])
    
    recommendation = f"""
**{predator}** (Risk: {risk_level})

🕐 **Activity pattern:** {pattern}

⚠️ **Highest risk hours:** {hours_text}

📋 **Recommendations:**
- Avoid grazing during these hours to reduce encounters with predators
- Keep livestock in corrals or fenced areas during high-risk periods
- Implement additional surveillance if grazing is necessary during these times
- Consider using guard dogs during risk hours
"""
    
    if pattern == 'Nocturnal':
        recommendation += "\n- The predator is primarily nocturnal. Recommend securing livestock at dusk."
    elif pattern == 'Crepuscular':
        recommendation += "\n- The predator is most active at dawn and dusk. Exercise extreme caution during these periods."
    
    return recommendation


def identify_safe_grazing_zones(df, site_column='Sitio_Agrupado'):
    """
    Identifica zonas seguras para pastoreo basado en presencia de depredadores
    
    Args:
        df: DataFrame con datos
        site_column: Columna de sitio
    
    Returns:
        DataFrame: Clasificación de sitios por seguridad
    """
    species_list = df['Especie_Categoria'].unique()
    predators = identify_livestock_predators(species_list)
    
    all_predators = predators['high_risk'] + predators['moderate_risk']
    
    # Analizar cada sitio
    site_safety = []
    
    for site in df[site_column].unique():
        site_data = df[df[site_column] == site]
        
        # Contar depredadores en el sitio
        site_species = site_data['Especie_Categoria'].unique()
        
        high_risk_count = sum(1 for sp in site_species if sp in predators['high_risk'])
        moderate_risk_count = sum(1 for sp in site_species if sp in predators['moderate_risk'])
        
        # Calcular eventos de depredadores
        predator_events = site_data[site_data['Especie_Categoria'].isin(all_predators)]['Eventos_Independientes'].sum()
        total_events = site_data['Eventos_Independientes'].sum()
        
        predator_percentage = (predator_events / total_events * 100) if total_events > 0 else 0
        
        # Clasificar seguridad
        if high_risk_count > 0 and predator_percentage > 20:
            safety_class = 'Alto Riesgo'
            recommendation = 'No recomendado para pastoreo'
        elif high_risk_count > 0 or predator_percentage > 10:
            safety_class = 'Riesgo Moderado'
            recommendation = 'Pastoreo con precauciones extremas'
        elif moderate_risk_count > 0:
            safety_class = 'Riesgo Bajo'
            recommendation = 'Pastoreo permitido con vigilancia'
        else:
            safety_class = 'Seguro'
            recommendation = 'Zona segura para pastoreo'
        
        site_safety.append({
            'Sitio': site,
            'Depredadores_Alto_Riesgo': high_risk_count,
            'Depredadores_Riesgo_Moderado': moderate_risk_count,
            'Porcentaje_Eventos_Depredadores': predator_percentage,
            'Clasificacion_Seguridad': safety_class,
            'Recomendacion': recommendation
        })
    
    return pd.DataFrame(site_safety).sort_values('Porcentaje_Eventos_Depredadores', ascending=False)


def generate_livestock_management_report(df, language='es'):
    """
    Genera reporte completo de manejo ganadero
    
    Args:
        df: DataFrame con datos
        language: Idioma
    
    Returns:
        dict: Reporte completo
    """
    report = {}
    
    # Identificar depredadores
    species_list = df['Especie_Categoria'].unique()
    predators = identify_livestock_predators(species_list)
    
    report['predators_detected'] = predators
    report['total_predator_species'] = (len(predators['high_risk']) + 
                                       len(predators['moderate_risk']) + 
                                       len(predators['low_risk']))
    
    # Recomendaciones de pastoreo
    report['grazing_recommendations'] = generate_grazing_recommendations(df, language)
    
    # Zonas seguras
    report['safe_zones'] = identify_safe_grazing_zones(df)
    
    # Presencia de ganado
    livestock_data = identify_livestock_in_data(df)
    report['livestock_detected'] = len(livestock_data) > 0
    report['livestock_records'] = len(livestock_data)
    
    # Resumen ejecutivo
    if language == 'es':
        report['executive_summary'] = generate_executive_summary_es(report)
    else:
        report['executive_summary'] = generate_executive_summary_en(report)
    
    return report


def generate_executive_summary_es(report):
    """
    Genera resumen ejecutivo en español
    """
    summary = "# 🐄 Resumen Ejecutivo - Manejo Ganadero y Coexistencia con Fauna Silvestre\n\n"
    
    predators = report['predators_detected']
    
    if len(predators['high_risk']) > 0:
        summary += f"⚠️ **ALERTA:** Se detectaron {len(predators['high_risk'])} especies de depredadores de alto riesgo:\n"
        for pred in predators['high_risk']:
            summary += f"- {pred}\n"
        summary += "\n"
    
    if len(predators['moderate_risk']) > 0:
        summary += f"⚡ Se detectaron {len(predators['moderate_risk'])} especies de depredadores de riesgo moderado.\n\n"
    
    summary += f"**Total de recomendaciones generadas:** {len(report['grazing_recommendations'])}\n\n"
    
    # Zonas de riesgo
    safe_zones = report['safe_zones']
    high_risk_zones = safe_zones[safe_zones['Clasificacion_Seguridad'] == 'Alto Riesgo']
    
    if len(high_risk_zones) > 0:
        summary += f"🚫 **Zonas de alto riesgo identificadas:** {len(high_risk_zones)}\n"
        summary += "Se recomienda evitar pastoreo en estas zonas.\n\n"
    
    summary += "📋 Consulte las recomendaciones detalladas a continuación para implementar estrategias de coexistencia efectivas."
    
    return summary


def generate_executive_summary_en(report):
    """
    Genera resumen ejecutivo en inglés
    """
    summary = "# 🐄 Executive Summary - Livestock Management and Wildlife Coexistence\n\n"
    
    predators = report['predators_detected']
    
    if len(predators['high_risk']) > 0:
        summary += f"⚠️ **ALERT:** {len(predators['high_risk'])} high-risk predator species detected:\n"
        for pred in predators['high_risk']:
            summary += f"- {pred}\n"
        summary += "\n"
    
    if len(predators['moderate_risk']) > 0:
        summary += f"⚡ {len(predators['moderate_risk'])} moderate-risk predator species detected.\n\n"
    
    summary += f"**Total recommendations generated:** {len(report['grazing_recommendations'])}\n\n"
    
    # Risk zones
    safe_zones = report['safe_zones']
    high_risk_zones = safe_zones[safe_zones['Clasificacion_Seguridad'] == 'Alto Riesgo']
    
    if len(high_risk_zones) > 0:
        summary += f"🚫 **High-risk zones identified:** {len(high_risk_zones)}\n"
        summary += "Grazing in these zones is not recommended.\n\n"
    
    summary += "📋 See detailed recommendations below to implement effective coexistence strategies."
    
    return summary
