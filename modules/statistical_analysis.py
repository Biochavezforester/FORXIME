"""
Módulo de análisis estadístico para FORXIME/2
Incluye índices de biodiversidad, análisis de ocupación y modelo Royle-Nichols
VERSIÓN 2.1 — Reforzado + Modelo de Ocupación Covariado
"""
import pandas as pd
import numpy as np
from scipy import stats, optimize
from scipy.special import expit
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import pairwise_distances
import warnings
import streamlit as st
warnings.filterwarnings('ignore')

# ─── COVARIABLES RECONOCIDAS AUTOMÁTICAMENTE ─────────────────────────────────
# Si alguna de estas columnas existe en el DataFrame, el modelo covariado se
# activará automáticamente en run_occupancy_analysis().
KNOWN_COVARIATES = [
    'Dist_Carretera_m',
    'Dist_Agua_m',
    'Altitud_m',
    'Pendiente_grados',
    'Cobertura_Vegetal_pct',
    'Dist_Poblado_m',
    'NDVI',
]

# ─────────────────────────────────────────────────────────────────────────────
# ÍNDICES DE BIODIVERSIDAD
# ─────────────────────────────────────────────────────────────────────────────

def calculate_shannon_index(abundance_data):
    """Shannon-Wiener H' = -sum(p_i * ln(p_i))"""
    try:
        abundance_data = np.array(abundance_data, dtype=float)
        abundance_data = abundance_data[abundance_data > 0]
        if len(abundance_data) == 0:
            return 0.0
        proportions = abundance_data / abundance_data.sum()
        return float(-np.sum(proportions * np.log(proportions)))
    except Exception:
        return 0.0


def calculate_simpson_index(abundance_data):
    """Simpson (1-D) unbiased: D = sum(n_i*(n_i-1)) / (N*(N-1))"""
    try:
        abundance_data = np.array(abundance_data, dtype=float)
        abundance_data = abundance_data[abundance_data > 0]
        if len(abundance_data) == 0:
            return 0.0
        n = abundance_data.sum()
        if n <= 1:
            return 0.0
        d = np.sum(abundance_data * (abundance_data - 1)) / (n * (n - 1))
        return float(1 - d)
    except Exception:
        return 0.0


def calculate_chao_shannon(abundance_data):
    """
    Estimador de Shannon corregido (Chao & Shen 2003).
    Ajusta el índice por especies no detectadas usando cobertura de muestra.
    """
    try:
        x = np.array(abundance_data, dtype=int)
        x = x[x > 0]
        n = x.sum()
        if n == 0: return 0.0
        
        # Cobertura de la muestra (Sample Coverage)
        f1 = np.sum(x == 1)
        f2 = np.sum(x == 2)
        if f2 > 0:
            chat = 1 - (f1 / n) * (((n - 1) * f1) / ((n - 1) * f1 + 2 * f2))
        else:
            chat = 1 - (f1 / n) * (((n - 1) * (f1 - 1)) / ((n - 1) * (f1 - 1) + 2)) if f1 > 0 else 1.0
        
        chat = max(chat, 0.01) # Evitar ceros
        
        # Ajuste de abundancias
        p_adj = (x / n) * chat
        shannon = -np.sum(p_adj * np.log(p_adj) / (1 - (1 - p_adj)**n))
        return float(max(shannon, 0.0))
    except Exception:
        return 0.0


def calculate_chao_simpson(abundance_data):
    """
    Estimador de Simpson corregido (Chao et al. 1997).
    """
    try:
        x = np.array(abundance_data, dtype=int)
        x = x[x > 0]
        n = x.sum()
        if n <= 1: return 0.0
        
        # Similitud corregida (MVUE)
        sum_n_sq = np.sum(x * (x - 1))
        if n*(n-1) == 0: return 0.0
        
        d_est = sum_n_sq / (n * (n - 1))
        return float(max(1 - d_est, 0.0))
    except Exception:
        return 0.0


def calculate_species_richness(species_list):
    """Riqueza de especies (S)."""
    try:
        return int(pd.Series(species_list).nunique())
    except Exception:
        return 0


def calculate_pielou_evenness(abundance_data):
    """Equitatividad de Pielou J' = H' / ln(S)"""
    try:
        abundance_data = np.array(abundance_data, dtype=float)
        shannon = calculate_shannon_index(abundance_data)
        richness = int((abundance_data > 0).sum())
        if richness <= 1:
            return 0.0
        return float(shannon / np.log(richness))
    except Exception:
        return 0.0


@st.cache_data(show_spinner=False)
def calculate_biodiversity_indices(df):
    """Calcula todos los índices de biodiversidad."""
    try:
        if df is None or df.empty:
            return {'Shannon': 0, 'Simpson': 0, 'Richness': 0,
                    'Pielou_Evenness': 0, 'Total_Individuals': 0,
                    'Chao_Shannon': 0, 'Chao_Simpson': 0}
        abundance = df.groupby('Especie_Categoria', observed=True)['Eventos_Independientes'].sum()

        vals = abundance.values
        return {
            'Shannon': calculate_shannon_index(vals),
            'Simpson': calculate_simpson_index(vals),
            'Richness': calculate_species_richness(df['Especie_Categoria']),
            'Pielou_Evenness': calculate_pielou_evenness(vals),
            'Total_Individuals': int(vals.sum()),
            'Chao_Shannon': calculate_chao_shannon(vals),
            'Chao_Simpson': calculate_chao_simpson(vals)
        }
    except Exception as e:
        return {'Shannon': 0, 'Simpson': 0, 'Richness': 0,
                'Pielou_Evenness': 0, 'Total_Individuals': 0, 
                'Chao_Shannon': 0, 'Chao_Simpson': 0, 'error': str(e)}


@st.cache_data(show_spinner=False)
def calculate_biodiversity_by_site(df):
    """Calcula índices de biodiversidad por sitio (Optimizado para grandes datasets)."""
    try:
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Obtener matriz de abundancia: Sitios (filas) x Especies (columnas)
        abundance_matrix = df.groupby([site_col, 'Especie_Categoria'], observed=True)['Eventos_Independientes'].sum().unstack(fill_value=0)

        
        # 1. Total Eventos y Riqueza (S)
        total_eventos = abundance_matrix.sum(axis=1)
        richness = (abundance_matrix > 0).sum(axis=1)
        
        # 2. Shannon (H')
        # p_i = n_i / N
        proportions = abundance_matrix.div(total_eventos, axis=0)
        # H = -sum(p * log(p))
        shannon = -(proportions * np.log(proportions.replace(0, np.nan))).sum(axis=1).fillna(0)
        
        # 3. Simpson (1-D) unbiased
        # D = sum(n*(n-1)) / (N*(N-1))
        n_sums = (abundance_matrix * (abundance_matrix - 1)).sum(axis=1)
        N_fact = total_eventos * (total_eventos - 1)
        simpson_d = n_sums / N_fact.replace(0, np.nan)
        simpson_index = (1 - simpson_d).fillna(0)
        
        # 4. Pielou (J')
        pielou = shannon / np.log(richness.replace(1, np.nan))
        pielou = pielou.fillna(0)

        # 5. Chao1 (Estimador de Riqueza para Singletons/Doubletons en abundancia)
        # Nota: calculate_chao_shannon y chao_simpson son más lentos de vectorizar fielmente 
        # pero podemos calcularlos eficientemente operando sobre las filas.
        results = []
        for site, vals_row in abundance_matrix.iterrows():
            vals = vals_row.values[vals_row.values > 0]
            site_name = site
            
            results.append({
                'Sitio': site_name,
                'Shannon': round(float(shannon[site]), 3),
                'Simpson': round(float(simpson_index[site]), 3),
                'Richness': int(richness[site]),
                'Pielou': round(float(pielou[site]), 3),
                'Chao_Shannon': round(calculate_chao_shannon(vals), 3),
                'Chao_Simpson': round(calculate_chao_simpson(vals), 3),
                'Total_Eventos': int(total_eventos[site]),
            })
            
        return pd.DataFrame(results)
    except Exception as e:
        print(f"Error en calculate_biodiversity_by_site: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# BRAY-CURTIS Y DENDROGRAMA
# ─────────────────────────────────────────────────────────────────────────────

def apply_hellinger_transformation(abundance_matrix):
    """
    Aplica la transformación de Hellinger: sqrt(p_i).
    Reduce el peso de especies dominantes, ideal para Bray-Curtis.
    """
    try:
        # Convertir a proporciones por sitio (filas)
        row_sums = abundance_matrix.sum(axis=1)
        # Evitar división por cero
        proportions = abundance_matrix.div(row_sums, axis=0).fillna(0)
        # Raíz cuadrada
        return np.sqrt(proportions)
    except Exception:
        return abundance_matrix

def calculate_bray_curtis_matrix(df, transform_hellinger=False):
    """Calcula matriz de disimilitud de Bray-Curtis."""
    try:
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        abundance_matrix = df.pivot_table(
            index=site_col, columns='Especie_Categoria',
            values='Eventos_Independientes', aggfunc='sum', fill_value=0)
        
        if transform_hellinger:
            data_to_dist = apply_hellinger_transformation(abundance_matrix).values
        else:
            data_to_dist = abundance_matrix.values
            
        dist_matrix = pairwise_distances(data_to_dist, metric='braycurtis')
        return dist_matrix, abundance_matrix.index.tolist()
    except Exception:
        return np.array([[0]]), ['Sitio_1']


@st.cache_data(show_spinner=False)
def create_bray_curtis_dendrogram(df, transform_hellinger=False):
    """Crea dendrograma de Bray-Curtis."""
    try:
        distance_matrix, site_names = calculate_bray_curtis_matrix(df, transform_hellinger)
        if len(site_names) < 2:
            return None
        condensed_dist = squareform(distance_matrix)
        linkage_matrix = linkage(condensed_dist, method='average')
        return {
            'linkage_matrix': linkage_matrix,
            'site_names': site_names,
            'distance_matrix': distance_matrix,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ÍNDICE DE ABUNDANCIA RELATIVA (RAI)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def calculate_relative_abundance_index(df):
    """RAI = (Eventos Independientes / Dias‑Trampa) × 100 (Optimizado)"""
    if df is None or df.empty:
        return pd.DataFrame(columns=['Especie', 'Eventos_Independientes', 'Dias_Trampa', 'RAI'])

    df = df.loc[:, ~df.columns.duplicated()]

    try:
        # VECTORIZADO: calcular min/max de Fecha por cámara sin apply+lambda
        df_dates = pd.to_datetime(df['Fecha'], errors='coerce')
        cam_trap = (
            df.assign(_fecha=df_dates)
            .groupby('Camara', observed=True)['_fecha']

            .agg(['min', 'max'])
        )
        cam_trap['dias'] = (cam_trap['max'] - cam_trap['min']).dt.days.fillna(0) + 1
        trap_nights = max(int(cam_trap['dias'].sum()), 1)
    except Exception:
        trap_nights = 1

    try:
        species_stats = df.groupby('Especie_Categoria', observed=True).agg(

            Eventos_Independientes=('Eventos_Independientes', 'sum'),
            Camara=('Camara', 'nunique')
        ).reset_index()
    except Exception:
        return pd.DataFrame(columns=['Especie', 'Eventos_Independientes', 'Dias_Trampa', 'RAI'])

    num_cameras = max(df['Camara'].nunique(), 1)
    avg_days = trap_nights / num_cameras
    species_stats['Dias_Trampa'] = (species_stats['Camara'] * avg_days).astype(int)
    species_stats['RAI'] = (species_stats['Eventos_Independientes'] / trap_nights) * 100

    return pd.DataFrame({
        'Especie': species_stats['Especie_Categoria'],
        'Eventos_Independientes': species_stats['Eventos_Independientes'],
        'Dias_Trampa': species_stats['Dias_Trampa'],
        'RAI': species_stats['RAI'],
    }).sort_values('RAI', ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS DE OCUPACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def calculate_naive_occupancy(df):
    """Ocupación Naive: psi = sitios_con_especie / total_sitios"""
    try:
        if df is None or df.empty:
            return pd.DataFrame(columns=['Especie', 'Sitios_Ocupados', 'Total_Sitios', 'Ocupacion_Naive'])
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        total_sites = df[site_col].nunique()
        if total_sites == 0:
            return pd.DataFrame(columns=['Especie', 'Sitios_Ocupados', 'Total_Sitios', 'Ocupacion_Naive'])
        occ = df.groupby('Especie_Categoria', observed=True)[site_col].nunique()

        return pd.DataFrame({
            'Especie': occ.index,
            'Sitios_Ocupados': occ.values,
            'Total_Sitios': total_sites,
            'Ocupacion_Naive': (occ.values / total_sites).round(3),
        }).sort_values('Ocupacion_Naive', ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=['Especie', 'Sitios_Ocupados', 'Total_Sitios', 'Ocupacion_Naive'])


def check_royle_nichols_assumptions(detection_history):
    """Verifica supuestos del modelo Royle-Nichols."""
    try:
        n_sites, n_occasions = detection_history.shape
        total_detections = int(detection_history.sum())
        warnings_list = []
        if n_sites < 10:
            warnings_list.append(f"Sitios ({n_sites}) < 10 recomendados")
        if n_occasions < 3:
            warnings_list.append(f"Ocasiones ({n_occasions}) < 3 recomendadas")
        if total_detections < 10:
            warnings_list.append(f"Pocas detecciones ({total_detections}). Modelo puede ser inestable.")
        meets = n_sites >= 10 and n_occasions >= 3 and total_detections >= 10
        return {
            'sufficient_sites': n_sites >= 10,
            'sufficient_occasions': n_occasions >= 3,
            'n_sites': n_sites,
            'n_occasions': n_occasions,
            'total_detections': total_detections,
            'meets_requirements': meets,
            'warnings': warnings_list,
        }
    except Exception as e:
        return {'meets_requirements': False, 'warnings': [str(e)], 'n_sites': 0, 'n_occasions': 0}


def estimate_royle_nichols_simple(detection_history, effective_area_ha=None, r_per_individual=0.15):
    """
    Modelo Royle-Nichols (método de momentos).
    Estima: psi (ocupación), lambda (abundancia local), p (prob. detección).
    Si effective_area_ha se proporciona, también estima la Densidad (ind/ha).
    Ref: Royle & Nichols 2003, Ecology 84(3):777-790.
    
    Args:
        detection_history: Matriz binaria (sitios x ocasiones)
        effective_area_ha: Área efectiva de muestreo (ha)
        r_per_individual: Probabilidad de detección de 1 individuo en 1 ocasión (parámetro r). 
                         Aumentar este valor reduce la sobreestimación en especies muy conspicuas (reses, venados).
    """
    try:
        assumptions = check_royle_nichols_assumptions(detection_history)
        if not assumptions['meets_requirements']:
            return {'success': False,
                    'message': 'No se cumplen supuestos del modelo',
                    'assumptions': assumptions}

        n_sites, n_occasions = detection_history.shape
        p_site = detection_history.sum(axis=1) / n_occasions
        psi_obs = float((p_site > 0).sum() / n_sites)
        p_mean = float(p_site[p_site > 0].mean()) if (p_site > 0).any() else 0.0

        # Estimación de lambda: p_site_i = 1 - (1-r)^lambda_i
        # Despejando: lambda = log(1 - p_site) / log(1 - r)
        r = r_per_individual
        
        # Evitar logaritmos de cero o negativos
        lambda_estimates = []
        for p in p_site[p_site > 0]:
            if 0 < p < 1.0:
                # Si r se acerca a p, lambda se acerca a 1.
                # Asegurar que r no sea mayor que p si p es muy bajo, o viceversa
                # r_eff = min(r, 0.99)
                val = np.log(1 - p) / np.log(1 - r)
                lambda_estimates.append(val)
            elif p >= 0.99:
                # Saturación: abundancia alta
                lambda_estimates.append(10.0) # Valor conservador de saturación

        # Descartar estimaciones irreales (> 100 individuos/punto) o negativas
        lambda_estimates = [l for l in lambda_estimates if l > 0 and l <= 100]
        lambda_mean = float(np.mean(lambda_estimates)) if lambda_estimates else 0.0

        
        result = {
            'success': True,
            'psi': round(psi_obs, 3),
            'lambda': round(lambda_mean, 3),
            'p_detection': round(p_mean, 3),
            'n_sites': n_sites,
            'n_occasions': n_occasions,
            'assumptions': assumptions,
            'method': 'Estimación Royle & Nichols (2003)',
            'note': 'Atención: Densidad RN usa área de visión. Para estimaciones territoriales, prefiera REM.',
        }
        
        if effective_area_ha is not None and effective_area_ha > 0:
            result['density'] = round(lambda_mean / effective_area_ha, 4)
            result['effective_area_ha'] = round(effective_area_ha, 4)
            
        return result
    except Exception as e:
        return {'success': False, 'message': str(e)}

def calculate_effective_area_ha(radius_m, angle_degrees):
    """
    Calcula el área efectiva de muestreo de una cámara trampa (en hectáreas).
    Asume un modelo de detección cónico/sector circular.
    
    Args:
        radius_m: Distancia máxima de detección en metros
        angle_degrees: Ángulo de visión de la cámara en grados
    """
    import math
    try:
        if radius_m <= 0 or angle_degrees <= 0:
            return 0.0
        # Área del sector circular = (Ángulo / 360) * π * r²
        area_m2 = (angle_degrees / 360.0) * math.pi * (radius_m ** 2)
        # Convertir a hectáreas (1 ha = 10,000 m2)
        return area_m2 / 10000.0
    except:
        return 0.0


def estimate_density_rem(events, trap_days, velocity_km_day, radius_m, angle_degrees):
    """
    Estima la densidad poblacional (Random Encounter Model - REM).
    Ideal para especies raras o con pocas recapturas.
    (Rowcliffe et al. 2008)
    
    Densidad = Y / (T * v * r * (2 + theta))
    """
    import math
    if trap_days <= 0 or velocity_km_day <= 0 or radius_m <= 0 or angle_degrees <= 0:
        return {'success': False, 'message': 'Parámetros inválidos para REM (>0 requeridos).'}
        
    try:
        radius_km = radius_m / 1000.0
        angle_radians = math.radians(angle_degrees)
        
        denominator = trap_days * velocity_km_day * radius_km * (2 + angle_radians)
        
        if denominator == 0:
            return {'success': False, 'message': 'El denominador de la fórmula es cero.'}
            
        density_km2 = events / denominator
        density_ha = density_km2 / 100.0  # Convertir km2 a hectáreas
        
        return {'success': True,
            'events': events,
            'trap_days': trap_days,
            'density_km2': round(density_km2, 4),
            'density_ha': round(density_ha, 4),
            'method': 'Random Encounter Model',
            'parameters': {'v': velocity_km_day, 'r': radius_m, 'theta': angle_degrees}
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}

def estimate_density_fmp(events, trap_days, velocity_km_day, radius_m, angle_degrees):
    """
    Estima la densidad poblacional usando el método Formozov-Malyshev-Pereleshin (FMP).
    Basado en encuentros de línea proyectados.
    
    Formula: D = (pi * Y) / (2 * v * T * w)
    donde w = 2 * r * sin(theta/2)
    """
    import math
    if trap_days <= 0 or velocity_km_day <= 0 or radius_m <= 0 or angle_degrees <= 0:
        return {'success': False, 'message': 'Parámetros inválidos para FMP.'}
        
    try:
        # Convertir a km
        radius_km = radius_m / 1000.0
        angle_radians = math.radians(angle_degrees)
        
        # Ancho de detección (cordal/arco proyectado)
        w_km = 2 * radius_km * math.sin(angle_radians / 2.0)
        
        if w_km == 0:
            return {'success': False, 'message': 'Ancho de detección es cero.'}
            
        # Densidad ind/km2
        density_km2 = (math.pi * events) / (2 * velocity_km_day * trap_days * w_km)
        density_ha = density_km2 / 100.0
        
        return {
            'success': True,
            'events': events,
            'trap_days': trap_days,
            'density_km2': round(density_km2, 4),
            'density_ha': round(density_ha, 4),
            'method': 'Formozov-Malyshev-Pereleshin (FMP)',
            'parameters': {'v': velocity_km_day, 'r': radius_m, 'theta': angle_degrees, 'w': w_km * 1000}
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}


def estimate_density_ste(df, species, viewshed_ha, snapshot_interval_min=60):
    """
    Estima la densidad poblacional usando el modelo Space-to-Event (STE).
    (Moeller et al. 2018)
    Optimizado para grandes volúmenes de datos (100k+ registros).
    """
    try:
        if df is None or df.empty or viewshed_ha <= 0:
            return {'success': False, 'message': 'Datos insuficientes o área inválida para STE.'}
            
        # 1. Preparar datos de la especie
        df_sp = df[df['Especie_Categoria'] == species].copy()
        
        # Asegurar DateTime
        if 'DateTime' not in df_sp.columns:
            if 'Fecha_Captura' in df_sp.columns:
                df_sp['DateTime'] = pd.to_datetime(df_sp['Fecha_Captura'], errors='coerce')
            elif 'Fecha' in df_sp.columns and 'Hora' in df_sp.columns:
                df_sp['DateTime'] = pd.to_datetime(df_sp['Fecha'].astype(str) + ' ' + df_sp['Hora'].astype(str), errors='coerce')
            else:
                return {'success': False, 'message': 'No se encontró columna de fecha/hora.'}
        
        df_sp = df_sp.dropna(subset=['DateTime'])
        
        # 2. Identificar sitios totales
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Camara'
        all_sites = df[site_col].unique()
        n_sites = len(all_sites)
        if n_sites == 0: return {'success': False, 'message': 'No hay sitios detectados.'}

        # 3. Definir rango temporal global (usar el del dataset completo o el de la especie)
        t_min = df['Fecha_Captura'].min() if 'Fecha_Captura' in df.columns else df_sp['DateTime'].min()
        t_max = df['Fecha_Captura'].max() if 'Fecha_Captura' in df.columns else df_sp['DateTime'].max()
        
        if pd.isna(t_min) or pd.isna(t_max):
            return {'success': False, 'message': 'Rango temporal no válido.'}

        # 4. Generar Snapshots teóricos
        total_seconds = (t_max - t_min).total_seconds()
        interval_seconds = snapshot_interval_min * 60
        n_snapshots = int(total_seconds // interval_seconds) + 1
        
        if n_snapshots < 2:
            return {'success': False, 'message': 'Rango temporal insuficiente.'}

        # 5. VECTORIZACIÓN: Asignar cada registro al snapshot más cercano
        # Window de detección (±5 min por defecto)
        window_sec = 300 # 5 min
        
        # Calcular a qué índice de snapshot pertenece cada registro
        # index = round((T - Tmin) / interval)
        diff_sec = (df_sp['DateTime'] - t_min).dt.total_seconds()
        snap_idx = (diff_sec / interval_seconds).round().astype(int)
        
        # Validar si cae dentro de la ventana de tiempo del snapshot
        snap_time_diff = np.abs(diff_sec - (snap_idx * interval_seconds))
        valid_mask = (snap_time_diff <= window_sec) & (snap_idx >= 0) & (snap_idx < n_snapshots)
        
        df_sp['snap_idx'] = snap_idx
        valid_detections = df_sp[valid_mask]
        
        # 6. Contar sitios únicos por snapshot usando groupby
        # Esto es órdenes de magnitud más rápido que filtrar en un loop
        if not valid_detections.empty:
            sites_per_snap = valid_detections.groupby('snap_idx', observed=True)[site_col].nunique()

            # Proporción de sitios detectados (K/N)
            p_per_snap = sites_per_snap / n_sites
            
            # Sumar todas las P detectadas y promediar con los snapshots vacíos
            p_sum = p_per_snap.sum()
            p_mean = p_sum / n_snapshots
        else:
            p_mean = 0.0

        # 7. Cálculo final
        p_constrained = min(max(p_mean, 1e-10), 0.999)
        density_ha = -np.log(1 - p_constrained) / viewshed_ha
        
        return {
            'success': True,
            'species': species,
            'density_ha': round(density_ha, 6),
            'p_instant': round(p_constrained, 6),
            'n_snapshots': n_snapshots,
            'hits': int(len(valid_detections)),
            'viewshed_ha': round(viewshed_ha, 6),
            'method': 'Space-To-Event (STE) Vectorizado'
        }
    except Exception as e:
        return {'success': False, 'message': f'Error en STE: {str(e)}'}

# ─── NUEVO: Modelo Covariado ──────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def calculate_covariate_occupancy(df, species, covariates=None):
    """
    Modelo de Ocupación con Covariables — Regresión Logística Ridge (L2) / Penalizada.

    MEJORAS ESTADÍSTICAS vs versión anterior:
      1. Regularización Ridge (penalización L2) para prevenir divergencia bajo separación completa.
      2. Selección automática de covariables por criterio EPV (Eventos Por Variable ≥ 10).
      3. Diagnóstico de separación y calidad de ajuste.
      4. Odds Ratio acotado para evitar valores astronómicos.
      5. Señales claras de no-confiabilidad del modelo.

    Args:
        df:          DataFrame con columnas de covariables por sitio/cámara.
        species:     Nombre de la especie.
        covariates:  Lista de columnas a usar. Si None, se detectan de KNOWN_COVARIATES.

    Returns:
        dict con coef_table (DataFrame), site_predictions, AIC e interpretaciones.
    """
    try:
        import traceback
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'

        # ── 1. Detectar covariables disponibles ──────────────────────────────
        if covariates is None:
            covariates = [c for c in KNOWN_COVARIATES if c in df.columns and df[c].notna().any()]

        if not covariates:
            return {
                'success': False,
                'message': (
                    'No hay covariables con datos en el dataset. Añade columnas como: '
                    + ', '.join(KNOWN_COVARIATES)
                ),
                'covariates_used': [],
            }

        # ── 2. Tabla sitio x covariable (mediana — robusta a outliers) ───────
        site_cov = df.groupby(site_col, observed=True)[covariates].median().reset_index()
        occupied = set(df[df['Especie_Categoria'] == species][site_col].unique())
        site_cov['Presencia'] = site_cov[site_col].isin(occupied).astype(int)
        site_cov = site_cov.dropna(subset=covariates)

        n_sites   = len(site_cov)
        n_pos     = int(site_cov['Presencia'].sum())
        n_neg     = n_sites - n_pos

        if n_sites < 5:
            return {
                'success': False,
                'message': f'Mínimo 5 sitios con datos completos (hay {n_sites}).',
                'covariates_used': covariates,
            }

        # ── 3. Diagnóstico de separación ─────────────────────────────────────
        separation_warnings = []
        if n_pos == 0 or n_neg == 0:
            return {
                'success': False,
                'message': (
                    f'Separación perfecta: {"todas" if n_pos == n_sites else "ninguna"} '
                    f'las cámaras tienen presencia de {species}. '
                    'El modelo logístico no puede estimar probabilidades intermedias.'
                ),
                'covariates_used': covariates,
            }

        pct_occ = n_pos / n_sites
        if pct_occ >= 0.85 or pct_occ <= 0.15:
            separation_warnings.append(
                f'⚠️ Cuasi-separación: {n_pos}/{n_sites} sitios ocupados ({pct_occ:.0%}). '
                'El modelo puede seguir siendo inestable incluso con regularización.'
            )

        # ── 4. Selección por EPV (Eventos Por Variable) ───────────────────────
        # EPV = min(n_pos, n_neg) / n_covariables ≥ 10 recomendado
        # Si EPV < 5, reducimos automáticamente
        n_events = min(n_pos, n_neg)
        max_covs  = max(1, n_events // 5)    # EPV ≥ 5 (conservador)
        epv_warning = None
        if len(covariates) > max_covs:
            epv_warning = (
                f'⚠️ Sobreparametrización: {n_events} eventos minoritarios / '
                f'{len(covariates)} variables → EPV={n_events/len(covariates):.1f}. '
                f'Se usarán solo las {max_covs} más informativas (por varianza).'
            )
            # Seleccionar las covariables con mayor varianza (las más informativas)
            variances = site_cov[covariates].astype(float).var()
            covariates = variances.nlargest(max_covs).index.tolist()

        # ── 5. Preparar matrices ─────────────────────────────────────────────
        X = site_cov[covariates].values.astype(float)
        y = site_cov['Presencia'].values.astype(float)

        # Estandarización Z-score (necesaria para que el ridge sea ecuánime)
        X_means = X.mean(axis=0)
        X_stds  = X.std(axis=0)
        X_stds[X_stds == 0] = 1.0
        Xs = (X - X_means) / X_stds

        # Diseño con intercepto
        Xd = np.hstack([np.ones((Xs.shape[0], 1)), Xs])
        param_names = ['Intercepto'] + covariates

        # ── 6. Regularización Ridge (L2) ─────────────────────────────────────
        # lambda de regularización: mayor → más suave, menos divergencia
        # Escala automática: lambda = (n_sites / n_events) — más conservador con menos eventos
        ridge_lambda = max(1.0, n_sites / max(n_events, 1))

        def penalized_nll(beta):
            """Neg-log-verosimilitud + penalización Ridge (NO penaliza el intercepto)."""
            prob = expit(np.clip(Xd @ beta, -20, 20))
            prob = np.clip(prob, 1e-8, 1 - 1e-8)
            nll  = -float(np.sum(y * np.log(prob) + (1 - y) * np.log(1 - prob)))
            # Penalización L2 (solo over β[1:], no sobre el intercepto)
            ridge = (ridge_lambda / 2.0) * float(np.sum(beta[1:] ** 2))
            return nll + ridge

        result = optimize.minimize(
            penalized_nll,
            np.zeros(Xd.shape[1]),
            method='BFGS',
            options={'maxiter': 2000, 'gtol': 1e-6}
        )
        beta_hat = result.x

        # ── 7. Errores estándar y estadísticos ───────────────────────────────
        try:
            H_inv = np.array(result.hess_inv)
            se = np.sqrt(np.maximum(np.diag(H_inv), 0))
        except Exception:
            se = np.full_like(beta_hat, np.nan)

        z_vals = np.where(se > 0, beta_hat / se, 0.0)
        p_vals = 2 * (1 - stats.norm.cdf(np.abs(z_vals)))

        # OR acotado a [-20, 20] en escala log para evitar display absurdo
        beta_for_OR = np.clip(beta_hat, -20, 20)
        OR = np.exp(beta_for_OR)

        # ── 8. AIC penalizado ─────────────────────────────────────────────────
        # Usamos la log-verosimilitud sin penalización para el AIC
        prob_fitted = expit(Xd @ beta_hat)
        prob_fitted = np.clip(prob_fitted, 1e-8, 1 - 1e-8)
        ll_unpen = float(np.sum(y * np.log(prob_fitted) + (1 - y) * np.log(1 - prob_fitted)))
        k   = len(beta_hat)
        aic = round(2 * k - 2 * ll_unpen, 2)

        # ── 9. Diagnósticos de convergencia ──────────────────────────────────
        convergence_warnings = separation_warnings[:]
        if epv_warning:
            convergence_warnings.append(epv_warning)

        # Detectar si los coeficientes divergieron a pesar de la regularización
        if np.any(np.abs(beta_hat) > 15):
            convergence_warnings.append(
                '⚠️ Coeficientes excesivamente grandes (separación residual). '
                'Interpreta los OR y p-valores con cautela extrema.'
            )
        if not result.success:
            convergence_warnings.append(
                f'⚠️ Optimizador no convergió ({result.message}). '
                'Los estimadores pueden ser inestables.'
            )
        # p-valores todos cercanos a 1 → claro síntoma de separación
        if np.all(p_vals > 0.9):
            convergence_warnings.append(
                '⚠️ Todos los p-valores ≈ 1.0: señal de separación completa residual. '
                'El modelo no es confiable para esta especie con los datos actuales.'
            )

        # ── 10. Predicciones por sitio ────────────────────────────────────────
        psi_pred = expit(Xd @ beta_hat)
        site_cov = site_cov.copy()
        site_cov['Psi_Predicha']  = psi_pred.round(3)
        site_cov['Presencia_Obs'] = y.astype(int)

        # ── 11. Tabla de coeficientes ─────────────────────────────────────────
        OR_display = OR.round(3)
        coef_table = pd.DataFrame({
            'Covariable':    param_names,
            'Beta':          beta_hat.round(3),
            'SE':            se.round(3),
            'z':             z_vals.round(2),
            'p_valor':       p_vals.round(4),
            'Odds_Ratio':    OR_display,
            'Significativo': (p_vals < 0.05).tolist(),
        })

        # ── 12. Interpretación automática ─────────────────────────────────────
        interpretations = []
        for _, row in coef_table[coef_table['Covariable'] != 'Intercepto'].iterrows():
            sig  = "✅" if row['Significativo'] else "⚪"
            interpretations.append(
                f"{sig} **{row['Covariable']}** (β={row['Beta']}, OR={row['Odds_Ratio']}, p={row['p_valor']}): "
                f"A mayor {row['Covariable'].replace('_', ' ').lower()}, "
                f"{'favorece' if row['Beta'] > 0 else 'reduce'} la ocupación de *{species}*."
            )

        return {
            'success':             True,
            'species':             species,
            'covariates_used':     covariates,
            'n_sites':             int(n_sites),
            'n_occupied':          n_pos,
            'aic':                 aic,
            'coef_table':          coef_table,
            'site_predictions':    site_cov[[site_col, 'Presencia_Obs', 'Psi_Predicha']],
            'interpretations':     interpretations,
            'warnings':            convergence_warnings,
            'ridge_lambda':        round(ridge_lambda, 3),
            'method':              f'Regresión Logística Ridge (lambda={ridge_lambda:.2f}) con Z-score',
            'note': (
                'β positivo = covariable favorece presencia. '
                'OR > 1 = mayor probabilidad de ocupación por unidad estandarizada. '
                f'Ridge lambda={ridge_lambda:.2f} aplicado para estabilizar estimación.'
            ),
        }

    except Exception as e:
        return {
            'success':         False,
            'message':         f'Error en modelo covariado: {str(e)}',
            'traceback':       traceback.format_exc(),
            'covariates_used': covariates or [],
        }


# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def run_occupancy_analysis(df, period_days=7, effective_area_ha=None, rn_r_probs=None):
    """
    Análisis completo de ocupación:
    1. Ocupación Naive (siempre)
    2. Royle-Nichols (si hay suficientes datos) con periodo dinámico y densidad opcional.
    3. Modelo Covariado (automático si existen columnas de covariables)
    """
    results = {}
    if df is None or df.empty:
        return results

    # Filtrar categorías no-faunísticas antes de cualquier análisis
    _EXCLUDE = {'vacío', 'vacio', 'vacía', 'vacia', 'humano', 'human',
                'vehículo', 'vehiculo', 'vehicle', 'desconocido', 'unknown', 'empty'}
    df = df[~df['Especie_Categoria'].str.strip().str.lower().isin(_EXCLUDE)].copy()
    if df.empty:
        return results

    # 1. Ocupación Naive
    results['naive_occupancy'] = calculate_naive_occupancy(df)

    # 2. Royle-Nichols
    try:
        from modules.data_processing import prepare_detection_history
        detection_histories = prepare_detection_history(df, period_days)
        results['royle_nichols'] = {}
        for species, history_data in detection_histories.items():
            binary_history = history_data['binary'].values
            # Obtener r específico si existe
            sp_r = rn_r_probs.get(species, 0.15) if rn_r_probs else 0.15
            results['royle_nichols'][species] = estimate_royle_nichols_simple(
                binary_history, 
                effective_area_ha,
                r_per_individual=sp_r
            )
    except Exception as e:
        results['royle_nichols'] = {'error': str(e)}

    # 3. Modelo Covariado (automático)
    available_covs = [c for c in KNOWN_COVARIATES if c in df.columns]
    if available_covs:
        results['covariate_occupancy'] = {}
        for sp in df['Especie_Categoria'].unique():
            results['covariate_occupancy'][sp] = calculate_covariate_occupancy(
                df, sp, available_covs)
    else:
        results['covariate_occupancy'] = {}
        results['covariate_occupancy_note'] = (
            'No se detectaron covariables. Añade columnas como: '
            + ', '.join(KNOWN_COVARIATES)
        )

    return results


# ─────────────────────────────────────────────────────────────────────────────
# CURVAS DE ACUMULACIÓN Y RAREFACCIÓN
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def calculate_species_accumulation_curve(df):
    """Curva acumulada de especies (Optimizado para grandes datasets)."""
    try:
        if df is None or df.empty:
            return pd.DataFrame({'Fecha': [], 'Especies_Acumuladas': []})
            
        df = df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])
        
        # 1. Encontrar la primera detección de cada especie
        first_detections = df.sort_values('Fecha').drop_duplicates('Especie_Categoria', keep='first')
        
        # 2. Contar cuántas nuevas especies aparecen cada día
        new_species_per_date = first_detections.groupby('Fecha').size().reset_index(name='Nuevas')
        
        # 3. Obtener todos los días del dataset para rellenar la curva
        all_dates = pd.DataFrame({'Fecha': sorted(df['Fecha'].unique())})
        
        # 4. Combinar y calcular suma acumulada
        curve = pd.merge(all_dates, new_species_per_date, on='Fecha', how='left').fillna(0)
        curve['Especies_Acumuladas'] = curve['Nuevas'].cumsum().astype(int)
        
        return curve[['Fecha', 'Especies_Acumuladas']]
    except Exception as e:
        print(f"Error en curva de acumulación: {e}")
        return pd.DataFrame({'Fecha': [], 'Especies_Acumuladas': []})


def calculate_co_occurrence_matrix(df):
    """Matriz de co-ocurrencia de especies por sitio."""
    try:
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        presence = df.pivot_table(
            index=site_col, columns='Especie_Categoria',
            values='Eventos_Independientes', aggfunc='sum', fill_value=0)
        return (presence > 0).astype(int).T.dot((presence > 0).astype(int))
    except Exception:
        return pd.DataFrame()


def calculate_rarefaction_curve(df, method='individual', n_iterations=50):
    """Curva de rarefacción con IC 95% via bootstrap (50 iteraciones, optimizado)."""
    try:
        if method == 'individual':
            individuals = []
            for _, row in df.iterrows():
                individuals.extend([row['Especie_Categoria']] * int(max(row['Eventos_Independientes'], 0)))
            individuals = np.array(individuals)
            if len(individuals) < 2:
                return pd.DataFrame()
            sample_sizes = np.unique(np.linspace(1, len(individuals), min(40, len(individuals))).astype(int))
            rows = []
            for ss in sample_sizes:
                counts = [
                    len(np.unique(np.random.choice(individuals, size=ss, replace=False)))
                    for _ in range(n_iterations)
                ]
                rows.append({'Sample_Size': ss, 'Mean_Species': np.mean(counts),
                             'SD': np.std(counts),
                             'CI_Lower': np.percentile(counts, 2.5),
                             'CI_Upper': np.percentile(counts, 97.5)})
            return pd.DataFrame(rows)
        else:
            df_c = df.copy()
            df_c['Fecha'] = pd.to_datetime(df_c['Fecha'], errors='coerce')
            unique_dates = df_c['Fecha'].dropna().unique()
            if len(unique_dates) < 2:
                return pd.DataFrame()
            sample_sizes = np.unique(np.linspace(1, len(unique_dates), min(25, len(unique_dates))).astype(int))
            rows = []
            for ss in sample_sizes:
                counts = [
                    df_c[df_c['Fecha'].isin(np.random.choice(unique_dates, size=ss, replace=False))][
                        'Especie_Categoria'].nunique()
                    for _ in range(n_iterations)
                ]
                rows.append({'Sample_Size': ss, 'Mean_Species': np.mean(counts),
                             'SD': np.std(counts),
                             'CI_Lower': np.percentile(counts, 2.5),
                             'CI_Upper': np.percentile(counts, 97.5)})
            return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def estimate_sampling_completeness(df, method='chao1'):
    """Completitud del muestreo: Chao1 (abundancia) o Chao2 (incidencia)."""
    try:
        observed = df['Especie_Categoria'].nunique()
        counts   = df.groupby('Especie_Categoria', observed=True)['Eventos_Independientes'].sum()

        q1 = int((counts == 1).sum())   # singletons
        q2 = int((counts == 2).sum())   # doubletons

        if method == 'chao2':
            site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
            by_site  = df.groupby('Especie_Categoria', observed=True)[site_col].nunique()

            u1 = int((by_site == 1).sum())
            u2 = int((by_site == 2).sum())
            estimated = (observed + u1**2 / (2 * u2)) if u2 > 0 else observed + u1 * (u1 - 1) / 2
        else:  # chao1
            estimated = (observed + q1**2 / (2 * q2)) if q2 > 0 else observed + q1 * (q1 - 1) / 2

        completeness = min((observed / estimated) * 100, 100.0) if estimated > 0 else 100.0

        if completeness >= 90:
            status, rec = "Excelente", "El muestreo ha capturado la mayoría de las especies presentes."
        elif completeness >= 75:
            status, rec = "Bueno", "El muestreo es adecuado; podrían detectarse algunas especies adicionales."
        elif completeness >= 60:
            status, rec = "Moderado", "Se recomienda extender el muestreo."
        else:
            status, rec = "Insuficiente", "El muestreo es insuficiente. Se requiere mayor esfuerzo."

        return {
            'observed_richness':     int(observed),
            'estimated_richness':    round(float(estimated), 1),
            'completeness_percent':  round(completeness, 1),
            'status':                status,
            'recommendation':        rec,
            'singletons':            q1,
            'doubletons':            q2,
            'method':                method.upper(),
        }
    except Exception as e:
        return {
            'observed_richness': 0, 'estimated_richness': 0,
            'completeness_percent': 0, 'status': 'Error',
            'recommendation': str(e), 'singletons': 0,
            'doubletons': 0, 'method': method.upper(),
        }


# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def run_spatial_occupancy_analysis(df, period_days=7, buffer_m=1000, rn_r_probs=None):
    """
    Ejecuta el modelo Spatial Royle-Nichols usando conteos para mayor precisión.
    """
    results = {}
    if 'Coordenada_X_UTM' not in df.columns or 'Coordenada_Y_UTM' not in df.columns:
        return {'success': False, 'message': 'No hay coordenadas UTM disponibles para el modelo espacial.'}
    
    try:
        from modules.data_processing import prepare_detection_history
        from modules.spatial_models import estimate_spatial_royle_nichols
        
        # Identificar la columna de agrupación
        site_col = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
        
        det_histories = prepare_detection_history(df, period_days)
        
        # Coordenadas maestras (todos los sitios)
        coords_df = df.groupby(site_col, observed=True).agg({

            'Coordenada_X_UTM': 'first',
            'Coordenada_Y_UTM': 'first'
        }).sort_index()
        
        all_sites = coords_df.index.tolist()
        species_coords = coords_df.values
        
        for species, history_data in det_histories.items():
            # USAR CONTEOS EN LUGAR DE BINARIO
            counts_df = history_data['counts']
            aligned_counts = counts_df.reindex(all_sites, fill_value=0).values
            
            # Obtener r calibrado si existe
            sp_r = rn_r_probs.get(species, 0.15) if rn_r_probs else 0.15
            
            results[species] = estimate_spatial_royle_nichols(
                aligned_counts, 
                species_coords, 
                buffer_m=buffer_m,
                p0_fixed=sp_r
            )
            
        return {'success': True, 'species_results': results}
        
    except Exception as e:
        import traceback
        return {'success': False, 'message': str(e), 'traceback': traceback.format_exc()}
