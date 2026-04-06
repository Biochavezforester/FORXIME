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
# Imports pesados movidos dentro de las funciones (Lazy Loading)
import io
import base64


def create_abundance_bar_chart(df, top_n=None):
    """
    Crea gráfica de barras de abundancia por especie
    
    Args:
        df: DataFrame con datos
        top_n: Número de especies a mostrar (None para mostrar todas)
    
    Returns:
        plotly figure
    """
    abundance = df.groupby('Especie_Categoria')['Eventos_Independientes'].sum().sort_values(ascending=False)
    
    if top_n is not None:
        top_species = abundance.head(top_n)
    else:
        top_species = abundance
    
    fig = go.Figure(data=[
        go.Bar(
            x=top_species.values,
            y=top_species.index,
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
        title=f'Abundancia de Especies' + (f' (Top {top_n})' if top_n else ''),
        xaxis_title='Número de Eventos Independientes',
        yaxis_title='Especie',
        height=max(400, len(top_species) * 30),
        template='plotly_white',
        font=dict(size=12)
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
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram
    fig, ax = plt.subplots(figsize=(12, 6))
    
    dendrogram(
        linkage_matrix,
        labels=site_names,
        ax=ax,
        color_threshold=0.7,
        above_threshold_color='gray'
    )
    
    ax.set_title('Dendrograma de Similitud de Bray-Curtis', fontsize=14, fontweight='bold')
    ax.set_xlabel('Sitios', fontsize=12)
    ax.set_ylabel('Distancia de Bray-Curtis', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig


def create_activity_pattern_plot(activity_data):
    """
    Crea gráfica radial de patrón de actividad
    
    Args:
        activity_data: Diccionario con datos de actividad
    
    Returns:
        plotly figure
    """
    grid_hours = activity_data['grid_hours']
    density = activity_data['density']
    species = activity_data['species']
    
    # Convertir horas a ángulos (0-360 grados)
    theta = (grid_hours / 24) * 360
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=density,
        theta=theta,
        fill='toself',
        name=species,
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Agregar marcadores para períodos del día
    fig.add_trace(go.Scatterpolar(
        r=[0, max(density)],
        theta=[0, 0],
        mode='lines',
        line=dict(color='orange', width=1, dash='dash'),
        name='Amanecer (6:00)',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[0, max(density)],
        theta=[180, 180],
        mode='lines',
        line=dict(color='red', width=1, dash='dash'),
        name='Atardecer (18:00)',
        showlegend=True
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(density) * 1.1]),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 90, 180, 270],
                ticktext=['0:00', '6:00', '12:00', '18:00'],
                direction='clockwise'
            )
        ),
        title=f'Patrón de Actividad: {species}<br>Clasificación: {activity_data["pattern"]}',
        showlegend=True,
        height=500
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
    
    # Especie 1
    theta1 = (pattern1['grid_hours'] / 24) * 360
    fig.add_trace(go.Scatterpolar(
        r=pattern1['density'],
        theta=theta1,
        fill='toself',
        name=sp1,
        line=dict(color='#1f77b4', width=2),
        opacity=0.6
    ))
    
    # Especie 2
    theta2 = (pattern2['grid_hours'] / 24) * 360
    fig.add_trace(go.Scatterpolar(
        r=pattern2['density'],
        theta=theta2,
        fill='toself',
        name=sp2,
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
        title=f'Solapamiento Temporal: {sp1} vs {sp2}<br>' +
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


def create_rai_chart(rai_df, top_n=None):
    """
    Crea gráfica de Índice de Abundancia Relativa
    
    Args:
        rai_df: DataFrame con RAI
        top_n: Número de especies a mostrar (None para todas)
    
    Returns:
        plotly figure
    """
    if top_n is not None:
        top_rai = rai_df.head(top_n)
    else:
        top_rai = rai_df
    
    fig = go.Figure(data=[
        go.Bar(
            x=top_rai['RAI'],
            y=top_rai['Especie'],
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
        title=f'Índice de Abundancia Relativa (RAI)' + (f' - Top {top_n}' if top_n else ''),
        xaxis_title='RAI (eventos por 100 días-trampa)',
        yaxis_title='Especie',
        height=max(400, len(top_rai) * 30),
        template='plotly_white'
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
    
    fig.add_trace(go.Bar(
        name='Ocupación Naive',
        x=species_list,
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
            x=species_list,
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


def create_lambda_bar_chart(royle_nichols_results, top_n=None):
    """
    Crea gráfica de barras de abundancia relativa (λ) del modelo Royle-Nichols
    
    Args:
        royle_nichols_results: Diccionario con resultados de Royle-Nichols
        top_n: Número de especies a mostrar (None para todas)
    
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
    
    if top_n is not None:
        lambda_df = pd.DataFrame(lambda_data).sort_values('Lambda', ascending=False).head(top_n)
    else:
        lambda_df = pd.DataFrame(lambda_data).sort_values('Lambda', ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            x=lambda_df['Lambda'],
            y=lambda_df['Especie'],
            orientation='h',
            marker=dict(
                color=lambda_df['Lambda'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="λ")
            ),
            text=[f'{x:.2f}' for x in lambda_df['Lambda']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Abundancia Relativa (λ) - Modelo Royle-Nichols' + (f' - Top {len(lambda_df)}' if top_n else ''),
        xaxis_title='Abundancia Relativa (λ)',
        yaxis_title='Especie',
        height=max(400, len(lambda_df) * 30),
        template='plotly_white',
        font=dict(size=12)
    )
    
    return fig


def create_detection_probability_chart(royle_nichols_results, top_n=None):
    """
    Crea gráfica de probabilidades de detección del modelo Royle-Nichols
    
    Args:
        royle_nichols_results: Diccionario con resultados de Royle-Nichols
        top_n: Número de especies a mostrar (None para todas)
    
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
    
    if top_n is not None:
        detection_df = pd.DataFrame(detection_data).sort_values('P_detection', ascending=False).head(top_n)
    else:
        detection_df = pd.DataFrame(detection_data).sort_values('P_detection', ascending=False)
    
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
        title=f'Probabilidad de Detección (p) - Modelo Royle-Nichols' + (f' - Top {len(detection_df)}' if top_n else ''),
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
    
    # Añadir marcadores de cámaras
    for cam in camera_coords:
        # Determinar color del marcador según RAI
        if cam['rai'] >= z_max * 0.7:
            marker_color = 'red'
        elif cam['rai'] >= z_max * 0.4:
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
            color='white',
            fillColor=marker_color,
            fillOpacity=0.9,
            weight=2
        ).add_to(m)
    
    # Añadir leyenda personalizada
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 220px; height: auto; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <p style="margin: 0; font-weight: bold; text-align: center;">
            Tasa de detección del {species.split()[-1] if ' ' in species else species}
        </p>
        <p style="margin: 5px 0; font-size: 11px; text-align: center;">
            (RAI: 0.88 registros/100 trampas-día)
        </p>
        <div style="background: linear-gradient(to right, #00FF00, #FFFF00, #FF0000); 
                    height: 20px; margin: 10px 0; border-radius: 3px;"></div>
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
            <span>Bajo: 0.66</span>
            <span style="text-align: right;">Alto: 7.66</span>
        </div>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0; font-size: 11px;">
            <b>RAI Promedio:</b> {camera_data['RAI'].mean():.2f}<br>
            <b>RAI Máximo:</b> {camera_data['RAI'].max():.2f}<br>
            <b>Cámaras:</b> {len(camera_data)}
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
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64
