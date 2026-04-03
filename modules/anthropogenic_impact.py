"""
Módulo de análisis de impacto antropogénico para FORXIME/2
"""
import pandas as pd
import numpy as np
from modules.data_processing import identify_non_wildlife, categorize_anthropogenic


def calculate_anthropogenic_impact(df):
    """
    Calcula métricas de impacto antropogénico
    
    Args:
        df: DataFrame con todos los datos
    
    Returns:
        dict: Métricas de impacto antropogénico
    """
    # Identificar registros no-fauna
    non_wildlife = identify_non_wildlife(df)
    
    total_records = len(df)
    anthropogenic_records = len(non_wildlife)
    
    # Porcentaje de registros antropogénicos
    anthropogenic_pct = (anthropogenic_records / total_records * 100) if total_records > 0 else 0
    
    # Categorizar registros antropogénicos
    if len(non_wildlife) > 0:
        anthropogenic_by_category = non_wildlife.groupby('Categoria_Antropogenica').size()
    else:
        anthropogenic_by_category = pd.Series()
    
    results = {
        'total_records': total_records,
        'anthropogenic_records': anthropogenic_records,
        'wildlife_records': total_records - anthropogenic_records,
        'anthropogenic_percentage': anthropogenic_pct,
        'by_category': anthropogenic_by_category.to_dict() if len(anthropogenic_by_category) > 0 else {},
        'non_wildlife_df': non_wildlife
    }
    
    return results


def calculate_impact_by_site(df):
    """
    Calcula impacto antropogénico por sitio
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Impacto por sitio
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    non_wildlife = identify_non_wildlife(df)
    
    # Total de registros por sitio
    total_by_site = df.groupby(site_column).size()
    
    # Registros antropogénicos por sitio
    if len(non_wildlife) > 0:
        anthro_by_site = non_wildlife.groupby(site_column).size()
    else:
        anthro_by_site = pd.Series()
    
    # Crear DataFrame de resultados
    impact_df = pd.DataFrame({
        'Sitio': total_by_site.index,
        'Total_Registros': total_by_site.values
    })
    
    impact_df['Registros_Antropogenicos'] = impact_df['Sitio'].map(anthro_by_site).fillna(0).astype(int)
    impact_df['Porcentaje_Antropogenico'] = (impact_df['Registros_Antropogenicos'] / 
                                              impact_df['Total_Registros'] * 100)
    
    # Clasificar nivel de impacto
    def classify_impact(pct):
        if pct < 5:
            return 'Bajo'
        elif pct < 15:
            return 'Moderado'
        elif pct < 30:
            return 'Alto'
        else:
            return 'Muy Alto'
    
    impact_df['Nivel_Impacto'] = impact_df['Porcentaje_Antropogenico'].apply(classify_impact)
    
    return impact_df.sort_values('Porcentaje_Antropogenico', ascending=False)


def analyze_wildlife_anthropogenic_correlation(df):
    """
    Analiza correlación entre presencia antropogénica y fauna silvestre
    
    Args:
        df: DataFrame con datos
    
    Returns:
        dict: Análisis de correlación
    """
    from scipy.stats import spearmanr
    
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    # Separar fauna y no-fauna
    non_wildlife = identify_non_wildlife(df)
    wildlife = df[~df.index.isin(non_wildlife.index)]
    
    # Métricas por sitio
    anthro_by_site = non_wildlife.groupby(site_column).size() if len(non_wildlife) > 0 else pd.Series()
    wildlife_richness = wildlife.groupby(site_column)['Especie_Categoria'].nunique()
    wildlife_abundance = wildlife.groupby(site_column)['Eventos_Independientes'].sum()
    
    # Crear DataFrame combinado
    combined = pd.DataFrame({
        'Sitio': wildlife_richness.index,
        'Riqueza_Fauna': wildlife_richness.values,
        'Abundancia_Fauna': wildlife_abundance.values
    })
    
    combined['Registros_Antropogenicos'] = combined['Sitio'].map(anthro_by_site).fillna(0)
    
    # Calcular correlaciones
    correlations = {}
    
    if len(combined) > 3 and combined['Registros_Antropogenicos'].sum() > 0:
        # Correlación con riqueza
        corr_r, p_val_r = spearmanr(combined['Registros_Antropogenicos'], 
                                     combined['Riqueza_Fauna'])
        
        # Correlación con abundancia
        corr_a, p_val_a = spearmanr(combined['Registros_Antropogenicos'], 
                                     combined['Abundancia_Fauna'])
        
        correlations = {
            'richness_correlation': corr_r,
            'richness_pvalue': p_val_r,
            'abundance_correlation': corr_a,
            'abundance_pvalue': p_val_a,
            'interpretation': interpret_correlation(corr_r, p_val_r)
        }
    
    return {
        'correlations': correlations,
        'data': combined
    }


def interpret_correlation(corr, pval):
    """
    Interpreta correlación
    
    Args:
        corr: Coeficiente de correlación
        pval: P-valor
    
    Returns:
        str: Interpretación
    """
    if pval > 0.05:
        return "No se encontró correlación significativa entre presencia antropogénica y riqueza de fauna."
    
    if corr < -0.5:
        return "Correlación negativa fuerte: La presencia antropogénica está asociada con menor riqueza de fauna."
    elif corr < -0.3:
        return "Correlación negativa moderada: La presencia antropogénica tiende a reducir la riqueza de fauna."
    elif corr < 0:
        return "Correlación negativa débil: Ligera tendencia de reducción de fauna con presencia antropogénica."
    elif corr < 0.3:
        return "Correlación positiva débil: No hay evidencia clara de impacto negativo."
    else:
        return "Correlación positiva: Resultado inesperado que requiere investigación adicional."


def generate_management_recommendations(impact_df):
    """
    Genera recomendaciones de manejo basadas en impacto antropogénico
    
    Args:
        impact_df: DataFrame con impacto por sitio
    
    Returns:
        list: Lista de recomendaciones
    """
    recommendations = []
    
    # Sitios con alto impacto
    high_impact_sites = impact_df[impact_df['Nivel_Impacto'].isin(['Alto', 'Muy Alto'])]
    
    if len(high_impact_sites) > 0:
        recommendations.append({
            'priority': 'Alta',
            'recommendation': f"Se identificaron {len(high_impact_sites)} sitios con alto impacto antropogénico. "
                            f"Se recomienda implementar medidas de control de acceso y educación ambiental.",
            'sites': high_impact_sites['Sitio'].tolist()
        })
    
    # Presencia de perros domésticos
    if 'Perro Doméstico' in impact_df.columns or any('perro' in str(x).lower() for x in impact_df.get('Categoria_Antropogenica', [])):
        recommendations.append({
            'priority': 'Alta',
            'recommendation': "Se detectó presencia de perros domésticos. Estos pueden depredar fauna nativa "
                            "y transmitir enfermedades. Se recomienda implementar programas de control de perros ferales.",
            'sites': []
        })
    
    # Presencia de ganado
    avg_impact = impact_df['Porcentaje_Antropogenico'].mean()
    if avg_impact > 15:
        recommendations.append({
            'priority': 'Media',
            'recommendation': f"El impacto antropogénico promedio es {avg_impact:.1f}%. "
                            f"Se recomienda evaluar la efectividad de las medidas de conservación actuales.",
            'sites': []
        })
    
    return recommendations
