"""
Módulo de Hidratación para FORXIME/2
Asegura que todos los resultados necesarios para el reporte PDF estén calculados
"""
import pandas as pd
import numpy as np
from modules import temporal_analysis, statistical_analysis, sampling_evaluation

def hydrate_all_results(results, wildlife_df, processed_df, status_fn=None, enabled_sections=None):
    """
    Hidrata el diccionario de resultados con todos los análisis necesarios para el PDF.
    
    Args:
        results (dict): Diccionario de resultados actual
        wildlife_df (pd.DataFrame): DataFrame de fauna filtrado
        processed_df (pd.DataFrame): DataFrame procesado filtrado
        status_fn (callable): Función para actualizar el estado en la UI (opcional)
        enabled_sections (dict): Secciones habilitadas por el usuario (opcional)
    """
    if enabled_sections is None:
        enabled_sections = {}

    def update_status(text):
        if status_fn:
            status_fn(text)

    # 1. Métricas Básicas (Siempre necesario para resumen)
    if 'basic_metrics' not in results:
        update_status("⏳ Calculando métricas básicas...")
        results['basic_metrics'] = {
            'total_records': len(wildlife_df),
            'total_cameras': wildlife_df['Camara'].nunique() if 'Camara' in wildlife_df.columns else 0,
            'total_sites': wildlife_df['Sitio'].nunique() if 'Sitio' in wildlife_df.columns else 0,
            'total_species': wildlife_df['Especie_Categoria'].nunique() if 'Especie_Categoria' in wildlife_df.columns else 0,
            'total_trap_days': int(wildlife_df['Dias_Trampa'].sum() / max(wildlife_df['Especie_Categoria'].nunique(), 1)) if 'Dias_Trampa' in wildlife_df.columns and not wildlife_df.empty else 0
        }

    # 2. Biodiversidad
    if enabled_sections.get('biodiversity', True) and 'biodiversity' not in results:
        update_status("⏳ Calculando índices de biodiversidad...")
        try:
            results['biodiversity'] = statistical_analysis.calculate_biodiversity_indices(wildlife_df)
        except:
            results['biodiversity'] = {}

    # 3. Abundancia Relativa (RAI)
    if enabled_sections.get('abundance', True) and ('rai' not in results or (isinstance(results['rai'], pd.DataFrame) and results['rai'].empty)):
        update_status("⏳ Calculando abundancia relativa (RAI)...")
        try:
            results['rai'] = statistical_analysis.calculate_relative_abundance_index(wildlife_df)
        except:
            results['rai'] = pd.DataFrame()

    # 4. Evaluación de Muestreo
    if enabled_sections.get('sampling_effort', True) and 'sampling_effort' not in results:
        update_status("⏳ Evaluando esfuerzo de muestreo...")
        try:
            results['sampling_effort'] = statistical_analysis.calculate_sampling_effort(wildlife_df)
            results['false_triggers'] = sampling_evaluation.calculate_false_triggers(processed_df)
            results['sampling_recommendations'] = sampling_evaluation.generate_recommendations(results['sampling_effort'], results['false_triggers'])
        except:
            pass

    # 5. Patrones Temporales
    if enabled_sections.get('temporal_patterns', True):
        update_status("⏳ Analizando patrones de actividad temporal...")
        
        # Asegurar columna Hora
        if 'Hora' not in wildlife_df.columns:
            if 'Fecha_Captura' in wildlife_df.columns:
                temp_dates = pd.to_datetime(wildlife_df['Fecha_Captura'], errors='coerce')
                wildlife_df = wildlife_df.assign(
                    Hora = temp_dates.dt.hour + temp_dates.dt.minute/60
                )
        
        if not results.get('activity_patterns'):
            all_species = wildlife_df['Especie_Categoria'].unique()
            patterns = {}
            for sp in all_species:
                # Filtrar especies de ruido
                p = temporal_analysis.calculate_activity_pattern(wildlife_df, sp)
                if p: patterns[sp] = p
            results['activity_patterns'] = patterns

    # 6. Impacto Antropogénico
    if enabled_sections.get('anthropogenic', True) and 'anthropogenic' not in results:
        update_status("⏳ Analizando impacto antropogénico...")
        try:
            anthro_keywords = ['Humano', 'Vehiculo', 'Ganado', 'Perro', 'Gato', 'Cerdo', 'Bovino', 'Caballo']
            anthro_data = wildlife_df[wildlife_df['Especie_Categoria'].str.contains('|'.join(anthro_keywords), case=False, na=False)]
            results['anthropogenic'] = {
                'total_records': len(wildlife_df),
                'anthropogenic_records': len(anthro_data),
                'anthropogenic_percentage': (len(anthro_data) / len(wildlife_df) * 100) if not wildlife_df.empty else 0
            }
            results['anthropogenic_by_site'] = anthro_data.groupby('Sitio').size().reset_index(name='Registros') if 'Sitio' in wildlife_df.columns else pd.DataFrame()
        except:
            pass

    # 7. Dendrogramas
    if enabled_sections.get('dendrograms', True) and results.get('dendrogram') is None:
        update_status("⏳ Generando análisis de similitud (dendrogramas)...")
        try:
            results['dendrogram'] = statistical_analysis.calculate_dendrogram_data(wildlife_df)
        except:
            results['dendrogram'] = None

    # 8. Co-ocurrencia
    if enabled_sections.get('cooccurrence', True) and 'co_occurrence' not in results:
        update_status("⏳ Analizando co-ocurrencia de especies...")
        try:
            results['co_occurrence'] = statistical_analysis.calculate_cooccurrence_matrix(wildlife_df)
        except:
            results['co_occurrence'] = None

    # 9. [NUEVO] Análisis Covariado de Ocupación
    if enabled_sections.get('covariate_analysis', False) and 'covariate_analysis' not in results:
        update_status("⏳ Ejecutando modelos covariados (Regresión Ridge)...")
        try:
            cov_results = {}
            # Procesar TODAS las especies seleccionadas que tengan suficientes datos
            all_selected = wildlife_df['Especie_Categoria'].unique()
            for sp in all_selected:
                # El análisis de ocupación requiere un mínimo de datos, pero intentaremos con todas
                res = statistical_analysis.run_occupancy_analysis(wildlife_df, sp)
                if res and res.get('success'):
                    cov_results[sp] = res
            results['covariate_analysis'] = cov_results
        except Exception as e:
            print(f"Error en Covariate Analysis: {e}")
            results['covariate_analysis'] = None

    # 10. [NUEVO] Estatus Biogeográfico y Conservación
    if enabled_sections.get('conservation', True) and 'species_assessment' not in results:
        update_status("⏳ Evaluando estatus biogeográfico y legal...")
        try:
            from modules import species_assessment
            assessment = {}
            # Evaluar TODAS las especies seleccionadas, excluyendo humanos y domésticos para listas de conservación
            all_species = wildlife_df['Especie_Categoria'].unique()
            for sp in all_species:
                if species_assessment.is_excluded_species(sp):
                    continue
                nom_cat = species_assessment.assess_nom059_status(sp)
                bg_cat = species_assessment.assess_biogeographic_status(sp)
                assessment[sp] = {
                    'nom_059': species_assessment.get_nom059_description(nom_cat, 'es'),
                    'iucn': species_assessment.assess_species_conservation_status(sp),
                    'biogeographic': species_assessment.get_biogeographic_description(bg_cat, 'es')
                }
            results['species_assessment'] = assessment
        except Exception as e:
            print(f"Error en species_assessment: {e}")
            results['species_assessment'] = {}

    # 11. [NUEVO] Fichas Técnicas por Especie
    if enabled_sections.get('species_fact_sheets', False) and 'species_fact_sheets' not in results:
        update_status("⏳ Compilando fichas técnicas por especie...")
        try:
            fact_sheets = {}
            all_species = wildlife_df['Especie_Categoria'].unique()
            for sp in all_species:
                sp_df = wildlife_df[wildlife_df['Especie_Categoria'] == sp]
                fact_sheets[sp] = {
                    'records': len(sp_df),
                    'sites': sp_df['Sitio'].nunique() if 'Sitio' in sp_df.columns else 0,
                    'first_detection': sp_df['Fecha_Captura'].min(),
                    'last_detection': sp_df['Fecha_Captura'].max(),
                    'peak_activity': int(pd.to_datetime(sp_df['Hora'], errors='coerce').dt.hour.mode().iloc[0]) if not sp_df['Hora'].dropna().empty else None
                }
            results['species_fact_sheets'] = fact_sheets
        except:
            results['species_fact_sheets'] = {}

    update_status("✅ Hidratación completada")
    return results

    update_status("✅ Hidratación completada")
    return results
