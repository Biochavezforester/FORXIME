"""
Módulo de evaluación de riesgo de especies y prioridades de conservación para FORXIME/2
"""
import pandas as pd
import numpy as np


# Lista de especies amenazadas (IUCN) - Simplificada
THREATENED_SPECIES = {
    # Críticamente en Peligro (CR)
    'CR': [
        'panthera tigris', 'tiger', 'tigre',
        'gorilla beringei', 'gorila de montaña',
        'pongo abelii', 'orangután de sumatra',
        'rhinoceros sondaicus', 'rinoceronte de java'
    ],
    # En Peligro (EN)
    'EN': [
        'panthera pardus', 'leopardo', 'leopard',
        'elephas maximus', 'elefante asiático',
        'pan troglodytes', 'chimpancé',
        'lycaon pictus', 'perro salvaje africano',
        'tapirus bairdii', 'tapir centroamericano'
    ],
    # Vulnerable (VU)
    'VU': [
        'panthera onca', 'jaguar',
        'hippopotamus amphibius', 'hipopótamo',
        'puma concolor', 'puma',
        'leopardus pardalis', 'ocelote', 'ocelot',
        'tapirus terrestris', 'tapir sudamericano'
    ],
    # Casi Amenazada (NT)
    'NT': [
        'panthera leo', 'león', 'lion',
        'ursus americanus', 'oso negro',
        'lynx rufus', 'lince rojo'
    ]
}

# NOM-059-SEMARNAT-2010 (México)
NOM_059_SPECIES = {
    # Probablemente extinta en el medio silvestre (E)
    'E': [
        'antilocapra americana', 'berrendo'
    ],
    # En peligro de extinción (P)
    'P': [
        'panthera onca', 'jaguar',
        'tapirus bairdii', 'tapir',
        'trichechus manatus', 'manatí',
        'ursus americanus', 'oso negro',
        'leopardus pardalis', 'ocelote',
        'leopardus wiedii', 'tigrillo',
        'herpailurus yagouaroundi', 'jaguarundi',
        'aquila chrysaetos', 'águila real'
    ],
    # Amenazada (A)
    'A': [
        'puma concolor', 'puma',
        'lynx rufus', 'lince',
        'pecari tajacu', 'pecarí de collar', 'jabalí',
        'tayassu pecari', 'pecarí de labios blancos',
        'odocoileus virginianus', 'venado cola blanca',
        'mazama temama', 'temazate',
        'nasua narica', 'coatí',
        'bassariscus astutus', 'cacomixtle'
    ],
    # Sujeta a protección especial (Pr)
    'Pr': [
        'urocyon cinereoargenteus', 'zorra gris',
        'procyon lotor', 'mapache',
        'mephitis macroura', 'zorrillo',
        'didelphis virginiana', 'tlacuache'
    ]
}

# Estatus biogeográfico
BIOGEOGRAPHIC_STATUS = {
    # Endémicas de México
    'endemic': [
        'bassariscus astutus', 'cacomixtle',
        'romerolagus diazi', 'teporingo',
        'cynomys mexicanus', 'perrito llanero mexicano'
    ],
    # Invasoras
    'invasive': [
        'sus scrofa', 'jabalí europeo', 'cerdo asilvestrado',
        'felis catus', 'gato doméstico', 'gato feral',
        'canis familiaris', 'perro doméstico', 'perro feral'
    ],
    # Exóticas (introducidas)
    'exotic': [
        'axis axis', 'venado axis',
        'dama dama', 'gamo',
        'cervus elaphus', 'ciervo rojo'
    ]
    # Por defecto, si no está en ninguna lista, se considera 'native' (nativa)
}


def assess_species_conservation_status(species_name):
    """
    Evalúa el estado de conservación de una especie
    
    Args:
        species_name: Nombre de la especie
    
    Returns:
        str: Categoría IUCN o 'LC' (Preocupación Menor)
    """
    species_lower = species_name.lower()
    
    for category, species_list in THREATENED_SPECIES.items():
        if any(sp in species_lower for sp in species_list):
            return category
    
    return 'LC'  # Least Concern (Preocupación Menor)


def assess_nom059_status(species_name):
    """
    Evalúa el estado según NOM-059-SEMARNAT-2010
    
    Args:
        species_name: Nombre de la especie
    
    Returns:
        str: Categoría NOM-059 o None
    """
    species_lower = species_name.lower()
    
    for category, species_list in NOM_059_SPECIES.items():
        if any(sp in species_lower for sp in species_list):
            return category
    
    return None


def assess_biogeographic_status(species_name):
    """
    Evalúa el estatus biogeográfico de la especie
    
    Args:
        species_name: Nombre de la especie
    
    Returns:
        str: 'endemic', 'invasive', 'exotic', o 'native'
    """
    species_lower = species_name.lower()
    
    if any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['endemic']):
        return 'endemic'
    elif any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['invasive']):
        return 'invasive'
    elif any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['exotic']):
        return 'exotic'
    else:
        return 'native'


def get_nom059_description(category, language='es'):
    """
    Obtiene descripción de categoría NOM-059
    
    Args:
        category: Categoría NOM-059
        language: Idioma
    
    Returns:
        str: Descripción
    """
    descriptions_es = {
        'E': 'Probablemente Extinta en el Medio Silvestre',
        'P': 'En Peligro de Extinción',
        'A': 'Amenazada',
        'Pr': 'Sujeta a Protección Especial'
    }
    
    descriptions_en = {
        'E': 'Probably Extinct in the Wild',
        'P': 'Endangered',
        'A': 'Threatened',
        'Pr': 'Subject to Special Protection'
    }
    
    if language == 'es':
        return descriptions_es.get(category, 'No listada')
    else:
        return descriptions_en.get(category, 'Not listed')


def get_biogeographic_description(status, language='es'):
    """
    Obtiene descripción de estatus biogeográfico
    
    Args:
        status: Estatus biogeográfico
        language: Idioma
    
    Returns:
        str: Descripción
    """
    descriptions_es = {
        'endemic': 'Endémica',
        'native': 'Nativa',
        'invasive': 'Invasora',
        'exotic': 'Exótica'
    }
    
    descriptions_en = {
        'endemic': 'Endemic',
        'native': 'Native',
        'invasive': 'Invasive',
        'exotic': 'Exotic'
    }
    
    if language == 'es':
        return descriptions_es.get(status, 'Desconocido')
    else:
        return descriptions_en.get(status, 'Unknown')

def calculate_conservation_priority_score(df, species):
    """
    Calcula puntaje de prioridad de conservación
    
    Args:
        df: DataFrame con datos
        species: Nombre de la especie
    
    Returns:
        dict: Puntaje y componentes
    """
    species_data = df[df['Especie_Categoria'] == species]
    
    # Componentes del puntaje
    score_components = {}
    
    # 1. Estado de conservación (0-40 puntos)
    status = assess_species_conservation_status(species)
    status_scores = {'CR': 40, 'EN': 30, 'VU': 20, 'NT': 10, 'LC': 0}
    score_components['conservation_status'] = status_scores.get(status, 0)
    score_components['iucn_category'] = status
    
    # 2. Rareza (basado en ocupación) (0-30 puntos)
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    total_sites = df[site_column].nunique()
    sites_occupied = species_data[site_column].nunique()
    occupancy = sites_occupied / total_sites if total_sites > 0 else 0
    
    # Especies raras (baja ocupación) tienen mayor prioridad
    if occupancy < 0.2:
        score_components['rarity'] = 30
    elif occupancy < 0.4:
        score_components['rarity'] = 20
    elif occupancy < 0.6:
        score_components['rarity'] = 10
    else:
        score_components['rarity'] = 0
    
    score_components['occupancy'] = occupancy
    
    # 3. Abundancia relativa (0-20 puntos)
    total_events = species_data['Eventos_Independientes'].sum()
    all_events = df['Eventos_Independientes'].sum()
    relative_abundance = total_events / all_events if all_events > 0 else 0
    
    # Especies con baja abundancia tienen mayor prioridad
    if relative_abundance < 0.05:
        score_components['low_abundance'] = 20
    elif relative_abundance < 0.10:
        score_components['low_abundance'] = 10
    else:
        score_components['low_abundance'] = 0
    
    score_components['relative_abundance'] = relative_abundance
    
    # 4. Rol ecológico (0-10 puntos)
    # Depredadores tope y especies clave
    keystone_keywords = ['panthera', 'jaguar', 'puma', 'wolf', 'lobo', 'elephant', 'elefante', 'tapir']
    is_keystone = any(kw in species.lower() for kw in keystone_keywords)
    score_components['keystone_species'] = 10 if is_keystone else 0
    
    # Puntaje total (0-100)
    total_score = sum([
        score_components['conservation_status'],
        score_components['rarity'],
        score_components['low_abundance'],
        score_components['keystone_species']
    ])
    
    score_components['total_score'] = total_score
    
    # Clasificación de prioridad
    if total_score >= 70:
        priority = 'Crítica'
    elif total_score >= 50:
        priority = 'Alta'
    elif total_score >= 30:
        priority = 'Media'
    else:
        priority = 'Baja'
    
    score_components['priority_level'] = priority
    
    return score_components


def generate_conservation_priorities_report(df, language='es'):
    """
    Genera reporte de prioridades de conservación
    
    Args:
        df: DataFrame con datos
        language: Idioma
    
    Returns:
        DataFrame: Reporte de prioridades
    """
    priorities = []
    
    for species in df['Especie_Categoria'].unique():
        score_data = calculate_conservation_priority_score(df, species)
        
        # Obtener clasificaciones adicionales
        nom059_status = assess_nom059_status(species)
        biogeo_status = assess_biogeographic_status(species)
        
        priorities.append({
            'Especie': species,
            'Categoria_IUCN': score_data['iucn_category'],
            'NOM_059': get_nom059_description(nom059_status, language) if nom059_status else 'No listada',
            'Estatus_Biogeografico': get_biogeographic_description(biogeo_status, language),
            'Ocupacion': f"{score_data['occupancy']:.2%}",
            'Abundancia_Relativa': f"{score_data['relative_abundance']:.2%}",
            'Especie_Clave': 'Sí' if score_data['keystone_species'] > 0 else 'No',
            'Puntaje_Total': score_data['total_score'],
            'Prioridad': score_data['priority_level']
        })
    
    priorities_df = pd.DataFrame(priorities).sort_values('Puntaje_Total', ascending=False)
    
    return priorities_df


def identify_critical_habitats(df):
    """
    Identifica hábitats críticos basado en presencia de especies amenazadas
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Sitios críticos
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    critical_sites = []
    
    for site in df[site_column].unique():
        site_data = df[df[site_column] == site]
        
        # Contar especies amenazadas
        threatened_count = 0
        threatened_species = []
        
        for species in site_data['Especie_Categoria'].unique():
            status = assess_species_conservation_status(species)
            if status in ['CR', 'EN', 'VU']:
                threatened_count += 1
                threatened_species.append(f"{species} ({status})")
        
        # Calcular riqueza total
        richness = site_data['Especie_Categoria'].nunique()
        
        # Clasificar importancia
        if threatened_count >= 3:
            importance = 'Crítica'
        elif threatened_count >= 2:
            importance = 'Alta'
        elif threatened_count >= 1:
            importance = 'Media'
        else:
            importance = 'Baja'
        
        critical_sites.append({
            'Sitio': site,
            'Riqueza_Total': richness,
            'Especies_Amenazadas': threatened_count,
            'Lista_Especies_Amenazadas': '; '.join(threatened_species) if threatened_species else 'Ninguna',
            'Importancia_Conservacion': importance
        })
    
    critical_df = pd.DataFrame(critical_sites).sort_values('Especies_Amenazadas', ascending=False)
    
    return critical_df


def generate_species_fact_sheet(df, species, language='es'):
    """
    Genera ficha técnica de una especie
    
    Args:
        df: DataFrame con datos
        species: Nombre de la especie
        language: Idioma
    
    Returns:
        dict: Ficha técnica
    """
    species_data = df[df['Especie_Categoria'] == species]
    
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    fact_sheet = {
        'species_name': species,
        'conservation_status': assess_species_conservation_status(species),
        'total_records': len(species_data),
        'independent_events': species_data['Eventos_Independientes'].sum(),
        'sites_detected': species_data[site_column].nunique(),
        'cameras_detected': species_data['Camara'].nunique(),
        'occupancy_rate': species_data[site_column].nunique() / df[site_column].nunique(),
        'detection_rate': len(species_data) / len(df),
        'first_detection': species_data['Fecha'].min(),
        'last_detection': species_data['Fecha'].max()
    }
    
    # Calcular prioridad de conservación
    priority_data = calculate_conservation_priority_score(df, species)
    fact_sheet['conservation_priority'] = priority_data['priority_level']
    fact_sheet['priority_score'] = priority_data['total_score']
    
    return fact_sheet


def generate_monitoring_recommendations(priorities_df, language='es'):
    """
    Genera recomendaciones de monitoreo basadas en prioridades
    
    Args:
        priorities_df: DataFrame con prioridades
        language: Idioma
    
    Returns:
        list: Recomendaciones
    """
    recommendations = []
    
    # Especies de prioridad crítica
    critical_species = priorities_df[priorities_df['Prioridad'] == 'Crítica']
    
    if len(critical_species) > 0:
        if language == 'es':
            rec = {
                'category': 'Especies de Prioridad Crítica',
                'priority': 'Crítica',
                'recommendation': f"Se identificaron {len(critical_species)} especies de prioridad crítica. "
                                f"Se recomienda:\n"
                                f"- Aumentar esfuerzo de monitoreo en sitios donde fueron detectadas\n"
                                f"- Implementar protocolos específicos de conservación\n"
                                f"- Evaluar amenazas inmediatas\n"
                                f"- Considerar establecimiento de áreas protegidas",
                'species_list': critical_species['Especie'].tolist()
            }
        else:
            rec = {
                'category': 'Critical Priority Species',
                'priority': 'Critical',
                'recommendation': f"{len(critical_species)} critical priority species identified. "
                                f"Recommended actions:\n"
                                f"- Increase monitoring effort at detection sites\n"
                                f"- Implement specific conservation protocols\n"
                                f"- Assess immediate threats\n"
                                f"- Consider establishing protected areas",
                'species_list': critical_species['Especie'].tolist()
            }
        
        recommendations.append(rec)
    
    # Especies raras (baja ocupación)
    rare_species = priorities_df[priorities_df['Ocupacion'].str.rstrip('%').astype(float) < 20]
    
    if len(rare_species) > 0:
        if language == 'es':
            rec = {
                'category': 'Especies Raras',
                'priority': 'Alta',
                'recommendation': f"Se detectaron {len(rare_species)} especies raras (ocupación <20%). "
                                f"Se recomienda:\n"
                                f"- Investigar causas de baja detección\n"
                                f"- Evaluar si son naturalmente raras o en declive\n"
                                f"- Aumentar número de cámaras en sitios de detección",
                'species_list': rare_species['Especie'].tolist()
            }
        
        recommendations.append(rec)
    
    return recommendations
