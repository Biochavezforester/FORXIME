"""
Módulo de información cinegética para FORXIME/2
Proporciona información sobre especies de interés cinegético y recomendaciones de manejo
"""
import pandas as pd
import numpy as np


# Especies cinegéticas de México (según calendario cinegético)
GAME_SPECIES = {
    # Ungulados
    'ungulates': {
        'odocoileus virginianus': {
            'nombre_comun': 'Venado de Cola Blanca',
            'temporada': 'Noviembre - Febrero',
            'cuota': 'Variable por UMA',
            'metodo': 'Rifle, arco',
            'valor_economico': 'Alto',
            'manejo': 'UMA intensivo o extensivo'
        },
        'pecari tajacu': {
            'nombre_comun': 'Pecarí de Collar',
            'temporada': 'Octubre - Marzo',
            'cuota': 'Variable por UMA',
            'metodo': 'Rifle',
            'valor_economico': 'Medio',
            'manejo': 'UMA extensivo'
        }
    },
    # Aves
    'birds': {
        'meleagris gallopavo': {
            'nombre_comun': 'Guajolote Norteño',
            'temporada': 'Marzo - Abril',
            'cuota': '1-2 por temporada',
            'metodo': 'Escopeta',
            'valor_economico': 'Alto',
            'manejo': 'UMA extensivo'
        },
        'callipepla': {
            'nombre_comun': 'Codorniz',
            'temporada': 'Octubre - Febrero',
            'cuota': '15-20 por día',
            'metodo': 'Escopeta',
            'valor_economico': 'Medio',
            'manejo': 'Caza deportiva'
        }
    }
}

# NOTA: Coyote (Canis latrans) NO es especie cinegética en México.
# Es una especie de control de daños, no de caza deportiva.
# Especies como Jaguar, Puma, Ocelote están PROTEGIDAS y no pueden cazarse.


def identify_game_species(df):
    """
    Identifica especies cinegéticas en los datos
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Especies cinegéticas detectadas
    """
    game_species_detected = []
    
    for species in df['Especie_Categoria'].unique():
        species_lower = species.lower()
        
        # Buscar en todas las categorías
        for category, species_dict in GAME_SPECIES.items():
            for scientific_name, info in species_dict.items():
                if scientific_name in species_lower or info['nombre_comun'].lower() in species_lower:
                    species_data = df[df['Especie_Categoria'] == species]
                    
                    game_species_detected.append({
                        'Especie': species,
                        'Nombre_Comun': info['nombre_comun'],
                        'Categoria': category,
                        'Temporada_Caza': info['temporada'],
                        'Cuota_Recomendada': info['cuota'],
                        'Metodo_Caza': info['metodo'],
                        'Valor_Economico': info['valor_economico'],
                        'Tipo_Manejo': info['manejo'],
                        'Eventos_Detectados': species_data['Eventos_Independientes'].sum(),
                        'Sitios_Detectados': species_data['Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'].nunique()
                    })
                    break
    
    if len(game_species_detected) > 0:
        return pd.DataFrame(game_species_detected)
    else:
        return pd.DataFrame()


def calculate_sustainable_harvest(df, species, language='es'):
    """
    Calcula estimación de cosecha sostenible
    
    Args:
        df: DataFrame con datos
        species: Nombre de la especie
        language: Idioma
    
    Returns:
        dict: Estimación de cosecha
    """
    species_data = df[df['Especie_Categoria'] == species]
    
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Calcular índice de abundancia relativa
    total_trap_nights = df.groupby('Camara')['Fecha'].apply(
        lambda x: (pd.to_datetime(x.max()) - pd.to_datetime(x.min())).days + 1
    ).sum()
    
    events = species_data['Eventos_Independientes'].sum()
    rai = (events / total_trap_nights * 100) if total_trap_nights > 0 else 0
    
    # Estimación conservadora de cosecha (10-15% de población estimada)
    # Esto es muy simplificado y requiere estudios poblacionales detallados
    
    if language == 'es':
        recommendation = {
            'species': species,
            'rai': rai,
            'abundance_level': 'Alta' if rai > 5 else 'Media' if rai > 2 else 'Baja',
            'harvest_recommendation': None,
            'notes': []
        }
        
        if rai > 5:
            recommendation['harvest_recommendation'] = 'Cosecha sostenible posible con plan de manejo adecuado'
            recommendation['notes'].append('RAI indica abundancia alta')
            recommendation['notes'].append('Requiere estudio poblacional detallado antes de autorizar cosecha')
        elif rai > 2:
            recommendation['harvest_recommendation'] = 'Cosecha limitada posible con monitoreo estricto'
            recommendation['notes'].append('RAI indica abundancia media')
            recommendation['notes'].append('Implementar cuotas conservadoras')
        else:
            recommendation['harvest_recommendation'] = 'NO se recomienda cosecha - población baja'
            recommendation['notes'].append('RAI indica abundancia baja')
            recommendation['notes'].append('Enfocar en recuperación poblacional')
    
    return recommendation


def generate_hunting_management_plan(df, language='es'):
    """
    Genera plan de manejo cinegético
    
    Args:
        df: DataFrame con datos
        language: Idioma
    
    Returns:
        dict: Plan de manejo
    """
    game_species_df = identify_game_species(df)
    
    if len(game_species_df) == 0:
        return {
            'has_game_species': False,
            'message': 'No se detectaron especies de interés cinegético' if language == 'es' else 'No game species detected'
        }
    
    plan = {
        'has_game_species': True,
        'species_detected': len(game_species_df),
        'species_list': game_species_df,
        'recommendations': [],
        'uma_recommendation': None
    }
    
    # Generar recomendaciones por especie
    for idx, row in game_species_df.iterrows():
        harvest_rec = calculate_sustainable_harvest(df, row['Especie'], language)
        
        plan['recommendations'].append({
            'species': row['Especie'],
            'common_name': row['Nombre_Comun'],
            'harvest_recommendation': harvest_rec['harvest_recommendation'],
            'abundance_level': harvest_rec['abundance_level'],
            'rai': harvest_rec['rai'],
            'notes': harvest_rec['notes']
        })
    
    # Recomendación de UMA
    if language == 'es':
        if len(game_species_df) >= 2:
            plan['uma_recommendation'] = """
### Recomendación de UMA (Unidad de Manejo para la Conservación de Vida Silvestre)

Basado en las especies detectadas, se recomienda:

**Tipo de UMA:** Extensiva (vida libre)

**Beneficios:**
- Aprovechamiento sustentable de fauna silvestre
- Ingresos económicos por cacería deportiva
- Incentivo para conservación de hábitat
- Monitoreo continuo de poblaciones

**Requisitos:**
- Registro ante SEMARNAT
- Plan de manejo aprobado
- Monitoreo poblacional anual
- Infraestructura básica (señalización, registros)
- Capacitación de personal

**Especies aprovechables detectadas:**
"""
            for idx, row in game_species_df.iterrows():
                plan['uma_recommendation'] += f"\n- {row['Nombre_Comun']} ({row['Especie']})"
            
            plan['uma_recommendation'] += "\n\n**Nota:** La viabilidad de la UMA debe ser evaluada por especialistas considerando aspectos legales, ecológicos y económicos."
    
    return plan


def generate_hunting_calendar(game_species_df, language='es'):
    """
    Genera calendario cinegético
    
    Args:
        game_species_df: DataFrame con especies cinegéticas
        language: Idioma
    
    Returns:
        str: Calendario en formato markdown
    """
    if len(game_species_df) == 0:
        return "No hay especies cinegéticas detectadas"
    
    if language == 'es':
        calendar = "## 📅 Calendario Cinegético\n\n"
        calendar += "| Especie | Temporada | Cuota | Método |\n"
        calendar += "|---------|-----------|-------|--------|\n"
        
        for idx, row in game_species_df.iterrows():
            calendar += f"| {row['Nombre_Comun']} | {row['Temporada_Caza']} | {row['Cuota_Recomendada']} | {row['Metodo_Caza']} |\n"
        
        calendar += "\n**Nota:** Las temporadas y cuotas son referenciales. Consultar calendario oficial de SEMARNAT."
    
    return calendar


def assess_hunting_impact(df, game_species_df, language='es'):
    """
    Evalúa impacto potencial de cacería
    
    Args:
        df: DataFrame con todos los datos
        game_species_df: DataFrame con especies cinegéticas
        language: Idioma
    
    Returns:
        dict: Evaluación de impacto
    """
    if len(game_species_df) == 0:
        return {'has_data': False}
    
    assessment = {
        'has_data': True,
        'impacts': [],
        'mitigation_measures': []
    }
    
    if language == 'es':
        # Evaluar impacto en depredadores
        predator_species = df[df['Especie_Categoria'].str.contains('jaguar|puma|ocelote', case=False, na=False)]
        
        if len(predator_species) > 0:
            assessment['impacts'].append({
                'type': 'Reducción de presas naturales',
                'severity': 'Media',
                'description': 'La cacería de herbívoros puede reducir presas disponibles para depredadores',
                'affected_species': predator_species['Especie_Categoria'].unique().tolist()
            })
            
            assessment['mitigation_measures'].append({
                'measure': 'Cuotas conservadoras',
                'description': 'Mantener cuotas de cosecha por debajo del 10% de la población estimada'
            })
            
            assessment['mitigation_measures'].append({
                'measure': 'Zonas de exclusión',
                'description': 'Establecer áreas sin cacería para mantener presas para depredadores'
            })
        
        # Evaluar perturbación
        assessment['impacts'].append({
            'type': 'Perturbación por actividad humana',
            'severity': 'Baja-Media',
            'description': 'La actividad de cacería puede perturbar temporalmente a la fauna',
            'affected_species': 'Todas las especies del área'
        })
        
        assessment['mitigation_measures'].append({
            'measure': 'Temporadas limitadas',
            'description': 'Restringir cacería a períodos específicos del año'
        })
        
        assessment['mitigation_measures'].append({
            'measure': 'Zonificación',
            'description': 'Designar áreas específicas para cacería, manteniendo zonas núcleo sin perturbación'
        })
    
    return assessment
