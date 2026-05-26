"""
FORXIME/2 - Plataforma de Análisis de Datos de Cámaras Trampa
Desarrollado por: Biólogo Erick Elio Chavez Gurrola
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os


# Importar módulos
from modules import data_processing, statistical_analysis, temporal_analysis
from modules import environmental_vars, anthropogenic_impact, sampling_evaluation
from modules import visualization, interpretation, livestock_management, species_assessment, hunting_info
from modules import taxonomy_manager, spatial_models, hydration_helper
from utils import validators, geospatial, helpers
from utils.assets_base64 import LOGO_B64

# Configuración de la página
st.set_page_config(
    page_title="FORXIME/2 - Análisis de Cámaras Trampa",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .developer-credit {
        text-align: center;
        font-style: italic;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 2rem;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

if 'data' not in st.session_state:
    st.session_state.data = None

if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

if 'results' not in st.session_state:
    st.session_state.results = {}

# Cargar traducciones
def load_translations():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'translations.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

translations = load_translations()

def t(key):
    """Función helper para traducciones"""
    return translations[st.session_state.language].get(key, key)

# Sidebar - Navegación y configuración
with st.sidebar:
    # Logo - Usar versión Base64 para que funcione en el navegador sin archivos externos
    try:
        st.image(LOGO_B64, use_container_width=True)
    except:
        # Fallback a placeholder si falla
        st.image("https://via.placeholder.com/200x100/2E7D32/FFFFFF?text=FORXIME/2", use_container_width=True)
    
    # Selector de idioma
    language_options = {'Español': 'es', 'English': 'en'}
    selected_lang = st.selectbox(
        t('language'),
        options=list(language_options.keys()),
        index=0 if st.session_state.language == 'es' else 1
    )
    st.session_state.language = language_options[selected_lang]
    
    st.markdown("---")
    
    # Menú de navegación
    menu_options = [
        t('menu_home'),
        t('menu_process'),
        t('menu_results'),
        "🏷️ Gestor de Taxonomía",
        t('menu_instructions'),
        t('menu_donations')
    ]
    
    page = st.radio(t('menu_navigation'), menu_options, label_visibility="collapsed")

# Página de Inicio
if page == t('menu_home'):
    st.markdown(f'<div class="main-header">{t("welcome_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="developer-credit">{t("developer")}</div>', unsafe_allow_html=True)
    
    # Información del desarrollador
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <a href='https://orcid.org/0009-0007-7054-6999' target='_blank' style='margin: 0 10px;'>
            <img src='https://orcid.org/sites/default/files/images/orcid_16x16.png' alt='ORCID' style='vertical-align: middle;'/>
            ORCID: 0009-0007-7054-6999
        </a>
        |
        <a href='https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2' target='_blank' style='margin: 0 10px;'>
            ResearchGate Profile
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"## {t('welcome_subtitle')}")
    st.markdown(t('welcome_description'))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Análisis Estadístico**\n\nÍndices de biodiversidad y abundancia relativa")
    
    with col2:
        st.success("⏰ **Análisis Temporal**\n\nPatrones de actividad y solapamiento temporal")
    
    with col3:
        st.warning("🌍 **Variables Ambientales**\n\nAnálisis de factores que influyen en la fauna")
    
    st.markdown("---")
    
    # Instrucciones rápidas
    with st.expander("🚀 Inicio Rápido"):
        st.markdown("""
        1. Ve a **Procesar Datos** en el menú lateral
        2. Elige entre entrada manual o carga de archivo Excel
        3. Completa la información de sitios, cámaras y especies
        4. Opcionalmente, agrega observaciones de comportamiento
        5. Procesa los datos y visualiza los resultados
        """)
    
    # Disclaimer legal
    with st.expander("⚖️ Aviso Legal y Responsabilidad"):
        st.markdown("""
        ### 👨‍🔬 Desarrollador
        **Biólogo Erick Elio Chavez Gurrola**
        - 📧 Email: eliogurrola5@gmail.com
        - 🔬 ResearchGate: [Ver Perfil](https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2)
        
        ### ⚠️ Aviso de Responsabilidad
        Esta plataforma ha sido desarrollada y evaluada por el Biólogo Erick Elio Chavez Gurrola 
        con el objetivo de facilitar el análisis estadístico de datos de cámaras trampa para sitios 
        simples y pareados.
        
        **IMPORTANTE**: Si bien se han implementado las mejores prácticas científicas y estadísticas 
        disponibles, los resultados generados por esta plataforma pueden contener errores o imprecisiones. 
        
        **Es responsabilidad exclusiva del usuario**:
        - Validar los resultados antes de su uso
        - Verificar la coherencia de los análisis
        - Interpretar correctamente los resultados en su contexto
        - No utilizar los resultados sin revisión previa en publicaciones, informes técnicos o toma de decisiones de manejo
        
        ### 🐛 Reporte de Errores
        Si detecta algún error, comportamiento inesperado o tiene sugerencias de mejora, por favor contacte 
        al desarrollador a través de:
        - 📧 **Email**: eliogurrola5@gmail.com
        - 🔬 **ResearchGate**: Mensaje directo al perfil
        
        Su retroalimentación es valiosa para mejorar continuamente la plataforma y beneficiar a la 
        comunidad científica.
        
        ### 📜 Licencia
        Esta plataforma es de código abierto y se distribuye bajo licencia MIT. Puede ser utilizada 
        libremente con fines académicos y de investigación.
        """)


# Página de Procesamiento de Datos
elif page == t('menu_process'):
    st.title(t('process_data_title'))
    
    st.subheader("📁 " + t('upload_file'))
    
    # Botón para descargar plantilla
    template_df = data_processing.create_excel_template()
    
    # Convertir a Excel en memoria
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Datos')
    
    st.download_button(
        label="⬇️ " + t('download_template'),
        data=buffer.getvalue(),
        file_name="plantilla_forxime2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Cargar archivo
    uploaded_file = st.file_uploader(
        t('upload_file'),
        type=['xlsx', 'xls'],
        help="Carga un archivo Excel con el formato de la plantilla"
    )
    
    if uploaded_file is not None:
        # Crear indicador de progreso
        progress_container = st.empty()
        status_container = st.empty()
        
        with progress_container:
            progress_bar = st.progress(0)
        
        try:
            # Paso 1: Leer archivo
            status_container.text("⏳ Paso 1/3: Leyendo archivo Excel...")
            progress_bar.progress(0.33)
            
            success, result = data_processing.process_excel_data(uploaded_file)
            
            # Paso 2: Validar datos
            status_container.text("⏳ Paso 2/3: Validando datos...")
            progress_bar.progress(0.66)
            
            if success:
                # Paso 3: Procesar
                status_container.text("⏳ Paso 3/3: Procesando datos...")
                progress_bar.progress(1.0)
                
                import time
                time.sleep(0.3)  # Breve pausa para mostrar 100%
                
                # Limpiar indicadores
                progress_container.empty()
                status_container.empty()
                
                st.success(t('file_uploaded'))
                st.session_state.data = result
                
                # Mostrar preview
                st.subheader("Vista Previa de Datos")
                st.dataframe(result.head(10))
                
                # Métricas básicas
                metrics = data_processing.calculate_basic_metrics(result)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Registros", metrics['total_records'])
                col2.metric("Cámaras", metrics['total_cameras'])
                col3.metric("Sitios", metrics['total_sites'])
                col4.metric("Especies", metrics['total_species'])
            else:
                # Limpiar indicadores
                progress_container.empty()
                status_container.empty()
                st.error(f"Error: {result}")
                
        except Exception as e:
            # Limpiar indicadores en caso de error
            progress_container.empty()
            status_container.empty()
            st.error(f"Error procesando archivo: {str(e)}")
    
    
    # Botón de procesamiento
    if st.session_state.data is not None:
        st.markdown("---")
        
        st.markdown("---")
        
        if st.button("🚀 " + t('process_button'), type="primary"):
            
            # Crear barra de progreso y contenedor de estado
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Importar time para el contador
            import time
            
            # Determinar total de pasos
            total_steps = 16  # Preparación + 14 Análisis + Finalización
            
            current_step = 0
            step_times = []  # Para calcular tiempo restante
            start_time = time.time()
            
            try:
                # Paso 0: Preparación de datos (Geospatial y Eventos)
                step_start = time.time()
                current_step += 1
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Convirtiendo coordenadas y calculando eventos...")
                
                # Conversión de Fechas y Horas
                df = st.session_state.data.copy()
                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
                    df = df.dropna(subset=['Fecha'])
                if 'Hora' in df.columns:
                    df['Hora'] = pd.to_datetime(df['Hora'].astype(str), format='mixed', errors='coerce').dt.time
                
                # Coordenadas y Eventos
                from utils import geospatial, helpers
                df = geospatial.add_latlon_columns(df)
                df = helpers.calculate_independent_events(df)
                df['Eventos_Independientes'] = df['Evento_Independiente'].astype(int)
                
                # Paso 1: Agrupar sitios
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Agrupando sitios por proximidad...")
                df = data_processing.group_sites(df, max_distance=10)
                step_times.append(time.time() - step_start)
                
                # Paso 2: Filtrar fauna silvestre
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                
                # Calcular tiempo restante
                if len(step_times) > 0:
                    avg_time = sum(step_times) / len(step_times)
                    remaining = avg_time * (total_steps - current_step)
                    mins, secs = divmod(int(remaining), 60)
                    time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                    status_text.text(f"⏳ Paso {current_step}/{total_steps}: Filtrando fauna silvestre...\n⏱️ Tiempo restante estimado: {time_str}")
                else:
                    status_text.text(f"⏳ Paso {current_step}/{total_steps}: Filtrando fauna silvestre...")
                
                # Se desactiva el filtrado automático por solicitud del usuario
                # Ahora wildlife_df contiene todos los datos y la exclusión se hace manual en el panel de resultados
                wildlife_df = df.copy()
                step_times.append(time.time() - step_start)
                
                st.session_state.processed_data = df
                st.session_state.wildlife_data = wildlife_df
                
                # Calcular todos los análisis
                results = {}
                
                # Paso 3: Métricas básicas
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Calculando métricas básicas...\n⏱️ Tiempo restante estimado: {time_str}")
                results['basic_metrics'] = data_processing.calculate_basic_metrics(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 4: Biodiversidad
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Calculando índices de biodiversidad...\n⏱️ Tiempo restante estimado: {time_str}")
                results['biodiversity'] = statistical_analysis.calculate_biodiversity_indices(wildlife_df)
                results['biodiversity_by_site'] = statistical_analysis.calculate_biodiversity_by_site(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 5: Dendrograma
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Generando dendrograma de Bray-Curtis...\n⏱️ Tiempo restante estimado: {time_str}")
                results['dendrogram'] = statistical_analysis.create_bray_curtis_dendrogram(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 6: Abundancia relativa (RAI)
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Calculando índice de abundancia relativa...\n⏱️ Tiempo restante estimado: {time_str}")
                results['rai'] = statistical_analysis.calculate_relative_abundance_index(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # PASO DE OCUPACIÓN ELIMINADO
                
                # Paso 7: Análisis temporal (patrones de actividad)
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Analizando patrones de actividad temporal...\n⏱️ Tiempo restante estimado: {time_str}")
                results['activity_patterns'] = {}
                for species in wildlife_df['Especie_Categoria'].unique()[:10]:  # Top 10 especies
                    pattern = temporal_analysis.calculate_activity_pattern(wildlife_df, species)
                    if pattern:
                        results['activity_patterns'][species] = pattern
                step_times.append(time.time() - step_start)
                
                
                # Solapamiento temporal se calculará bajo demanda en la sección de Resultados
                results['temporal_overlaps'] = []
                results['temporal_overlap_note'] = {'on_demand': True}
                
                # Paso 9: Impacto antropogénico
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Evaluando impacto antropogénico...\n⏱️ Tiempo restante estimado: {time_str}")
                results['anthropogenic'] = anthropogenic_impact.calculate_anthropogenic_impact(df)
                results['anthropogenic_by_site'] = anthropogenic_impact.calculate_impact_by_site(df)
                step_times.append(time.time() - step_start)
                
                # Paso 10: Evaluación de muestreo
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Evaluando esfuerzo de muestreo...\n⏱️ Tiempo restante estimado: {time_str}")
                results['sampling_effort'] = sampling_evaluation.calculate_sampling_effort(wildlife_df)
                results['sampling_recommendations'] = sampling_evaluation.generate_sampling_recommendations(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 11: Curva de acumulación
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Generando curva de acumulación de especies...\n⏱️ Tiempo restante estimado: {time_str}")
                results['accumulation'] = statistical_analysis.calculate_species_accumulation_curve(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 12: Co-ocurrencia
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Calculando matriz de co-ocurrencia...\n⏱️ Tiempo restante estimado: {time_str}")
                results['co_occurrence'] = statistical_analysis.calculate_co_occurrence_matrix(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 13: Manejo ganadero
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Generando reporte de manejo ganadero...\n⏱️ Tiempo restante estimado: {time_str}")
                results['livestock_management'] = livestock_management.generate_livestock_management_report(df, st.session_state.language)
                step_times.append(time.time() - step_start)
                
                # Paso 14: Evaluación de especies
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Evaluando prioridades de conservación...\n⏱️ Tiempo restante estimado: {time_str}")
                results['conservation_priorities'] = species_assessment.generate_conservation_priorities_report(wildlife_df, st.session_state.language)
                results['critical_habitats'] = species_assessment.identify_critical_habitats(wildlife_df)
                step_times.append(time.time() - step_start)
                
                # Paso 15 (o 14 si no hay solapamiento): Información cinegética
                step_start = time.time()
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                avg_time = sum(step_times) / len(step_times)
                remaining = avg_time * (total_steps - current_step)
                mins, secs = divmod(int(remaining), 60)
                time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"⏳ Paso {current_step}/{total_steps}: Generando plan de manejo cinegético...\n⏱️ Tiempo restante estimado: {time_str}")
                results['hunting_info'] = hunting_info.generate_hunting_management_plan(wildlife_df, st.session_state.language)
                step_times.append(time.time() - step_start)
                
                # Finalizar
                current_step += 1
                progress_bar.progress(1.0)
                total_time = time.time() - start_time
                mins, secs = divmod(int(total_time), 60)
                total_time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                status_text.text(f"✅ Completado: {total_steps}/{total_steps} pasos procesados exitosamente")
                
                st.session_state.results = results
                
                # Mostrar mensaje de éxito con tiempo
                import time
                time.sleep(0.5)  # Breve pausa para que el usuario vea el 100%
                status_text.empty()
                progress_bar.empty()
                
                st.success("✅ ¡Análisis completado! Ve a la sección 'Resultados' para ver los análisis.")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error durante el procesamiento: {str(e)}")
                st.exception(e)

# Página de Taxonomía
elif page == "🏷️ Gestor de Taxonomía":
    taxonomy_manager.render_taxonomy_manager()

# Página de Resultados
elif page == t('menu_results'):
    
    st.title(t('results_title'))
    
    if st.session_state.results:
        results = st.session_state.results
        wildlife_df = st.session_state.wildlife_data
        
        # Tabs para organizar resultados
        # Menú de navegación tipo dropdown para evitar scroll horizontal
        analysis_options = [
            "📊 Biodiversidad",
            "🌳 Dendrograma",
            "📈 Abundancia",
            "⏰ Patrones Temporales",
            "🔄 Solapamiento",
            "🗺️ Mapa",
            "👥 Impacto Antropogénico",
            "📋 Evaluación Muestreo",
            "🐄 Manejo Ganadero",
            "🦁 Conservación",
            "🎯 Información Cinegética"
        ]
        
        selected_analysis = st.selectbox(
            "Seleccionar Análisis:",
            options=analysis_options,
            index=0
        )
        
        st.markdown("---")
        
        # Tab 1: Biodiversidad
        if selected_analysis == "📊 Biodiversidad":
            st.header(t('biodiversity_indices'))
            
            # NUEVO: Filtrado de categorías
            with st.expander("🔧 Filtrar Categorías del Análisis", expanded=False):
                st.markdown("Excluye categorías que no deben considerarse en los índices de biodiversidad (ej: fotos vacías, humanos, etc.)")
                
                all_species = sorted(wildlife_df['Especie_Categoria'].unique())
                
                # Detectar categorías comunes a excluir
                common_exclusions = []
                for species in all_species:
                    species_lower = species.lower()
                    if any(word in species_lower for word in ['vacío', 'vacio', 'empty', 'sin identificar', 
                                                                'no identificad', 'humano', 'human', 'persona', 
                                                                'people', 'gente', 'desconocid']):
                        common_exclusions.append(species)
                
                if common_exclusions:
                    st.info(f"💡 **Sugerencia**: Considera excluir: {', '.join(common_exclusions)}")
                
                excluded_categories = st.multiselect(
                    "Selecciona categorías a EXCLUIR del análisis de biodiversidad",
                    options=all_species,
                    default=[],
                    key="biodiv_exclude",
                    help="Las categorías seleccionadas no se incluirán en el cálculo de índices de biodiversidad"
                )
            
            # Filtrar datos
            if excluded_categories:
                filtered_df = wildlife_df[~wildlife_df['Especie_Categoria'].isin(excluded_categories)]
                st.success(f"📊 Analizando **{filtered_df['Especie_Categoria'].nunique()} especies** (excluidas: {len(excluded_categories)})")
            else:
                filtered_df = wildlife_df
            
            # Recalcular índices con datos filtrados
            if excluded_categories:
                indices = statistical_analysis.calculate_biodiversity_indices(filtered_df)
            else:
                indices = results['biodiversity']
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t('shannon_index'), f"{indices['Shannon']:.3f}")
            col2.metric(t('simpson_index'), f"{indices['Simpson']:.3f}")
            col3.metric(t('species_richness'), indices['Richness'])
            col4.metric(t('pielou_evenness'), f"{indices['Pielou_Evenness']:.3f}")
            
            # Gráfica de índices
            fig_indices = visualization.create_biodiversity_indices_chart(indices)
            st.plotly_chart(fig_indices, use_container_width=True)
            
            # Interpretación
            with st.expander("📖 " + t('interpretation')):
                interp = interpretation.interpret_biodiversity_indices(indices, st.session_state.language)
                st.markdown(interp)
            
            # Biodiversidad por sitio
            st.subheader("Biodiversidad por Sitio")
            if excluded_categories:
                biodiv_by_site = statistical_analysis.calculate_biodiversity_by_site(filtered_df)
                st.dataframe(biodiv_by_site)
            else:
                st.dataframe(results['biodiversity_by_site'])
        
        # Tab 2: Dendrograma
        elif selected_analysis == "🌳 Dendrograma":
            st.header("Dendrograma de Bray-Curtis")
            
            with st.expander("🔧 Configuración del Dendrograma", expanded=True):
                st.markdown("Ajusta qué especies y qué transformaciones aplicar para el análisis de similitud.")
                
                # --- NUEVO: Filtrado de especies para Dendrograma ---
                all_species_dend = sorted(wildlife_df['Especie_Categoria'].unique())
                excluded_dend = st.multiselect(
                    "Selecciona especies a EXCLUIR del dendrograma",
                    options=all_species_dend,
                    default=[],
                    key="dend_exclude_v2"
                )
                
                # 2. Transformación
                apply_hellinger = st.checkbox(
                    "Aplicar Transformación de Hellinger", 
                    value=False,
                    help="Recomendado para distancias de Bray-Curtis. Reduce el peso de especies súper-abundantes y resalta la composición real."
                )
            
            # Filtrar y generar usando el df local
            if excluded_dend:
                dend_df = wildlife_df[~wildlife_df['Especie_Categoria'].isin(excluded_dend)]
            else:
                dend_df = wildlife_df
            
            # Determinar columna de sitio
            site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in dend_df.columns else 'Sitio'
            
            if site_col not in dend_df.columns or dend_df[site_col].nunique() < 2:
                st.warning("Se necesitan al menos 2 sitios con datos para generar el dendrograma.")
            else:
                if st.button("🌳 Generar Dendrograma", type="primary", key="btn_generar_dend"):
                    with st.spinner("Generando dendrograma..."):
                        dend_data = statistical_analysis.create_bray_curtis_dendrogram(dend_df, transform_hellinger=apply_hellinger)
                    st.session_state['last_dend_data'] = dend_data

                dend_data = st.session_state.get('last_dend_data', results.get('dendrogram'))
                
                if dend_data:
                    fig_dend = visualization.create_dendrogram_plot(
                        dend_data['linkage_matrix'],
                        dend_data['site_names']
                    )
                    st.pyplot(fig_dend)
                    
                    # Interpretación
                    with st.expander("📖 " + t('interpretation')):
                        interp = interpretation.interpret_dendrogram(
                            dend_data['distance_matrix'],
                            dend_data['site_names'],
                            st.session_state.language
                        )
                        st.markdown(interp)
                else:
                    st.error("No se pudo generar el dendrograma con los filtros seleccionados.")
        
        # Tab 3: Abundancia
        elif selected_analysis == "📈 Abundancia":
            st.header(t('abundance_analysis'))
            
            # NUEVO: Filtrado de categorías para gráficas
            with st.expander("🔧 Filtrar Categorías de las Gráficas", expanded=False):
                st.markdown("Oculta categorías específicas de las visualizaciones de abundancia")
                
                all_species_abundance = sorted(wildlife_df['Especie_Categoria'].unique())
                
                # Detectar categorías comunes a excluir
                common_exclusions_abundance = []
                for species in all_species_abundance:
                    species_lower = species.lower()
                    if any(word in species_lower for word in ['vacío', 'vacio', 'empty', 'sin identificar', 
                                                                'no identificad', 'humano', 'human', 'persona', 
                                                                'people', 'gente', 'desconocid']):
                        common_exclusions_abundance.append(species)
                
                if common_exclusions_abundance:
                    st.info(f"💡 **Sugerencia**: Considera excluir: {', '.join(common_exclusions_abundance)}")
                
                excluded_from_charts = st.multiselect(
                    "Selecciona categorías a EXCLUIR de las gráficas",
                    options=all_species_abundance,
                    default=[],
                    key="abundance_exclude",
                    help="Las categorías seleccionadas no aparecerán en las gráficas de abundancia"
                )
            
            # Filtrar datos para gráficas
            if excluded_from_charts:
                chart_df = wildlife_df[~wildlife_df['Especie_Categoria'].isin(excluded_from_charts)]
                rai_filtered = results['rai'][~results['rai']['Especie'].isin(excluded_from_charts)]
                st.success(f"📊 Mostrando **{chart_df['Especie_Categoria'].nunique()} especies** (ocultas: {len(excluded_from_charts)})")
            else:
                chart_df = wildlife_df
                rai_filtered = results['rai']
            
            # RAI
            st.subheader("Índice de Abundancia Relativa (RAI)")
            fig_rai = visualization.create_rai_chart(rai_filtered)
            st.plotly_chart(fig_rai, use_container_width=True)
            
            st.dataframe(rai_filtered)
            
            # Gráfica de abundancia
            st.subheader("Abundancia por Especie")
            fig_abundance = visualization.create_abundance_bar_chart(chart_df)
            st.plotly_chart(fig_abundance, use_container_width=True)
            
            # Curva de acumulación
            st.subheader("Curva de Acumulación de Especies")
            fig_accum = visualization.create_accumulation_curve_plot(results['accumulation'])
            st.plotly_chart(fig_accum, use_container_width=True)
            
            # Mapa de calor de co-ocurrencia
            st.subheader("Co-ocurrencia de Especies")
            fig_cooc = visualization.create_occupancy_heatmap(results['co_occurrence'])
            st.plotly_chart(fig_cooc, use_container_width=True)
        
        # Tab 4: Patrones Temporales
        elif selected_analysis == "⏰ Patrones Temporales":
            st.header(t('temporal_patterns'))
            
            if results['activity_patterns']:
                species_list = list(results['activity_patterns'].keys())
                selected_species = st.selectbox("Seleccionar Especie", species_list)
                
                if selected_species:
                    pattern_data = results['activity_patterns'][selected_species]
                    
                    plot_type = st.radio(
                        "Tipo de gráfica", 
                        ["circular", "linear"], 
                        horizontal=True,
                        key="activity_plot_type"
                    )
                    fig_activity = visualization.create_activity_pattern_plot(wildlife_df, selected_species, plot_type=plot_type)
                    
                    if fig_activity is not None:
                        st.plotly_chart(fig_activity, use_container_width=True)
                    else:
                        st.warning(f"No hay suficientes registros de hora validos para graficar el patron de {selected_species}.")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Patron", pattern_data['pattern'])
                    
                    peak_hour = pattern_data['mean_hour']
                    hours = int(peak_hour)
                    minutes = int((peak_hour - hours) * 60)
                    time_str = f"{hours:02d}:{minutes:02d}"
                    col2.metric("Hora Pico", time_str)
                    
                    col3.metric("Concentracion", f"{pattern_data['concentration']:.3f}")
            else:
                st.info("No hay suficientes datos para analisis temporal")
        
        # Tab 5: Solapamiento Temporal
        elif selected_analysis == "🔄 Solapamiento":
            st.header(t('temporal_overlap'))
            
            st.info("💡 Selecciona las especies que deseas comparar y calcula el solapamiento temporal bajo demanda")
            
            # Obtener especies disponibles
            if st.session_state.wildlife_data is not None:
                available_species = sorted(st.session_state.wildlife_data['Especie_Categoria'].unique())
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_species_overlap = st.multiselect(
                        "Selecciona especies para análisis de solapamiento",
                        options=available_species,
                        default=[],
                        key="overlap_species_selector",
                        help="Selecciona 2 o más especies (ej: Bos taurus, Panthera onca, Odocoileus virginianus)"
                    )
                
                with col2:
                    if len(selected_species_overlap) >= 2:
                        n_pairs = (len(selected_species_overlap) * (len(selected_species_overlap) - 1)) // 2
                        st.metric("Parejas a calcular", n_pairs)
                        
                        if st.button("🔄 Calcular Solapamiento", type="primary", key="calc_overlap_btn"):
                            with st.spinner("Calculando solapamiento temporal..."):
                                # Calculate overlaps on demand
                                overlap_results = []
                                progress_container = st.empty()
                                
                                total_pairs = n_pairs
                                current_pair = 0
                                
                                for i in range(len(selected_species_overlap)):
                                    for j in range(i + 1, len(selected_species_overlap)):
                                        sp1 = selected_species_overlap[i]
                                        sp2 = selected_species_overlap[j]
                                        
                                        current_pair += 1
                                        progress_container.text(f"Calculando pareja {current_pair}/{total_pairs}: {sp1} vs {sp2}")
                                        
                                        overlap_result = temporal_analysis.analyze_temporal_overlap(
                                            st.session_state.wildlife_data, sp1, sp2
                                        )
                                        
                                        if overlap_result.get('success', False):
                                            overlap_results.append(overlap_result)
                                
                                # Store in session state
                                st.session_state.on_demand_overlaps = overlap_results
                                progress_container.empty()
                                st.success(f"✅ Se calcularon {len(overlap_results)} solapamientos")
                    else:
                        st.warning("⚠️ Selecciona al menos 2 especies")
                
                st.markdown("---")
                
                # Display results if available
                if hasattr(st.session_state, 'on_demand_overlaps') and st.session_state.on_demand_overlaps:
                    st.subheader("📊 Resultados de Solapamiento Temporal")
                    
                    for overlap_data in st.session_state.on_demand_overlaps:
                        st.subheader(f"{overlap_data['species1']} vs {overlap_data['species2']}")
                        
                        fig_overlap = visualization.create_temporal_overlap_plot(overlap_data)
                        st.plotly_chart(fig_overlap, use_container_width=True)
                        
                        # Métricas
                        col1, col2 = st.columns(2)
                        
                        ridout = overlap_data['ridout_linkie']
                        kernel = overlap_data['kernel_overlap']
                        
                        col1.metric(
                            "Coef. Ridout-Linkie (Δ)",
                            f"{ridout['coefficient']:.3f}",
                            help=f"IC 95%: [{ridout['ci_lower']:.3f}, {ridout['ci_upper']:.3f}]"
                        )
                        col2.metric(
                            "Solapamiento KDE",
                            f"{kernel['overlap_percentage']:.1f}%"
                        )
                        
                        # Interpretación
                        with st.expander("📖 Interpretación"):
                            interp = interpretation.interpret_temporal_overlap(
                                overlap_data,
                                'general',
                                st.session_state.language
                            )
                            st.markdown(interp)
                        
                        st.markdown("---")
                else:
                    st.info("👆 Selecciona especies y haz clic en 'Calcular Solapamiento' para ver los resultados")
            else:
                st.warning("No hay datos disponibles")
        
        # Tab 6: Mapa
        elif selected_analysis == "🗺️ Mapa":
            st.header(t('study_area_map'))
            
            study_map = visualization.create_study_area_map(st.session_state.processed_data)
            
            if study_map:
                from streamlit_folium import folium_static
                folium_static(study_map, width=1200, height=600)
            else:
                st.error("No se pudo generar el mapa. Verifica las coordenadas.")
        

        
        # Tab 8: Impacto Antropogénico
        elif selected_analysis == "👥 Impacto Antropogénico":
            st.header(t('anthropogenic_impact'))
            
            anthro = results['anthropogenic']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Registros Totales", anthro['total_records'])
            col2.metric("Registros Antropogénicos", anthro['anthropogenic_records'])
            col3.metric("Porcentaje", f"{anthro['anthropogenic_percentage']:.1f}%")
            
            # Por sitio
            st.subheader("Impacto por Sitio")
            st.dataframe(results['anthropogenic_by_site'])
            
            # Interpretación
            with st.expander("📖 " + t('interpretation')):
                interp = interpretation.interpret_anthropogenic_impact(anthro, st.session_state.language)
                st.markdown(interp)
        
        # Tab 9: Evaluación de Muestreo
        elif selected_analysis == "📋 Evaluación Muestreo":
            st.header(t('sampling_evaluation'))
            
            st.subheader("Esfuerzo de Muestreo")
            st.dataframe(results['sampling_effort'])
            
            st.markdown("---")
            
            # NUEVO: Evaluación de espaciamiento de cámaras
            st.subheader("📍 Evaluación de Espaciamiento de Cámaras")
            
            spacing_issues = sampling_evaluation.detect_camera_spacing_issues(st.session_state.processed_data)
            
            if spacing_issues['has_issues']:
                st.warning(f"⚠️ Se detectaron {spacing_issues['n_close_pairs']} pares de cámaras muy cercanas (< 10m)")
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                col1.metric("Grupos de cámaras cercanas", spacing_issues['n_groups'])
                col2.metric("Distancia promedio", f"{spacing_issues['avg_distance']:.1f}m")
                col3.metric("Distancia mínima", f"{spacing_issues['min_distance']:.1f}m")
                
                # Mostrar tabla de cámaras cercanas
                st.markdown("**Cámaras detectadas:**")
                st.dataframe(spacing_issues['grouped_cameras'])
                
                # Recomendaciones específicas
                st.markdown("**Recomendaciones:**")
                for rec in spacing_issues['recommendations']:
                    st.info(rec)
                
                # Explicación adicional
                with st.expander("ℹ️ ¿Por qué es importante el espaciamiento?"):
                    st.markdown("""
                    ### Importancia del Espaciamiento de Cámaras
                    
                    **Independencia Espacial:**
                    - Cámaras muy cercanas (<10m) detectan los mismos individuos
                    - Se consideran el mismo sitio de muestreo
                    - Reduce el número de réplicas independientes
                    
                    **Recomendaciones Generales:**
                    - **Especies pequeñas** (roedores, aves): 50-100m
                    - **Especies medianas** (venados, coyotes): 200-500m
                    - **Especies grandes** (jaguar, puma): 500-1000m
                    
                    **Excepciones Válidas:**
                    - Múltiples ángulos del mismo sendero
                    - Estudio de comportamiento específico
                    - Validación de detecciones
                    
                    En estos casos, las cámaras cercanas son intencionales y aceptables.
                    """)
            else:
                st.success("✅ Todas las cámaras están bien espaciadas (> 10m de separación)")
                st.info("💡 El espaciamiento actual es adecuado para asegurar independencia espacial entre sitios.")
            
            st.markdown("---")
            
            # OPTIMIZADO: Curvas de Rarefacción con Lazy Loading
            st.subheader("📈 Curva de Rarefacción y Completitud del Muestreo")
            
            st.info("💡 Las curvas de rarefacción se calculan bajo demanda para optimizar el rendimiento. Haz clic en el botón para generar el análisis.")
            
            # Botón para calcular bajo demanda
            if st.button("🔄 Calcular Curva de Rarefacción", type="primary", key="calc_rarefaction_btn"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Paso 1: Calcular completitud (rápido)
                    status_text.text("⏳ Paso 1/2: Calculando completitud del muestreo...")
                    progress_bar.progress(0.3)
                    
                    completeness = statistical_analysis.estimate_sampling_completeness(wildlife_df, method='chao1')
                    
                    # Paso 2: Calcular rarefacción (más lento)
                    status_text.text("⏳ Paso 2/2: Generando curva de rarefacción (50 iteraciones)...")
                    progress_bar.progress(0.5)
                    
                    rarefaction_data = statistical_analysis.calculate_rarefaction_curve(wildlife_df, method='individual')
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Cálculo completado")
                    
                    # Guardar en session state
                    st.session_state.rarefaction_data = rarefaction_data
                    st.session_state.completeness_data = completeness
                    
                    import time
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Curva de rarefacción calculada exitosamente")
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Error al calcular rarefacción: {str(e)}")
            
            # Mostrar resultados si ya fueron calculados
            if hasattr(st.session_state, 'rarefaction_data') and st.session_state.rarefaction_data is not None:
                completeness = st.session_state.completeness_data
                rarefaction_data = st.session_state.rarefaction_data
                
                # Mostrar métricas de completitud
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Riqueza Observada", completeness['observed_richness'])
                col2.metric("Riqueza Estimada", completeness['estimated_richness'])
                col3.metric("Completitud", f"{completeness['completeness_percent']}%")
                
                # Color según estado
                status_colors = {
                    "Excelente": "🟢",
                    "Bueno": "🟡",
                    "Moderado": "🟠",
                    "Insuficiente": "🔴"
                }
                col4.metric("Estado", f"{status_colors.get(completeness['status'], '⚪')} {completeness['status']}")
                
                # Gráfica de rarefacción
                fig_rare = visualization.create_rarefaction_plot(rarefaction_data)
                st.plotly_chart(fig_rare, use_container_width=True)
                
                # Interpretación
                st.info(f"**{completeness['method']}**: {completeness['recommendation']}")
                
                # Detalles adicionales
                with st.expander("ℹ️ ¿Qué es la Curva de Rarefacción?"):
                    st.markdown(f"""
                    ### Interpretación de la Curva de Rarefacción
                    
                    La curva de rarefacción muestra cómo aumenta el número de especies detectadas conforme 
                    aumenta el esfuerzo de muestreo (número de individuos registrados).
                    
                    **Tu Muestreo:**
                    - **Especies observadas**: {completeness['observed_richness']}
                    - **Especies estimadas totales**: {completeness['estimated_richness']}
                    - **Completitud**: {completeness['completeness_percent']}%
                    - **Singletons** (especies con 1 registro): {completeness['singletons']}
                    - **Doubletons** (especies con 2 registros): {completeness['doubletons']}
                    
                    **¿Qué significa?**
                    
                    - Si la curva se **aplana** (asíntota): Has detectado la mayoría de especies presentes
                    - Si la curva sigue **subiendo**: Aún faltan especies por detectar, necesitas más muestreo
                    - **Completitud > 90%**: Excelente, el muestreo es suficiente
                    - **Completitud 75-90%**: Bueno, muestreo adecuado
                    - **Completitud < 75%**: Insuficiente, se recomienda más esfuerzo
                    
                    **Importancia Científica:**
                    
                    Las curvas de rarefacción son **obligatorias** en publicaciones científicas sobre biodiversidad.
                    Permiten:
                    - Justificar que el muestreo fue suficiente
                    - Comparar sitios con diferente esfuerzo de muestreo
                    - Estimar cuántas especies faltan por detectar
                    """)
            else:
                st.warning("⚠️ Aún no se ha calculado la curva de rarefacción. Haz clic en el botón de arriba para generarla.")
            
            st.markdown("---")
            
            st.subheader("Recomendaciones")
            
            if results['sampling_recommendations']:
                for rec in results['sampling_recommendations']:
                    priority_color = "🔴" if rec['priority'] == 'Alta' else "🟡" if rec['priority'] == 'Media' else "🟢"
                    st.markdown(f"{priority_color} **{rec['category']}** (Prioridad: {rec['priority']})")
                    st.info(rec['recommendation'])
            else:
                st.success("✅ El diseño de muestreo cumple con todos los estándares")
        
        # Tab 10: Manejo Ganadero
        elif selected_analysis == "🐄 Manejo Ganadero":
            st.header("🐄 Manejo Ganadero y Coexistencia con Fauna Silvestre")
            
            livestock_report = results.get('livestock_management', {})
            
            if livestock_report:
                # Resumen ejecutivo
                st.markdown(livestock_report.get('executive_summary', ''))
                
                st.markdown("---")
                
                # Depredadores detectados
                predators = livestock_report.get('predators_detected', {})
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Depredadores Alto Riesgo", len(predators.get('high_risk', [])))
                col2.metric("Depredadores Riesgo Moderado", len(predators.get('moderate_risk', [])))
                col3.metric("Total Especies Depredadoras", livestock_report.get('total_predator_species', 0))
                
                # Recomendaciones de pastoreo
                st.subheader("📋 Recomendaciones de Pastoreo por Especie")
                
                grazing_recs = livestock_report.get('grazing_recommendations', [])
                
                if grazing_recs:
                    for rec in grazing_recs:
                        with st.expander(f"🔍 {rec['species']} - Prioridad: {rec['priority']}"):
                            st.markdown(rec['recommendation'])
                else:
                    st.info("✅ No se detectaron depredadores de ganado en el área de estudio")
                
                # Zonas seguras para pastoreo
                st.subheader("🗺️ Clasificación de Zonas para Pastoreo")
                
                safe_zones = livestock_report.get('safe_zones')
                
                if safe_zones is not None and len(safe_zones) > 0:
                    st.dataframe(safe_zones)
                    
                    # Gráfica de zonas por seguridad
                    import plotly.express as px
                    
                    safety_counts = safe_zones['Clasificacion_Seguridad'].value_counts()
                    
                    fig_safety = px.pie(
                        values=safety_counts.values,
                        names=safety_counts.index,
                        title='Distribución de Sitios por Nivel de Seguridad',
                        color_discrete_map={
                            'Seguro': '#4CAF50',
                            'Riesgo Bajo': '#8BC34A',
                            'Riesgo Moderado': '#FFC107',
                            'Alto Riesgo': '#F44336'
                        }
                    )
                    
                    st.plotly_chart(fig_safety, use_container_width=True)
                
                # Información adicional
                with st.expander("ℹ️ Información Adicional sobre Coexistencia"):
                    st.markdown("""
                    ### Estrategias de Coexistencia Ganado-Fauna Silvestre
                    
                    **Medidas Preventivas:**
                    - Uso de perros guardianes entrenados
                    - Cercas eléctricas en áreas de alto riesgo
                    - Iluminación nocturna en corrales
                    - Vigilancia durante horas de mayor riesgo
                    
                    **Beneficios de la Coexistencia:**
                    - Conservación de depredadores tope (control de plagas)
                    - Mantenimiento del equilibrio ecológico
                    - Posibles incentivos económicos por conservación
                    - Turismo de observación de fauna
                    
                    **Reporte de Incidentes:**
                    - Documentar cualquier pérdida de ganado
                    - Identificar patrones de depredación
                    - Ajustar estrategias según resultados
                    """)
            else:
                st.info("No hay datos de manejo ganadero disponibles")
        
        # Tab 11: Prioridades de Conservación
        elif selected_analysis == "🦁 Conservación":
            st.header("🦁 Evaluación de Especies y Prioridades de Conservación")
            
            # Prioridades de conservación
            st.subheader("📊 Prioridades de Conservación por Especie")
            
            conservation_priorities = results.get('conservation_priorities')
            
            if conservation_priorities is not None and len(conservation_priorities) > 0:
                st.dataframe(conservation_priorities)
                
                # Gráfica de prioridades
                import plotly.express as px
                
                priority_counts = conservation_priorities['Prioridad'].value_counts()
                
                fig_priority = px.bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    title='Distribución de Especies por Nivel de Prioridad',
                    labels={'x': 'Nivel de Prioridad', 'y': 'Número de Especies'},
                    color=priority_counts.index,
                    color_discrete_map={
                        'Crítica': '#D32F2F',
                        'Alta': '#F57C00',
                        'Media': '#FBC02D',
                        'Baja': '#388E3C'
                    }
                )
                
                st.plotly_chart(fig_priority, use_container_width=True)
                
                # Especies de alta prioridad
                high_priority = conservation_priorities[
                    conservation_priorities['Prioridad'].isin(['Crítica', 'Alta'])
                ]
                
                if len(high_priority) > 0:
                    st.warning(f"⚠️ Se identificaron {len(high_priority)} especies de prioridad crítica o alta")
                    
                    st.subheader("🚨 Especies Prioritarias")
                    
                    for idx, row in high_priority.iterrows():
                        with st.expander(f"🔴 {row['Especie']} - {row['Prioridad']}"):
                            # Mostrar categorías de conservación
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Categoría IUCN", row['Categoria_IUCN'])
                                st.metric("Ocupación", row['Ocupacion'])
                            
                            with col2:
                                # Mostrar NOM-059 con color según categoría
                                nom_status = row.get('NOM_059', 'No listada')
                                if nom_status == 'En Peligro de Extinción':
                                    st.error(f"🚨 NOM-059: {nom_status}")
                                elif nom_status == 'Amenazada':
                                    st.warning(f"⚠️ NOM-059: {nom_status}")
                                elif nom_status == 'Sujeta a Protección Especial':
                                    st.info(f"ℹ️ NOM-059: {nom_status}")
                                else:
                                    st.metric("NOM-059", nom_status)
                                
                                st.metric("Abundancia Relativa", row['Abundancia_Relativa'])
                            
                            with col3:
                                st.metric("Estatus Biogeográfico", row.get('Estatus_Biogeografico', 'Nativa'))
                                st.metric("Puntaje de Prioridad", row['Puntaje_Total'])
                            
                            if row['Especie_Clave'] == 'Sí':
                                st.info("⭐ Esta es una especie clave (keystone species)")
            
            # Hábitats críticos
            st.subheader("🏞️ Hábitats Críticos para Conservación")
            
            critical_habitats = results.get('critical_habitats')
            
            if critical_habitats is not None and len(critical_habitats) > 0:
                st.dataframe(critical_habitats)
                
                # Sitios más importantes
                top_sites = critical_habitats.head(5)
                
                if len(top_sites) > 0:
                    st.subheader("🌟 Top 5 Sitios de Mayor Importancia")
                    
                    for idx, row in top_sites.iterrows():
                        importance_emoji = "🔴" if row['Importancia_Conservacion'] == 'Crítica' else \
                                         "🟠" if row['Importancia_Conservacion'] == 'Alta' else \
                                         "🟡" if row['Importancia_Conservacion'] == 'Media' else "🟢"
                        
                        st.markdown(f"{importance_emoji} **{row['Sitio']}** - {row['Importancia_Conservacion']}")
                        st.markdown(f"   - Riqueza total: {row['Riqueza_Total']} especies")
                        st.markdown(f"   - Especies amenazadas: {row['Especies_Amenazadas']}")
                        
                        if row['Lista_Especies_Amenazadas'] != 'Ninguna':
                            st.markdown(f"   - Especies: {row['Lista_Especies_Amenazadas']}")
                        
                        st.markdown("")
            
            # Recomendaciones de monitoreo
            with st.expander("📋 Recomendaciones de Monitoreo y Conservación"):
                st.markdown("""
                ### Acciones Recomendadas
                
                **Para Especies de Prioridad Crítica:**
                - Aumentar esfuerzo de monitoreo (más cámaras, mayor duración)
                - Implementar protocolos específicos de conservación
                - Evaluar amenazas inmediatas (caza, pérdida de hábitat)
                - Considerar establecimiento de áreas protegidas
                - Coordinar con autoridades ambientales
                
                **Para Hábitats Críticos:**
                - Priorizar protección de sitios con mayor número de especies amenazadas
                - Implementar corredores biológicos entre sitios importantes
                - Minimizar perturbaciones antropogénicas
                - Establecer zonas de amortiguamiento
                
                **Monitoreo a Largo Plazo:**
                - Mantener cámaras trampa en sitios críticos
                - Evaluar tendencias poblacionales
                - Documentar cambios en uso de hábitat
                - Adaptar estrategias según resultados
                """)
        
        # Tab 12: Información Cinegética
        elif selected_analysis == "🎯 Información Cinegética":
            st.header("🎯 Información Cinegética y Manejo de Especies de Caza")
            
            hunting_plan = results.get('hunting_info', {})
            
            if hunting_plan.get('has_game_species', False):
                st.success(f"✅ Se detectaron {hunting_plan['species_detected']} especies de interés cinegético")
                
                # Tabla de especies cinegéticas
                st.subheader("📋 Especies Cinegéticas Detectadas")
                
                game_species_df = hunting_plan['species_list']
                st.dataframe(game_species_df)
                
                # Calendario cinegético
                st.subheader("📅 Calendario de Temporadas")
                
                calendar_md = hunting_info.generate_hunting_calendar(game_species_df, st.session_state.language)
                st.markdown(calendar_md)
                
                # Recomendaciones por especie
                st.subheader("🎯 Recomendaciones de Cosecha Sostenible")
                
                for rec in hunting_plan['recommendations']:
                    with st.expander(f"🦌 {rec['common_name']} ({rec['species']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Nivel de Abundancia", rec['abundance_level'])
                            st.metric("RAI", f"{rec['rai']:.2f}")
                        
                        with col2:
                            # Indicador de cosecha
                            if "NO se recomienda" in rec['harvest_recommendation']:
                                st.error(rec['harvest_recommendation'])
                            elif "limitada" in rec['harvest_recommendation']:
                                st.warning(rec['harvest_recommendation'])
                            else:
                                st.success(rec['harvest_recommendation'])
                        
                        # Notas
                        if rec['notes']:
                            st.markdown("**Notas:**")
                            for note in rec['notes']:
                                st.markdown(f"- {note}")
                
                # Recomendación de UMA
                if hunting_plan.get('uma_recommendation'):
                    st.subheader("🏛️ Recomendación de UMA")
                    st.markdown(hunting_plan['uma_recommendation'])
                
                # Evaluación de impacto
                st.subheader("⚠️ Evaluación de Impacto de Cacería")
                
                impact_assessment = hunting_info.assess_hunting_impact(
                    st.session_state.wildlife_data,
                    game_species_df,
                    st.session_state.language
                )
                
                if impact_assessment.get('has_data', False):
                    # Impactos potenciales
                    st.markdown("**Impactos Potenciales:**")
                    
                    for impact in impact_assessment['impacts']:
                        severity_color = "🔴" if impact['severity'] == 'Alta' else \
                                       "🟡" if impact['severity'] in ['Media', 'Baja-Media'] else "🟢"
                        
                        st.markdown(f"{severity_color} **{impact['type']}** (Severidad: {impact['severity']})")
                        st.markdown(f"   {impact['description']}")
                        
                        if isinstance(impact['affected_species'], list):
                            st.markdown(f"   Especies afectadas: {', '.join(impact['affected_species'])}")
                        else:
                            st.markdown(f"   {impact['affected_species']}")
                        
                        st.markdown("")
                    
                    # Medidas de mitigación
                    st.markdown("**Medidas de Mitigación Recomendadas:**")
                    
                    for measure in impact_assessment['mitigation_measures']:
                        st.info(f"**{measure['measure']}:** {measure['description']}")
                
                # Información adicional
                with st.expander("ℹ️ Información Legal y Normativa"):
                    st.markdown("""
                    ### Marco Legal en México
                    
                    **Ley General de Vida Silvestre (LGVS)**
                    - Regula el aprovechamiento sustentable de vida silvestre
                    - Establece requisitos para UMAs
                    
                    **NOM-059-SEMARNAT-2010**
                    - Lista de especies en riesgo
                    - Prohíbe aprovechamiento de especies en peligro sin autorización especial
                    
                    **Calendario Cinegético**
                    - Publicado anualmente por SEMARNAT
                    - Define temporadas, cuotas y métodos permitidos
                    
                    **Requisitos para Cacería Legal:**
                    1. Licencia de caza vigente
                    2. Permiso de aprovechamiento (UMA o PIMVS)
                    3. Respetar temporadas y cuotas
                    4. Reportar aprovechamientos
                    5. Pago de derechos correspondientes
                    
                    **Contacto:**
                    - SEMARNAT: www.gob.mx/semarnat
                    - PROFEPA (denuncias): 01-800-PROFEPA
                    """)
            
            else:
                st.info("ℹ️ No se detectaron especies de interés cinegético en los datos procesados. Por favor verifica que las especies estén correctamente identificadas.")
                
                st.markdown("""
                ### Especies Cinegéticas Comunes en México
                
                Aunque no se detectaron en este estudio, las siguientes son especies comunes de interés cinegético:
                
                **Ungulados:**
                - Venado Cola Blanca (*Odocoileus virginianus*)
                - Pecarí de Collar (*Pecari tajacu*)
                
                **Aves:**
                - Guajolote Silvestre (*Meleagris gallopavo*)
                - Codornices (varias especies)
                - Palomas y huilotas
                
                **Nota:** La cacería de estas especies requiere permisos y debe realizarse dentro de UMAs registradas.
                """)
        

    
    else:
        st.info("⚠️ No hay resultados disponibles. Primero procesa los datos en la sección 'Procesar Datos'.")

# Página de Gestión Ganadera
elif page == t('menu_livestock'):
    st.title("🐄 " + t('menu_livestock'))
    
    if st.session_state.processed_data is not None:
        # Generar reporte de manejo ganadero
        report = livestock_management.generate_livestock_management_report(
            st.session_state.processed_data, 
            st.session_state.language
        )
        
        # Mostrar resumen ejecutivo
        st.subheader("Resumen Ejecutivo")
        st.info(report['summary'])
        
        # Secciones del reporte
        tabs = st.tabs(["📊 Análisis de Carga", "🚧 Conflictos Especie-Ganado", "💊 Salud y Manejo", "📑 Recomendaciones"])
        
        with tabs[0]:
            st.write(report['carrying_capacity'])
            # Mostrar tabla de abundancia de ganado si hay
            if 'livestock_data' in report:
                st.dataframe(report['livestock_data'])
        
        with tabs[1]:
            st.write(report['conflicts'])
        
        with tabs[2]:
            st.write(report['health_management'])
            
        with tabs[3]:
            st.write(report['recommendations'])
            
        # Exportar sección
        st.markdown("---")
        st.subheader("📥 Exportar Reporte Ganadero")
        if st.button("Generar PDF de Gestión Ganadera"):
            st.warning("Función en desarrollo. Por ahora puede copiar el texto de las secciones.")
    else:
        st.warning("⚠️ Primero debes procesar los datos en la sección 'Procesar Datos'.")

# Página de Instrucciones
elif page == t('menu_instructions'):
    st.title(t('instructions_title'))
    
    st.markdown("""
    ## 📖 Guía de Uso de FORXIME/2
    
    ### 1. Preparación de Datos
    
    - Descarga la plantilla Excel desde la sección "Procesar Datos"
    - Completa todas las columnas requeridas:
        - **Sitio**: Nombre del sitio de muestreo
        - **Camara**: Identificador único de la cámara
        - **Coordenada_X_UTM**: Coordenada Este en formato UTM
        - **Coordenada_Y_UTM**: Coordenada Norte en formato UTM
        - **Zona_UTM**: Zona UTM (ej: 12N, 13S)
        - **Especie_Categoria**: Nombre de la especie
        - **Fecha**: Fecha de captura (DD/MM/AAAA)
        - **Hora**: Hora de captura (HH:MM:SS)
        - **Eventos_Independientes**: Número de eventos independientes
    
    ### 2. Procesamiento
    
    - Haz clic en "Procesar Datos"
    - El sistema automáticamente:
        - Agrupa cámaras cercanas (<10m)
        - Calcula índices de biodiversidad
        - Analiza patrones temporales
        - Evalúa impacto antropogénico
        - Genera recomendaciones
    
    ### 3. Visualización de Resultados
    
    Explora las diferentes pestañas:
    - **Biodiversidad**: Índices de Shannon, Simpson, riqueza
    - **Dendrograma**: Similitud entre sitios
    - **Abundancia**: RAI y curvas de acumulación
    - **Patrones Temporales**: Actividad por especie
    - **Solapamiento**: Análisis depredador-presa y competencia
    - **Mapa**: Visualización geográfica del estudio
    - **Impacto Antropogénico**: Evaluación de perturbación
    - **Evaluación Muestreo**: Calidad del diseño
    
    ### 4. Interpretación
    
    - Cada sección incluye interpretaciones automáticas
    - Expande las secciones "Interpretación" para más detalles
    - Las interpretaciones están en el idioma seleccionado
    
    
    
    ## 📧 Soporte
    
    Para preguntas o reportar problemas, contacta a:
    
    **Biólogo Erick Elio Chavez Gurrola**  
    Email: eliogurrola5@gmail.com  
    ORCID: [0009-0007-7054-6999](https://orcid.org/0009-0007-7054-6999)  
    ResearchGate: [Perfil de Investigador](https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2)
    """)

# Página de Donaciones
elif page == t('menu_donations'):
    st.title(t('donations_title'))
    
    st.markdown(t('donations_description'))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇲🇽 " + t('donation_mexico'))
        st.info(f"""
        **Banco:** BBVA  
        **{t('card_number')}:** 4152 3144 0105 9541  
        **Titular:** Erick Elio Chavez Gurrola
        """)
    
    with col2:
        st.subheader("🌎 " + t('donation_international'))
        st.info(f"""
        **PayPal**  
        **{t('paypal_email')}:** eliogurrola5@gmail.com
        """)
    
    st.markdown("---")
    st.success(t('thank_you'))
    
    st.markdown("""
    ### ¿Por qué donar?
    
    Tu donación ayuda a:
    - ✅ Mantener la plataforma gratuita y accesible
    - ✅ Desarrollar nuevas funcionalidades
    - ✅ Mejorar los algoritmos de análisis
    - ✅ Proporcionar soporte técnico
    - ✅ Crear tutoriales y documentación
    
    **¡Cada contribución cuenta!** 🙏
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>FORXIME/2</strong> - Plataforma de Análisis de Datos de Cámaras Trampa</p>
    <p>Desarrollado por Biólogo Erick Elio Chavez Gurrola | 2026</p>
    <p>
        <a href='https://orcid.org/0009-0007-7054-6999' target='_blank' style='color: #666; text-decoration: none; margin: 0 10px;'>
            <img src='https://orcid.org/sites/default/files/images/orcid_16x16.png' alt='ORCID' style='vertical-align: middle;'/>
            ORCID
        </a>
        |
        <a href='https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2' target='_blank' style='color: #666; text-decoration: none; margin: 0 10px;'>
            ResearchGate
        </a>
    </p>
    <p>Versión 2.0</p>
</div>
""", unsafe_allow_html=True)
