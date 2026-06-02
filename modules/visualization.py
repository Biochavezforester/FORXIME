"""
Módulo de visualización para FORXIME/2
Genera gráficas profesionales y mapas interactivos
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram
import io
import base64
import re

def is_scientific_name(name):
    """Detecta si un nombre es científico basándose en heurísticas"""
    if not isinstance(name, str): return False
    # Agregar animales domésticos y términos comunes a la exclusión
    exclude = ['vacío', 'vacio', 'humano', 'desconocido', 'vehículo', 'otro', 'antropogénico', 
               'sin identificar', 'sin fauna', 'nada', 'none', 'doméstico', 'domestico', 
               'perro', 'gato', 'caballo', 'vaca', 'cerdo', 'gallina', 'oveja', 'borrego', 'burro', 'mula']
    if any(e in name.lower() for e in exclude):
        return False
    words = name.split()
    # Dos palabras capitalizadas o segunda en minúscula (ej. Bos Taurus o Panthera onca)
    if len(words) >= 2 and words[0][0].isupper() and (words[1][0].isupper() or words[1][0].islower() or words[1].lower() in ['sp.', 'spp.']):
        return True
    return False

def italics_scientific(name):
    """Agrega tags de itálicas si el nombre es científico"""
    return f"<i>{name}</i>" if is_scientific_name(name) else name


def create_abundance_bar_chart(df, top_n=200):
    """
    Crea gráfica de barras de abundancia por especie
    
    Args:
        df: DataFrame con datos
        top_n: Número de especies a mostrar
    
    Returns:
        plotly figure
    """
    # Deduplicate columns to prevent aggregation errors
    df = df.loc[:, ~df.columns.duplicated()]
    
    abundance = df.groupby('Especie_Categoria', observed=True)['Eventos_Independientes'].sum().sort_values(ascending=False)

    
    top_species = abundance.head(top_n)
    
    # Aplicar cursivas a los nombres científicos en el eje Y
    y_labels = [italics_scientific(name) for name in top_species.index]
    
    fig = go.Figure(data=[
        go.Bar(
            x=top_species.values,
            y=y_labels,
            orientation='h',
            marker=dict(
                color=top_species.values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Eventos")
            ),
            text=top_species.values,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Abundancia por Especie (Top {min(top_n, len(top_species))})',
        xaxis_title='Número de Eventos Independientes',
        yaxis_title='Especie',
        height=max(400, len(top_species) * 25),
        template='plotly_white',
        margin=dict(l=150, r=20, t=50, b=50),
        font=dict(size=11)
    )
    
    return fig


def create_biodiversity_indices_chart(indices_dict):
    """
    Crea gráfica de índices de biodiversidad
    
    Args:
        indices_dict: Diccionario con índices
    
    Returns:
        plotly figure
    """
    metrics = ['Shannon', 'Simpson', 'Pielou_Evenness']
    values = [indices_dict.get(m, 0) for m in metrics]
    labels = ['Índice de Shannon', 'Índice de Simpson', 'Equitatividad de Pielou']
    
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker=dict(
                color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                line=dict(color='rgb(8,48,107)', width=1.5)
            ),
            text=[f'{v:.3f}' for v in values],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='Índices de Biodiversidad',
        yaxis_title='Valor del Índice',
        template='plotly_white',
        height=400
    )
    
    return fig


def create_dendrogram_plot(linkage_matrix, site_names):
    """
    Crea dendrograma de Bray-Curtis
    
    Args:
        linkage_matrix: Matriz de linkage
        site_names: Nombres de sitios
    
    Returns:
        matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    dendrogram(
        linkage_matrix,
        labels=site_names,
        ax=ax,
        color_threshold=0.7,
        above_threshold_color='gray'
    )
    
    ax.set_title('Dendrograma de Similitud de Bray-Curtis', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('Sitios', fontsize=10)
    ax.set_ylabel('Distancia de Bray-Curtis', fontsize=10)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig


def create_activity_pattern_plot(activity_data, species, plot_type='circular'):
    """
    Crea gráfica de patrón de actividad
    
    Args:
        activity_data: DataFrame filtrado
        species: Especie seleccionada
        plot_type: 'circular' o 'linear'
    
    Returns:
        plotly figure or None if insufficient data
    """
    # Ensure we have a 'Hora' column with numeric values
    if 'Hora' not in activity_data.columns:
        # Extraer hora de fecha si es necesario
        if 'Fecha' in activity_data.columns:
            activity_data['Hora'] = activity_data['Fecha'].dt.hour + activity_data['Fecha'].dt.minute/60
        else:
            return None
    
    # Convert 'Hora' to numeric decimal hours — handles str, datetime.time, and numeric
    import datetime as dt
    def parse_time_to_hours(time_val):
        """Convert time value (string, datetime.time, or numeric) to decimal hours"""
        try:
            if time_val is None:
                return np.nan
            # pandas NaT / float NaN
            try:
                if pd.isna(time_val):
                    return np.nan
            except (TypeError, ValueError):
                pass
            # datetime.time object (e.g. datetime.time(14, 30, 0))
            if isinstance(time_val, dt.time):
                return time_val.hour + time_val.minute / 60 + time_val.second / 3600
            # string (e.g. "14:30:00")
            if isinstance(time_val, str):
                parts = time_val.split(':')
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                s = int(float(parts[2])) if len(parts) > 2 else 0
                return h + m / 60 + s / 3600
            # Already numeric
            return float(time_val)
        except Exception:
            return np.nan

    activity_data = activity_data.copy()
    activity_data['Hora'] = activity_data['Hora'].apply(parse_time_to_hours)
        
    sp_data = activity_data[activity_data['Especie_Categoria'] == species]
    if sp_data.empty:
        return None
        
    # Calcular densidad Kernel
    from scipy import stats
    
    # Datos circulares (0-24h)
    hours = sp_data['Hora'].values.astype(float)  # Ensure numeric type
    # Remove NaN values
    hours = hours[~np.isnan(hours)]
    
    if len(hours) == 0:
        return None
    
    # Duplicar datos para continuidad circular
    hours_circ = np.concatenate([hours, hours + 24, hours - 24])
    
    # KDE
    try:
        kde = stats.gaussian_kde(hours_circ, bw_method=0.15)
        grid_hours = np.linspace(0, 24, 100)
        density = kde(grid_hours) * 3  # Normalizar por triplicación de datos
    except Exception as e:
        print(f"Error KDE: {e}")
        return None

    fig = go.Figure()

    if plot_type == 'circular':
        # Convertir horas a ángulos (0-360 grados)
        theta = (grid_hours / 24) * 360
        
        fig.add_trace(go.Scatterpolar(
            r=density,
            theta=theta,
            fill='toself',
            name=species,
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Marcadores Amanecer/Atardecer
        fig.add_trace(go.Scatterpolar(
            r=[0, max(density)], theta=[0, 0], mode='lines', line=dict(color='orange', dash='dash'), name='Amanecer (6:00)'
        ))
        fig.add_trace(go.Scatterpolar(
            r=[0, max(density)], theta=[180, 180], mode='lines', line=dict(color='red', dash='dash'), name='Atardecer (18:00)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max(density)*1.1]),
                angularaxis=dict(
                    tickmode='array', tickvals=[0, 90, 180, 270],
                    ticktext=['0:00', '6:00', '12:00', '18:00'], direction='clockwise'
                )
            ),
            title=dict(
                text=f'Patrón de Actividad Diario: {italics_scientific(species)}',
                x=0.5
            ),
            height=500, template='plotly_white'
        )

    else:  # Linear plot
        fig.add_trace(go.Scatter(
            x=grid_hours, 
            y=density,
            fill='tozeroy',
            name=species,
            line=dict(color='#ff7f0e', width=2)
        ))
        
        # Marcadores
        fig.add_vline(x=6, line_dash="dash", line_color="orange", annotation_text="Amanecer")
        fig.add_vline(x=18, line_dash="dash", line_color="red", annotation_text="Atardecer")
        
        fig.update_layout(
            title=f'Densidad de Actividad: {species}',
            xaxis_title='Hora del Día',
            yaxis_title='Densidad de Actividad',
            xaxis=dict(tickmode='linear', tick0=0, dtick=2, range=[0, 24]),
            height=400, template='plotly_white'
        )
        
    return fig


def create_temporal_overlap_plot(overlap_data):
    """
    Crea gráfica de solapamiento temporal entre dos especies
    
    Args:
        overlap_data: Diccionario con datos de solapamiento
    
    Returns:
        plotly figure
    """
    sp1 = overlap_data['species1']
    sp2 = overlap_data['species2']
    
    pattern1 = overlap_data['activity_pattern_sp1']
    pattern2 = overlap_data['activity_pattern_sp2']
    
    fig = go.Figure()
    
    sp1_disp = italics_scientific(sp1)
    sp2_disp = italics_scientific(sp2)
    
    # Especie 1
    theta1 = (pattern1['grid_hours'] / 24) * 360
    fig.add_trace(go.Scatterpolar(
        r=pattern1['density'],
        theta=theta1,
        fill='toself',
        name=sp1_disp,
        line=dict(color='#1f77b4', width=2),
        opacity=0.6
    ))
    
    # Especie 2
    theta2 = (pattern2['grid_hours'] / 24) * 360
    fig.add_trace(go.Scatterpolar(
        r=pattern2['density'],
        theta=theta2,
        fill='toself',
        name=sp2_disp,
        line=dict(color='#ff7f0e', width=2),
        opacity=0.6
    ))
    
    ridout_coef = overlap_data['ridout_linkie']['coefficient']
    kernel_pct = overlap_data['kernel_overlap']['overlap_percentage']
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 90, 180, 270],
                ticktext=['0:00', '6:00', '12:00', '18:00'],
                direction='clockwise'
            )
        ),
        title=f'Solapamiento Temporal: {sp1_disp} vs {sp2_disp}<br>' +
              f'Coef. Ridout-Linkie (Δ): {ridout_coef:.3f} | Solapamiento KDE: {kernel_pct:.1f}%',
        showlegend=True,
        height=500
    )
    
    return fig


def create_occupancy_heatmap(co_occurrence_matrix):
    """
    Crea mapa de calor de co-ocurrencia
    
    Args:
        co_occurrence_matrix: Matriz de co-ocurrencia
    
    Returns:
        plotly figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=co_occurrence_matrix.values,
        x=co_occurrence_matrix.columns,
        y=co_occurrence_matrix.index,
        colorscale='YlOrRd',
        text=co_occurrence_matrix.values,
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="N° Sitios<br>Compartidos")
    ))
    
    fig.update_layout(
        title='Mapa de Calor de Co-ocurrencia de Especies',
        xaxis_title='Especie',
        yaxis_title='Especie',
        height=max(500, len(co_occurrence_matrix) * 30),
        template='plotly_white'
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def create_study_area_map(df):
    """
    Crea mapa interactivo del área de estudio con Folium
    
    Args:
        df: DataFrame con coordenadas
    
    Returns:
        folium map
    """
    from utils.geospatial import get_bounding_box
    
    # Obtener bounding box
    bbox = get_bounding_box(df)
    
    if not bbox:
        return None
    
    # Crear mapa centrado
    m = folium.Map(
        location=[bbox['center_lat'], bbox['center_lon']],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Agregar capas adicionales
    folium.TileLayer('Esri WorldImagery', name='Satélite', attr='Esri').add_to(m)
    folium.TileLayer('OpenTopoMap', name='Topográfico', attr='OpenTopoMap').add_to(m)
    
    # Agregar marcadores de cámaras
    # Defensive: Sitio_Agrupado may be absent when data was imported without UTM coords
    if 'Sitio_Agrupado' not in df.columns:
        df = df.copy()
        df['Sitio_Agrupado'] = df['Camara']
    camera_coords = df[['Camara', 'Latitud', 'Longitud', 'Sitio_Agrupado']].drop_duplicates()


    marker_cluster = MarkerCluster(name='Cámaras').add_to(m)
    
    for idx, row in camera_coords.iterrows():
        if pd.notna(row['Latitud']) and pd.notna(row['Longitud']):
            # Obtener información de la cámara
            camera_data = df[df['Camara'] == row['Camara']]
            n_species = camera_data['Especie_Categoria'].nunique()
            n_events = camera_data['Eventos_Independientes'].sum()
            
            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>Cámara:</b> {row['Camara']}<br>
                <b>Sitio:</b> {row['Sitio_Agrupado']}<br>
                <b>Especies:</b> {n_species}<br>
                <b>Eventos:</b> {n_events}<br>
                <b>Coordenadas:</b> {row['Latitud']:.5f}, {row['Longitud']:.5f}
            </div>
            """
            
            folium.Marker(
                location=[row['Latitud'], row['Longitud']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row['Camara'],
                icon=folium.Icon(color='green', icon='camera', prefix='fa')
            ).add_to(marker_cluster)
    
    # Agregar heatmap de riqueza
    heat_data = [[row['Latitud'], row['Longitud'], 
                  df[df['Camara'] == row['Camara']]['Especie_Categoria'].nunique()] 
                 for idx, row in camera_coords.iterrows() 
                 if pd.notna(row['Latitud']) and pd.notna(row['Longitud'])]
    
    if heat_data:
        HeatMap(heat_data, name='Mapa de Calor - Riqueza', radius=15, blur=25).add_to(m)
    
    # Agregar control de capas
    folium.LayerControl().add_to(m)
    
    return m


def create_spatial_richness_map(df):
    """Crea mapa de densidad (heatmap) de riqueza para exportación estática de alta calidad"""
    try:
        # Agrupar riqueza por sitio
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        if site_col not in df.columns:
            return None
            
        spatial_data = df.groupby([site_col, 'Latitud', 'Longitud'], observed=True).agg({

            'Especie_Categoria': 'nunique'
        }).reset_index()
        spatial_data.columns = [site_col, 'Latitud', 'Longitud', 'Riqueza']
        
        # Si no hay coordenadas válidas, retornar None
        if spatial_data['Latitud'].isnull().all():
            return None
            
        fig = px.density_mapbox(
            spatial_data, 
            lat='Latitud', 
            lon='Longitud', 
            z='Riqueza', 
            radius=20,
            hover_name=site_col, 
            color_continuous_scale='Viridis',
            zoom=12,
            title='Distribución Espacial de la Riqueza de Especies (Heatmap)'
        )
        
        # Agregar los puntos de las cámaras encima
        fig.add_trace(go.Scattermapbox(
            lat=spatial_data['Latitud'],
            lon=spatial_data['Longitud'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=8, color='white', opacity=0.7),
            text=spatial_data[site_col],
            hoverinfo='text',
            showlegend=False
        ))
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":40,"l":0,"b":0},
            title_z=0.9,
            height=600,
            coloraxis_colorbar=dict(title="Riqueza")
        )
        return fig
    except Exception as e:
        print(f"Error en mapa cartográfico: {e}")
        return None

def create_rai_chart(rai_df, top_n=200):
    """
    Crea gráfica de Índice de Abundancia Relativa
    
    Args:
        rai_df: DataFrame con RAI
        top_n: Número de especies a mostrar
    
    Returns:
        plotly figure
    """
    top_rai = rai_df.head(top_n)
    
    y_labels = [italics_scientific(name) for name in top_rai['Especie']]
    fig = go.Figure(data=[
        go.Bar(
            x=top_rai['RAI'],
            y=y_labels,
            orientation='h',
            marker=dict(
                color=top_rai['RAI'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="RAI")
            ),
            text=[f'{x:.2f}' for x in top_rai['RAI']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Índice de Abundancia Relativa (RAI) - Top {min(top_n, len(top_rai))}',
        xaxis_title='RAI (eventos por 100 días-trampa)',
        yaxis_title='Especie',
        height=max(400, len(top_rai) * 25),
        template='plotly_white',
        margin=dict(l=150, r=20, t=50, b=50),
        font=dict(size=11)
    )
    
    return fig


def create_accumulation_curve_plot(accumulation_df):
    """
    Crea gráfica de curva de acumulación de especies
    
    Args:
        accumulation_df: DataFrame con curva de acumulación
    
    Returns:
        plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=accumulation_df['Fecha'],
        y=accumulation_df['Especies_Acumuladas'],
        mode='lines+markers',
        name='Especies Acumuladas',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title='Curva de Acumulación de Especies',
        xaxis_title='Fecha',
        yaxis_title='Número de Especies Acumuladas',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_rarefaction_plot(rarefaction_df):
    """
    Crea gráfica de curva de rarefacción con intervalos de confianza
    
    Args:
        rarefaction_df: DataFrame con datos de rarefacción
    
    Returns:
        plotly figure
    """
    fig = go.Figure()
    
    # Curva principal
    fig.add_trace(go.Scatter(
        x=rarefaction_df['Sample_Size'],
        y=rarefaction_df['Mean_Species'],
        mode='lines',
        name='Especies Esperadas',
        line=dict(color='#1f77b4', width=3)
    ))
    
    # Intervalo de confianza
    fig.add_trace(go.Scatter(
        x=rarefaction_df['Sample_Size'].tolist() + rarefaction_df['Sample_Size'].tolist()[::-1],
        y=rarefaction_df['CI_Upper'].tolist() + rarefaction_df['CI_Lower'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(31, 119, 180, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='IC 95%',
        showlegend=True
    ))
    
    # Línea de asíntota (si se alcanza)
    max_species = rarefaction_df['Mean_Species'].max()
    last_10_pct = rarefaction_df.tail(int(len(rarefaction_df) * 0.1))
    species_gain = last_10_pct['Mean_Species'].iloc[-1] - last_10_pct['Mean_Species'].iloc[0]
    
    if species_gain / max_species < 0.05:  # Curva aplanada
        fig.add_hline(
            y=max_species,
            line_dash="dash",
            line_color="red",
            annotation_text="Asíntota alcanzada",
            annotation_position="right"
        )
    
    fig.update_layout(
        title='Curva de Rarefacción',
        xaxis_title='Tamaño de Muestra (individuos)',
        yaxis_title='Número de Especies',
        template='plotly_white',
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_occupancy_comparison_chart(occupancy_df, royle_nichols_results):
    """
    Crea gráfica comparativa de ocupación naive vs Royle-Nichols
    
    Args:
        occupancy_df: DataFrame con ocupación naive
        royle_nichols_results: Diccionario con resultados de Royle-Nichols
    
    Returns:
        plotly figure
    """
    # Preparar datos
    species_list = []
    naive_occ = []
    rn_occ = []
    
    for idx, row in occupancy_df.iterrows():
        species = row['Especie']
        species_list.append(species)
        naive_occ.append(row['Ocupacion_Naive'])
        
        # Obtener ocupación de Royle-Nichols si está disponible
        if species in royle_nichols_results and royle_nichols_results[species].get('success', False):
            rn_occ.append(royle_nichols_results[species]['psi'])
        else:
            rn_occ.append(None)
    
    # Crear gráfica
    fig = go.Figure()
    
    x_labels = [italics_scientific(name) for name in species_list]
    fig.add_trace(go.Bar(
        name='Ocupación Naive',
        x=x_labels,
        y=naive_occ,
        marker_color='lightblue',
        text=[f'{v:.2%}' for v in naive_occ],
        textposition='auto',
    ))
    
    # Solo agregar Royle-Nichols si hay datos
    valid_rn = [v for v in rn_occ if v is not None]
    if valid_rn:
        fig.add_trace(go.Bar(
            name='Ocupación Royle-Nichols (ψ)',
            x=x_labels,
            y=rn_occ,
            marker_color='darkblue',
            text=[f'{v:.2%}' if v is not None else 'N/A' for v in rn_occ],
            textposition='auto',
        ))
    
    fig.update_layout(
        title='Comparación de Ocupación: Naive vs Royle-Nichols',
        xaxis_title='Especie',
        yaxis_title='Probabilidad de Ocupación',
        yaxis=dict(tickformat='.0%', range=[0, 1]),
        barmode='group',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def create_lambda_bar_chart(royle_nichols_results, top_n=50):
    """
    Crea gráfica de barras de abundancia relativa (lambda) del modelo Royle-Nichols
    
    Args:
        royle_nichols_results: Diccionario con resultados de Royle-Nichols
        top_n: Número de especies a mostrar
    
    Returns:
        plotly figure
    """
    # Extraer datos de lambda
    lambda_data = []
    
    for species, results in royle_nichols_results.items():
        if results.get('success', False):
            lambda_data.append({
                'Especie': species,
                'Lambda': results['lambda'],
                'Psi': results['psi']
            })
    
    if not lambda_data:
        # Crear gráfica vacía con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de Royle-Nichols disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig
    
    lambda_df = pd.DataFrame(lambda_data).sort_values('Lambda', ascending=False).head(top_n)
    
    y_labels = [italics_scientific(name) for name in lambda_df['Especie']]
    fig = go.Figure(data=[
        go.Bar(
            x=lambda_df['Lambda'],
            y=y_labels,
            orientation='h',
            marker=dict(
                color=lambda_df['Lambda'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="lambda")
            ),
            text=[f'{x:.2f}' for x in lambda_df['Lambda']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Abundancia Relativa (lambda) - Modelo Royle-Nichols - Top {min(top_n, len(lambda_df))}',
        xaxis_title='Abundancia Relativa (lambda)',
        yaxis_title='Especie',
        height=max(400, len(lambda_df) * 30),
        template='plotly_white',
        font=dict(size=12)
    )
    
    return fig


def create_detection_probability_chart(royle_nichols_results, top_n=50):
    """
    Crea gráfica de probabilidades de detección del modelo Royle-Nichols
    
    Args:
        royle_nichols_results: Diccionario con resultados de Royle-Nichols
        top_n: Número de especies a mostrar
    
    Returns:
        plotly figure
    """
    # Extraer datos de probabilidad de detección
    detection_data = []
    
    for species, results in royle_nichols_results.items():
        if results.get('success', False):
            detection_data.append({
                'Especie': species,
                'P_detection': results['p_detection'],
                'Psi': results['psi']
            })
    
    if not detection_data:
        # Crear gráfica vacía con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de Royle-Nichols disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig
    
    detection_df = pd.DataFrame(detection_data).sort_values('P_detection', ascending=False).head(top_n)
    
    # Crear colores basados en nivel de detección
    colors = []
    for p in detection_df['P_detection']:
        if p >= 0.7:
            colors.append('#2ca02c')  # Verde - alta detección
        elif p >= 0.4:
            colors.append('#ff7f0e')  # Naranja - moderada
        else:
            colors.append('#d62728')  # Rojo - baja
    
    fig = go.Figure(data=[
        go.Bar(
            x=detection_df['P_detection'],
            y=detection_df['Especie'],
            orientation='h',
            marker=dict(color=colors),
            text=[f'{x:.2%}' for x in detection_df['P_detection']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Probabilidad de Detección (p) - Modelo Royle-Nichols - Top {min(top_n, len(detection_df))}',
        xaxis_title='Probabilidad de Detección (p)',
        yaxis_title='Especie',
        xaxis=dict(tickformat='.0%', range=[0, 1]),
        height=max(400, len(detection_df) * 30),
        template='plotly_white',
        font=dict(size=12)
    )
    
    # Agregar líneas de referencia
    fig.add_vline(x=0.7, line_dash="dash", line_color="green", 
                  annotation_text="Alta detección", annotation_position="top")
    fig.add_vline(x=0.4, line_dash="dash", line_color="orange", 
                  annotation_text="Moderada", annotation_position="top")
    
    return fig


def create_abundance_heatmap(df, species, bandwidth='auto', grid_resolution=100):
    """
    Crea mapa de abundancia relativa con interpolación KDE sobre imagen satelital
    
    Args:
        df: DataFrame con datos de cámaras trampa
        species: Nombre de la especie a analizar
        bandwidth: 'auto' o valor numérico para KDE
        grid_resolution: Resolución de la grilla de interpolación
    
    Returns:
        folium map con heatmap de abundancia
    """
    from modules.spatial_analysis import create_abundance_grid
    from utils.geospatial import utm_to_latlon
    import matplotlib.colors as mcolors
    
    # Generar grilla de abundancia
    grid_data = create_abundance_grid(df, species, grid_resolution, bandwidth)
    
    if grid_data is None:
        return None
    
    # Extraer datos
    grid_x = grid_data['grid_x']
    grid_y = grid_data['grid_y']
    grid_z = grid_data['grid_z']
    camera_data = grid_data['camera_data']
    
    # Obtener zona UTM de la primera cámara
    first_camera = df[df['Especie_Categoria'] == species].iloc[0]
    utm_zone = first_camera['Zona_UTM']
    zone_number = int(utm_zone[:-1])
    zone_letter = utm_zone[-1]
    
    # Convertir coordenadas de cámaras a lat/lon
    camera_coords = []
    for idx, row in camera_data.iterrows():
        lat, lon = utm_to_latlon(row['X'], row['Y'], zone_number, zone_letter)
        camera_coords.append({
            'lat': lat,
            'lon': lon,
            'camera': row['Camara'],
            'rai': row['RAI'],
            'events': row['Eventos'],
            'days': row['Dias_Muestreo']
        })
    
    # Calcular centro del mapa
    center_lat = np.mean([c['lat'] for c in camera_coords])
    center_lon = np.mean([c['lon'] for c in camera_coords])
    
    # Crear mapa base con tiles satelitales
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Añadir capa satelital de alta resolución
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite (Esri WorldImagery)',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Normalizar valores de abundancia para colormap
    z_max = np.max(grid_z)
    if z_max > 0:
        grid_z_norm = grid_z / z_max
    else:
        grid_z_norm = grid_z
    
    # Crear colormap personalizado (verde -> amarillo -> rojo)
    colors_list = ['#00FF00', '#7FFF00', '#FFFF00', '#FFD700', '#FFA500', '#FF4500', '#FF0000']
    n_bins = 100
    cmap = mcolors.LinearSegmentedColormap.from_list('abundance', colors_list, N=n_bins)
    
    # Convertir grilla UTM a lat/lon y crear polígonos
    from matplotlib.path import Path
    
    # Crear contornos de abundancia
    contour_levels = [0.1, 0.3, 0.5, 0.7, 0.9]  # Niveles relativos
    
    for level_idx, level in enumerate(contour_levels):
        # Crear máscara para este nivel
        mask = grid_z_norm >= level
        
        if not np.any(mask):
            continue
        
        # Obtener color para este nivel
        color = mcolors.rgb2hex(cmap(level))
        
        # Crear capa de polígonos para este nivel
        polygons = []
        
        # Simplificado: crear rectángulos para cada celda que supere el umbral
        step_x = (grid_x[0, 1] - grid_x[0, 0]) / 2
        step_y = (grid_y[1, 0] - grid_y[0, 0]) / 2
        
        for i in range(0, grid_x.shape[0], max(1, grid_resolution // 20)):  # Reducir densidad
            for j in range(0, grid_x.shape[1], max(1, grid_resolution // 20)):
                if mask[i, j]:
                    # Coordenadas de la celda en UTM
                    x_center = grid_x[i, j]
                    y_center = grid_y[i, j]
                    
                    # Convertir esquinas a lat/lon
                    corners_utm = [
                        (x_center - step_x, y_center - step_y),
                        (x_center + step_x, y_center - step_y),
                        (x_center + step_x, y_center + step_y),
                        (x_center - step_x, y_center + step_y)
                    ]
                    
                    corners_latlon = []
                    for x_utm, y_utm in corners_utm:
                        lat, lon = utm_to_latlon(x_utm, y_utm, zone_number, zone_letter)
                        corners_latlon.append([lat, lon])
                    
                    # Crear polígono
                    folium.Polygon(
                        locations=corners_latlon,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.4 - (level_idx * 0.05),  # Más transparente en niveles bajos
                        weight=0,
                        popup=f"RAI estimado: {grid_z[i, j]:.2f}"
                    ).add_to(m)
    
    # Computar métricas globales para la leyenda y colores
    min_rai = camera_data['RAI'].min() if not camera_data.empty else 0
    max_rai = camera_data['RAI'].max() if not camera_data.empty else 0
    avg_rai = camera_data['RAI'].mean() if not camera_data.empty else 0
    
    # Añadir marcadores de cámaras
    for cam in camera_coords:
        # Determinar color del marcador según RAI
        if max_rai > 0 and cam['rai'] >= max_rai * 0.7:
            marker_color = 'red'
        elif max_rai > 0 and cam['rai'] >= max_rai * 0.4:
            marker_color = 'orange'
        else:
            marker_color = 'green'
        
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 200px;">
            <b>Cámara:</b> {cam['camera']}<br>
            <b>Especie:</b> {species}<br>
            <b>RAI:</b> {cam['rai']:.2f} eventos/100 días-trampa<br>
            <b>Eventos:</b> {int(cam['events'])}<br>
            <b>Días de muestreo:</b> {int(cam['days'])}
        </div>
        """
        
        folium.CircleMarker(
            location=[cam['lat'], cam['lon']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{cam['camera']}: RAI={cam['rai']:.2f}",
            color='black',
            fillColor=marker_color,
            fillOpacity=0.9,
            weight=2
        ).add_to(m)
        
        # Añadir etiqueta de texto permanente al lado
        folium.Marker(
            location=[cam['lat'], cam['lon']],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 11pt; color: white; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; font-weight: bold; white-space: nowrap; transform: translate(12px, -12px);">{cam["camera"]}</div>'
            )
        ).add_to(m)
    
    # Añadir leyenda personalizada dinámica
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 260px; height: auto; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
        <p style="margin: 0; font-weight: bold; text-align: center;">
            Abundancia Relativa (RAI)
        </p>
        <p style="margin: 5px 0; font-size: 12px; text-align: center; color: #555;">
            {species}
        </p>
        <div style="background: linear-gradient(to right, #00FF00, #FFFF00, #FF0000); 
                    height: 20px; margin: 10px 0; border-radius: 3px;"></div>
        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold;">
            <span>Min: {min_rai:.2f}</span>
            <span>Max: {max_rai:.2f}</span>
        </div>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0; font-size: 11px;">
            <b>RAI Promedio:</b> {avg_rai:.2f}<br>
            <b>Esfuerzo (Cámaras):</b> {len(camera_data)}<br>
            <b>Cámaras con Éxito:</b> {len(camera_data[camera_data['Eventos'] > 0])}<br>
            <b>Eventos Totales:</b> {int(camera_data['Eventos'].sum())}<br>
            <br>
            <span style="color:red;">🔴 Alta (Hotspot)</span><br>
            <span style="color:orange;">🟠 Moderada</span><br>
            <span style="color:green;">🟢 Baja</span>
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Añadir control de capas
    folium.LayerControl().add_to(m)
    
    return m


def create_multi_species_abundance_comparison(df, species_list, bandwidth='auto'):
    """
    Genera comparación de mapas de abundancia para múltiples especies
    
    Args:
        df: DataFrame con datos de cámaras trampa
        species_list: Lista de especies a comparar
        bandwidth: 'auto' o valor numérico para KDE
    
    Returns:
        dict con mapas individuales por especie
    """
    abundance_maps = {}
    
    for species in species_list:
        map_obj = create_abundance_heatmap(df, species, bandwidth=bandwidth)
        if map_obj is not None:
            abundance_maps[species] = map_obj
    
    return abundance_maps


def fig_to_base64(fig):
    """
    Convierte figura matplotlib a base64 para embedding
    
    Args:
        fig: Figura matplotlib
    
    Returns:
        str: String base64
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def create_rai_by_site_bar_chart(rai_site_df, species):
    """
    Crea gráfica de barras de RAI por sitio para una especie
    
    Args:
        rai_site_df: DataFrame con columnas 'Sitio' y 'RAI'
        species: Nombre de la especie
        
    Returns:
        plotly figure
    """
    if rai_site_df is None or rai_site_df.empty:
        return None
        
    # Ordenar por RAI
    rai_site_df = rai_site_df.sort_values('RAI', ascending=False)
    
    # Usar 'Sitio' si existe, si no usar 'Camara'
    label_col = 'Sitio' if 'Sitio' in rai_site_df.columns else 'Camara'
    
    fig = go.Figure(data=[
        go.Bar(
            x=rai_site_df['RAI'],
            y=rai_site_df[label_col],
            orientation='h',
            marker=dict(
                color=rai_site_df['RAI'],
                colorscale='Greens',
                showscale=True,
                colorbar=dict(title="RAI")
            ),
            text=[f'{v:.2f}' for v in rai_site_df['RAI']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'RAI por Sitio: {italics_scientific(species)}',
        xaxis_title='RAI (eventos por 100 días-trampa)',
        yaxis_title='Sitio',
        height=max(400, len(rai_site_df) * 30),
        template='plotly_white',
        margin=dict(l=150, r=20, t=50, b=50),
        font=dict(size=11)
    )
    
    return fig
