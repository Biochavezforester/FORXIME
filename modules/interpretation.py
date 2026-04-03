"""
Módulo de interpretación automática para FORXIME/2
Genera interpretaciones en lenguaje natural de los resultados
"""


def interpret_biodiversity_indices(indices, language='es'):
    """
    Interpreta índices de biodiversidad
    
    Args:
        indices: Diccionario con índices
        language: Idioma ('es' o 'en')
    
    Returns:
        str: Interpretación en texto
    """
    shannon = indices.get('Shannon', 0)
    simpson = indices.get('Simpson', 0)
    richness = indices.get('Richness', 0)
    pielou = indices.get('Pielou_Evenness', 0)
    
    if language == 'es':
        interpretation = f"""
### Interpretación de Índices de Biodiversidad

**Riqueza de Especies:** Se registraron **{richness} especies** en el área de estudio.

**Índice de Shannon-Wiener ({shannon:.3f}):**
"""
        if shannon < 1.5:
            interpretation += "Valor **bajo**, indicando baja diversidad. Esto puede deberse a dominancia de pocas especies o baja riqueza."
        elif shannon < 3.0:
            interpretation += "Valor **moderado**, indicando diversidad media. La comunidad tiene una diversidad aceptable."
        else:
            interpretation += "Valor **alto**, indicando alta diversidad. La comunidad es muy diversa con múltiples especies bien representadas."
        
        interpretation += f"""

**Índice de Simpson ({simpson:.3f}):**
"""
        if simpson < 0.5:
            interpretation += "Valor **bajo**, indicando que la comunidad está dominada por pocas especies."
        elif simpson < 0.8:
            interpretation += "Valor **moderado**, indicando diversidad media con cierta dominancia."
        else:
            interpretation += "Valor **alto**, indicando alta diversidad y baja dominancia. La comunidad está bien equilibrada."
        
        interpretation += f"""

**Equitatividad de Pielou ({pielou:.3f}):**
"""
        if pielou < 0.5:
            interpretation += "Valor **bajo**, indicando distribución desigual de abundancias. Algunas especies son mucho más comunes que otras."
        elif pielou < 0.75:
            interpretation += "Valor **moderado**, indicando distribución relativamente equilibrada de abundancias."
        else:
            interpretation += "Valor **alto**, indicando distribución muy equilibrada. Las especies tienen abundancias similares."
        
        interpretation += "\n\n**Conclusión General:** "
        
        if shannon > 2.5 and simpson > 0.7:
            interpretation += "El área de estudio presenta una **comunidad saludable y diversa** con buena representación de múltiples especies."
        elif shannon < 1.5 or simpson < 0.5:
            interpretation += "El área muestra **baja diversidad**, lo que podría indicar perturbación, hábitat degradado, o especialización del ecosistema."
        else:
            interpretation += "El área presenta **diversidad moderada**, típica de ecosistemas en transición o con presiones moderadas."
    
    else:  # English
        interpretation = f"""
### Biodiversity Indices Interpretation

**Species Richness:** **{richness} species** were recorded in the study area.

**Shannon-Wiener Index ({shannon:.3f}):**
"""
        if shannon < 1.5:
            interpretation += "**Low** value, indicating low diversity. This may be due to dominance of few species or low richness."
        elif shannon < 3.0:
            interpretation += "**Moderate** value, indicating medium diversity. The community has acceptable diversity."
        else:
            interpretation += "**High** value, indicating high diversity. The community is very diverse with multiple well-represented species."
        
        interpretation += f"""

**Simpson Index ({simpson:.3f}):**
"""
        if simpson < 0.5:
            interpretation += "**Low** value, indicating the community is dominated by few species."
        elif simpson < 0.8:
            interpretation += "**Moderate** value, indicating medium diversity with some dominance."
        else:
            interpretation += "**High** value, indicating high diversity and low dominance. The community is well balanced."
    
    return interpretation


def interpret_dendrogram(distance_matrix, site_names, language='es'):
    """
    Interpreta dendrograma de Bray-Curtis
    
    Args:
        distance_matrix: Matriz de distancias
        site_names: Nombres de sitios
        language: Idioma
    
    Returns:
        str: Interpretación
    """
    import numpy as np
    
    avg_distance = np.mean(distance_matrix[np.triu_indices_from(distance_matrix, k=1)])
    
    if language == 'es':
        interpretation = f"""
### Interpretación del Dendrograma de Bray-Curtis

El dendrograma muestra la **similitud en composición de especies** entre los sitios de muestreo.

**Distancia promedio de Bray-Curtis:** {avg_distance:.3f}

"""
        if avg_distance < 0.3:
            interpretation += "Los sitios son **muy similares** en composición de especies. Esto sugiere un hábitat homogéneo o conectividad alta entre sitios."
        elif avg_distance < 0.6:
            interpretation += "Los sitios muestran **similitud moderada**. Existe cierta variación en la composición de especies entre sitios."
        else:
            interpretation += "Los sitios son **muy diferentes** en composición de especies. Esto sugiere heterogeneidad de hábitat o sitios en diferentes condiciones ecológicas."
        
        interpretation += """

**Cómo interpretar el dendrograma:**
- Sitios que se agrupan a **distancias cortas** (cerca de 0) tienen composiciones de especies muy similares
- Sitios que se unen a **distancias largas** tienen composiciones muy diferentes
- Los grupos formados pueden representar diferentes tipos de hábitat o condiciones ambientales
"""
    
    else:  # English
        interpretation = f"""
### Bray-Curtis Dendrogram Interpretation

The dendrogram shows the **similarity in species composition** between sampling sites.

**Average Bray-Curtis distance:** {avg_distance:.3f}

"""
        if avg_distance < 0.3:
            interpretation += "Sites are **very similar** in species composition. This suggests homogeneous habitat or high connectivity between sites."
        elif avg_distance < 0.6:
            interpretation += "Sites show **moderate similarity**. There is some variation in species composition between sites."
        else:
            interpretation += "Sites are **very different** in species composition. This suggests habitat heterogeneity or sites in different ecological conditions."
    
    return interpretation


def interpret_temporal_overlap(overlap_data, interaction_type='general', language='es'):
    """
    Interpreta solapamiento temporal
    
    Args:
        overlap_data: Datos de solapamiento
        interaction_type: 'predator-prey', 'competition', o 'general'
        language: Idioma
    
    Returns:
        str: Interpretación
    """
    sp1 = overlap_data['species1']
    sp2 = overlap_data['species2']
    ridout_coef = overlap_data['ridout_linkie']['coefficient']
    ci_lower = overlap_data['ridout_linkie']['ci_lower']
    ci_upper = overlap_data['ridout_linkie']['ci_upper']
    kernel_pct = overlap_data['kernel_overlap']['overlap_percentage']
    
    pattern1 = overlap_data['activity_pattern_sp1']['pattern']
    pattern2 = overlap_data['activity_pattern_sp2']['pattern']
    
    if language == 'es':
        interpretation = f"""
### Análisis de Solapamiento Temporal: {sp1} vs {sp2}

**Patrones de Actividad:**
- **{sp1}:** {pattern1}
- **{sp2}:** {pattern2}

**Coeficiente de Solapamiento (Ridout & Linkie):** {ridout_coef:.3f} (IC 95%: {ci_lower:.3f} - {ci_upper:.3f})
**Solapamiento por Kernel Density:** {kernel_pct:.1f}%

**Interpretación del Solapamiento:**
"""
        if ridout_coef > 0.75:
            interpretation += f"**Alto solapamiento** (Δ > 0.75). Las especies están activas en las mismas horas del día."
        elif ridout_coef > 0.5:
            interpretation += f"**Solapamiento moderado** (0.5 < Δ < 0.75). Existe coincidencia parcial en los períodos de actividad."
        else:
            interpretation += f"**Bajo solapamiento** (Δ < 0.5). Las especies tienen patrones de actividad diferentes."
        
        interpretation += "\n\n**Implicaciones Ecológicas:**\n"
        
        if interaction_type == 'predator-prey':
            if ridout_coef > 0.75:
                interpretation += f"El alto solapamiento sugiere que {sp2} (presa) está **expuesta** al depredador durante sus períodos de actividad. Esto puede indicar alta presión de depredación o que la presa no puede evitar temporalmente al depredador."
            elif ridout_coef > 0.5:
                interpretation += f"El solapamiento moderado sugiere que existe **riesgo de encuentros** entre depredador y presa, pero la presa tiene algunos períodos de actividad con menor riesgo."
            else:
                interpretation += f"El bajo solapamiento sugiere que {sp2} (presa) podría estar **evitando temporalmente** al depredador como estrategia anti-depredación."
        
        elif interaction_type == 'competition':
            if ridout_coef > 0.75:
                interpretation += f"El alto solapamiento sugiere **competencia directa** por recursos. Ambas especies están activas simultáneamente, lo que puede indicar abundancia de recursos o partición espacial del hábitat."
            elif ridout_coef > 0.5:
                interpretation += f"El solapamiento moderado sugiere **coexistencia** con cierta partición temporal de recursos."
            else:
                interpretation += f"El bajo solapamiento sugiere **partición temporal del nicho**. Los competidores evitan encontrarse mediante segregación temporal."
        
        else:  # general
            if ridout_coef > 0.75:
                interpretation += "Las especies comparten los mismos períodos de actividad, lo que puede facilitar interacciones directas."
            else:
                interpretation += "Las especies tienen patrones de actividad diferentes, lo que reduce la probabilidad de encuentros directos."
    
    else:  # English
        interpretation = f"""
### Temporal Overlap Analysis: {sp1} vs {sp2}

**Activity Patterns:**
- **{sp1}:** {pattern1}
- **{sp2}:** {pattern2}

**Overlap Coefficient (Ridout & Linkie):** {ridout_coef:.3f} (95% CI: {ci_lower:.3f} - {ci_upper:.3f})
**Kernel Density Overlap:** {kernel_pct:.1f}%
"""
    
    return interpretation


def interpret_royle_nichols(rn_results, species, language='es'):
    """
    Interpreta resultados del modelo Royle-Nichols
    
    Args:
        rn_results: Resultados del modelo
        species: Nombre de la especie
        language: Idioma
    
    Returns:
        str: Interpretación
    """
    if not rn_results['success']:
        if language == 'es':
            return f"**{species}:** No se pudo aplicar el modelo Royle-Nichols. {rn_results.get('message', '')}"
        else:
            return f"**{species}:** Royle-Nichols model could not be applied. {rn_results.get('message', '')}"
    
    psi = rn_results['psi']
    lambda_val = rn_results['lambda']
    p_det = rn_results['p_detection']
    
    if language == 'es':
        interpretation = f"""
### Modelo Royle-Nichols: {species}

**Ocupación (ψ):** {psi:.3f} ({psi*100:.1f}% de sitios ocupados)
**Abundancia Relativa (λ):** {lambda_val:.2f}
**Probabilidad de Detección (p):** {p_det:.3f}

**Interpretación:**
"""
        if psi > 0.7:
            interpretation += f"La especie tiene **alta ocupación**, estando presente en la mayoría de los sitios muestreados."
        elif psi > 0.4:
            interpretation += f"La especie tiene **ocupación moderada**, presente en aproximadamente la mitad de los sitios."
        else:
            interpretation += f"La especie tiene **baja ocupación**, presente en pocos sitios. Puede ser rara o tener requerimientos de hábitat específicos."
        
        interpretation += f"\n\nLa abundancia relativa (λ = {lambda_val:.2f}) "
        if lambda_val > 2:
            interpretation += "sugiere **múltiples individuos** por sitio ocupado."
        elif lambda_val > 1:
            interpretation += "sugiere **1-2 individuos** por sitio ocupado."
        else:
            interpretation += "sugiere **baja densidad** en los sitios ocupados."
        
        if p_det < 0.3:
            interpretation += f"\n\n⚠️ La probabilidad de detección es baja ({p_det:.3f}), lo que puede indicar que la especie es difícil de detectar o tiene baja actividad frente a las cámaras."
    
    else:  # English
        interpretation = f"""
### Royle-Nichols Model: {species}

**Occupancy (ψ):** {psi:.3f} ({psi*100:.1f}% of sites occupied)
**Relative Abundance (λ):** {lambda_val:.2f}
**Detection Probability (p):** {p_det:.3f}
"""
    
    return interpretation


def interpret_anthropogenic_impact(impact_results, language='es'):
    """
    Interpreta impacto antropogénico
    
    Args:
        impact_results: Resultados de impacto
        language: Idioma
    
    Returns:
        str: Interpretación
    """
    anthro_pct = impact_results['anthropogenic_percentage']
    total = impact_results['total_records']
    anthro = impact_results['anthropogenic_records']
    
    if language == 'es':
        interpretation = f"""
### Análisis de Impacto Antropogénico

**Registros Totales:** {total}
**Registros Antropogénicos:** {anthro} ({anthro_pct:.1f}%)
**Registros de Fauna Silvestre:** {impact_results['wildlife_records']}

**Nivel de Impacto:**
"""
        if anthro_pct < 5:
            interpretation += "**Bajo** - El área presenta mínima perturbación antropogénica."
        elif anthro_pct < 15:
            interpretation += "**Moderado** - Existe presencia humana pero no domina el área."
        elif anthro_pct < 30:
            interpretation += "**Alto** - Presencia antropogénica significativa que puede afectar la fauna silvestre."
        else:
            interpretation += "**Muy Alto** - El área está fuertemente impactada por actividades humanas."
        
        if impact_results['by_category']:
            interpretation += "\n\n**Categorías Detectadas:**\n"
            for category, count in impact_results['by_category'].items():
                interpretation += f"- {category}: {count} registros\n"
        
        interpretation += "\n**Recomendaciones:**\n"
        if anthro_pct > 15:
            interpretation += "- Considerar medidas de control de acceso\n"
            interpretation += "- Implementar programas de educación ambiental\n"
            interpretation += "- Evaluar el impacto en especies sensibles\n"
        else:
            interpretation += "- Mantener las medidas de conservación actuales\n"
            interpretation += "- Monitorear cambios en el tiempo\n"
    
    else:  # English
        interpretation = f"""
### Anthropogenic Impact Analysis

**Total Records:** {total}
**Anthropogenic Records:** {anthro} ({anthro_pct:.1f}%)
**Wildlife Records:** {impact_results['wildlife_records']}
"""
    
    return interpretation


def interpret_sampling_quality(sampling_recommendations, language='es'):
    """
    Interpreta calidad del muestreo
    
    Args:
        sampling_recommendations: Recomendaciones de muestreo
        language: Idioma
    
    Returns:
        str: Interpretación
    """
    if language == 'es':
        interpretation = """
### Evaluación de la Calidad del Muestreo

"""
        if len(sampling_recommendations) == 0:
            interpretation += "✅ **Excelente** - El diseño de muestreo cumple con todos los estándares recomendados."
        else:
            interpretation += f"Se identificaron **{len(sampling_recommendations)} áreas de mejora:**\n\n"
            
            for i, rec in enumerate(sampling_recommendations, 1):
                priority_emoji = "🔴" if rec['priority'] == 'Alta' else "🟡" if rec['priority'] == 'Media' else "🟢"
                interpretation += f"{priority_emoji} **{rec['category']}** (Prioridad: {rec['priority']})\n"
                interpretation += f"   {rec['recommendation']}\n\n"
    
    else:  # English
        interpretation = """
### Sampling Quality Evaluation

"""
        if len(sampling_recommendations) == 0:
            interpretation += "✅ **Excellent** - The sampling design meets all recommended standards."
        else:
            interpretation += f"**{len(sampling_recommendations)} areas for improvement** were identified:\n\n"
    
    return interpretation


def generate_executive_summary(all_results, language='es'):
    """
    Genera resumen ejecutivo de todos los análisis
    
    Args:
        all_results: Diccionario con todos los resultados
        language: Idioma
    
    Returns:
        str: Resumen ejecutivo
    """
    if language == 'es':
        summary = """
# 📊 Resumen Ejecutivo - Análisis de Cámaras Trampa

## Información General del Estudio
"""
        # Agregar información básica si está disponible
        if 'basic_metrics' in all_results:
            metrics = all_results['basic_metrics']
            summary += f"""
- **Período de muestreo:** {metrics['date_range']['days']} días
- **Número de cámaras:** {metrics['total_cameras']}
- **Número de sitios:** {metrics['total_sites']}
- **Especies registradas:** {metrics['total_species']}
- **Eventos independientes:** {metrics['total_independent_events']}
"""
        
        summary += "\n## Principales Hallazgos\n\n"
        
        # Biodiversidad
        if 'biodiversity' in all_results:
            indices = all_results['biodiversity']
            summary += f"### 🌿 Biodiversidad\n"
            summary += f"- Riqueza: {indices['Richness']} especies\n"
            summary += f"- Índice de Shannon: {indices['Shannon']:.3f}\n"
            summary += f"- Índice de Simpson: {indices['Simpson']:.3f}\n\n"
        
        # Impacto antropogénico
        if 'anthropogenic' in all_results:
            impact = all_results['anthropogenic']
            summary += f"### 👥 Impacto Antropogénico\n"
            summary += f"- Registros antropogénicos: {impact['anthropogenic_percentage']:.1f}%\n\n"
        
        summary += "\n---\n*Reporte generado por FORXIME/2*\n"
    
    else:  # English
        summary = """
# 📊 Executive Summary - Camera Trap Analysis

## Study Overview
"""
    
    return summary
