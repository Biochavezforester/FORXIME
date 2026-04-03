"""
Secciones adicionales para el módulo PDF de FORXIME/2
Este archivo contiene las implementaciones de las secciones faltantes
"""

def add_temporal_patterns_section(story, results, styles):
    """Agrega sección de patrones temporales"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    story.append(Paragraph("4. PATRONES DE ACTIVIDAD TEMPORAL", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    activity_patterns = results.get('activity_patterns', {})
    
    if activity_patterns:
        # Mostrar top 5 especies
        species_list = list(activity_patterns.keys())[:5]
        
        for idx, species in enumerate(species_list, 1):
            pattern_data = activity_patterns[species]
            
            story.append(Paragraph(f"4.{idx} {species}", styles['CustomHeading3']))
            
            # Tabla con datos del patrón
            mean_hour = pattern_data.get('mean_hour', 0)
            hours = int(mean_hour)
            minutes = int((mean_hour - hours) * 60)
            
            pattern_table_data = [
                ['Patrón', 'Hora Pico', 'Concentración'],
                [
                    pattern_data.get('pattern', 'N/A'),
                    f"{hours:02d}:{minutes:02d}",
                    f"{pattern_data.get('concentration', 0):.3f}"
                ]
            ]
            
            pattern_table = Table(pattern_table_data, colWidths=[2*inch, 2*inch, 2*inch])
            pattern_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(pattern_table)
            story.append(Spacer(1, 0.2*inch))
    else:
        story.append(Paragraph("No hay datos suficientes para análisis temporal.", styles['BodyText']))
    
    story.append(PageBreak())
    return story


def add_anthropogenic_section(story, results, styles):
    """Agrega sección de impacto antropogénico"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import pandas as pd
    
    story.append(Paragraph("5. IMPACTO ANTROPOGÉNICO", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    anthro = results.get('anthropogenic', {})
    
    if anthro:
        # Métricas generales
        metrics_data = [
            ['Métrica', 'Valor'],
            ['Registros Totales', str(anthro.get('total_records', 0))],
            ['Registros Antropogénicos', str(anthro.get('anthropogenic_records', 0))],
            ['Porcentaje', f"{anthro.get('anthropogenic_percentage', 0):.1f}%"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Impacto por sitio
        anthro_by_site = results.get('anthropogenic_by_site', pd.DataFrame())
        if not anthro_by_site.empty:
            story.append(Paragraph("5.1 Impacto por Sitio", styles['CustomHeading3']))
            
            site_data = [list(anthro_by_site.columns)]
            for _, row in anthro_by_site.iterrows():
                site_data.append([str(val) if not isinstance(val, float) else f"{val:.1f}" 
                                for val in row])
            
            site_table = Table(site_data)
            site_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(site_table)
    else:
        story.append(Paragraph("No hay datos de impacto antropogénico disponibles.", styles['BodyText']))
    
    story.append(PageBreak())
    return story


def add_conservation_section(story, results, styles):
    """Agrega sección de conservación con justificaciones generadas"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import pandas as pd
    
    # Función helper para generar justificaciones
    def generate_justification(species_name, rai=0):
        justifications = []
        species_lower = species_name.lower()
        
        # Argumentos basados en RAI y ecología poblacional
        if rai > 15:
            justifications.append("Alta detectabilidad (RAI>15) sugiere población estable o alta movilidad territorial")
        elif rai > 8:
            justifications.append("Detectabilidad moderada-alta (RAI 8-15) indica presencia regular en el área")
        elif rai > 3:
            justifications.append("Detectabilidad moderada (RAI 3-8) requiere monitoreo para evaluar tendencias poblacionales")
        else:
            justifications.append("Baja detectabilidad (RAI<3) puede indicar población reducida, comportamiento críptico o uso ocasional del área - prioridad de conservación")
        
        # Argumentos ecológicos específicos por grupo taxonómico
        if any(cat in species_lower for cat in ['panthera', 'puma', 'leopardus', 'jaguar', 'ocelote', 'lynx']):
            justifications.append("Depredador tope: regula poblaciones de mesodepredadores y herbívoros, requiere >100 km² de hábitat continuo, indicador de integridad ecosistémica (Ripple et al. 2014)")
        
        elif any(ung in species_lower for ung in ['odocoileus', 'venado', 'pecari', 'pecarí', 'mazama', 'cervus']):
            justifications.append("Herbívoro clave: dispersor de semillas, presa base para carnívoros, ingeniero de ecosistemas por ramoneo selectivo (Dirzo & Miranda 1991)")
        
        elif 'tapirus' in species_lower or 'tapir' in species_lower:
            justifications.append("Megaherbívoro: ingeniero de ecosistemas, dispersor de semillas de >100 especies, crea senderos y claros, indicador de bosques maduros (Fragoso 1997)")
        
        elif any(primate in species_lower for primate in ['ateles', 'alouatta', 'mono', 'saraguato', 'araña']):
            justifications.append("Primate frugívoro: dispersor legítimo de semillas grandes (>1cm), esencial para regeneración de árboles emergentes, indicador de bosque primario (Chapman & Russo 2007)")
        
        elif 'ursus' in species_lower or 'oso' in species_lower:
            justifications.append("Especie paraguas: protección beneficia >200 especies, alta sensibilidad a perturbación humana, dispersor de semillas y nutrientes (Servheen et al. 1999)")
        
        elif any(bird in species_lower for bird in ['crax', 'penelope', 'hocofaisán', 'pava', 'chachalaca']):
            justifications.append("Ave terrestre: dispersor de semillas, indicador de calidad de sotobosque, sensible a fragmentación (Brooks & Fuller 2006)")
        
        elif any(carn in species_lower for carn in ['nasua', 'procyon', 'bassariscus', 'coatí', 'mapache', 'cacomixtle']):
            justifications.append("Mesocarnívoro: dispersor de semillas, control de invertebrados, puede aumentar por liberación mesodepredadora (Crooks & Soulé 1999)")
        
        else:
            justifications.append("Componente de biodiversidad local: rol ecológico requiere evaluación específica, contribuye a redes tróficas y procesos ecosistémicos")
        
        return " | ".join(justifications[:2])  # Máximo 2 justificaciones para que quepa

    
    story.append(Paragraph("6. PRIORIDADES DE CONSERVACIÓN", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    conservation = results.get('conservation_priorities', pd.DataFrame())
    
    if not conservation.empty:
        top_conservation = conservation.head(10)
        
        cons_data = [['Especie', 'Prioridad', 'Justificación']]
        for _, row in top_conservation.iterrows():
            especie = str(row.get('Especie', ''))
            prioridad = str(row.get('Prioridad', ''))
            
            # Generar justificación
            justificacion_original = str(row.get('Justificacion', ''))
            if not justificacion_original or justificacion_original == 'nan' or len(justificacion_original) < 5:
                rai = row.get('RAI', 0)
                justificacion = generate_justification(especie, rai)
            else:
                justificacion = justificacion_original
            
            if len(especie) > 28:
                especie = especie[:25] + "..."
            if len(justificacion) > 70:
                justificacion = justificacion[:67] + "..."
            
            cons_data.append([especie, prioridad, justificacion])
        
        cons_table = Table(cons_data, colWidths=[1.8*inch, 1*inch, 3.7*inch])
        cons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(cons_table)
        story.append(Spacer(1, 0.2*inch))
        
        interpretation = """
        <para alignment="justify">
        <b>Interpretación:</b> Las especies listadas requieren atención prioritaria debido a su estatus 
        de riesgo, importancia ecológica, o baja frecuencia de detección. Se recomienda implementar medidas 
        de protección de hábitat, monitoreo continuo, y evaluación de conectividad para asegurar viabilidad 
        a largo plazo.
        </para>
        """
        story.append(Paragraph(interpretation, styles['Interpretation']))
        story.append(Spacer(1, 0.2*inch))
    else:
        story.append(Paragraph("No hay datos de prioridades de conservación disponibles.", styles['BodyText']))
    
    # Hábitats críticos
    habitats = results.get('critical_habitats', pd.DataFrame())
    if not habitats.empty:
        story.append(Paragraph("6.1 Hábitats Críticos Identificados", styles['CustomHeading3']))
        
        hab_data = [list(habitats.columns)]
        for _, row in habitats.head(5).iterrows():
            hab_data.append([str(val) for val in row])
        
        hab_table = Table(hab_data)
        hab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        
        story.append(hab_table)
    
    story.append(PageBreak())
    return story


def add_hunting_section(story, results, styles):
    """Agrega sección de información cinegética"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    story.append(Paragraph("7. INFORMACIÓN CINEGÉTICA", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    hunting_info = results.get('hunting_info', {})
    
    if hunting_info and hunting_info.get('has_game_species', False):
        # Especies con potencial cinegético
        species_list = hunting_info.get('species_list')
        
        if species_list is not None and len(species_list) > 0:
            story.append(Paragraph("7.1 Especies con Potencial Cinegético Detectadas", styles['CustomHeading3']))
            
            # Crear tabla de especies cinegéticas
            hunt_data = [['Especie', 'Nombre Común', 'Registros', 'RAI']]
            
            # Obtener RAI de results
            rai_df = results.get('rai', None)
            
            for _, species_row in species_list.iterrows():
                especie = str(species_row.get('Especie', 'N/A'))
                nombre_comun = str(species_row.get('Nombre_Comun', 'N/A'))
                registros = int(species_row.get('Eventos_Detectados', 0))
                
                # Buscar RAI
                rai_value = 0
                if rai_df is not None:
                    rai_match = rai_df[rai_df['Especie'] == especie]
                    if not rai_match.empty:
                        rai_value = rai_match.iloc[0]['RAI']
                
                hunt_data.append([
                    especie[:28],
                    nombre_comun[:25],
                    str(registros),
                    f"{rai_value:.2f}"
                ])
            
            if len(hunt_data) > 1:  # Si hay datos además del encabezado
                hunt_table = Table(hunt_data, colWidths=[2.2*inch, 2*inch, 1.2*inch, 1.1*inch])
                hunt_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
                ]))
                
                story.append(hunt_table)
                story.append(Spacer(1, 0.2*inch))
            
            # Nota legal
            legal_note = """
            <para alignment="justify">
            <b>IMPORTANTE:</b> La cacería de estas especies requiere permisos especiales y debe 
            realizarse exclusivamente dentro de Unidades de Manejo para la Conservación de la Vida 
            Silvestre (UMAs) debidamente registradas ante SEMARNAT. Consulte la normatividad vigente.
            </para>
            """
            story.append(Paragraph(legal_note, styles['Justified']))
        else:
            story.append(Paragraph("No se detectaron especies con potencial cinegético en este estudio.", 
                                 styles['BodyText']))
    else:
        story.append(Paragraph("No se detectaron especies con potencial cinegético en este estudio.", 
                             styles['BodyText']))
    
    # story.append(PageBreak())
    return story


def add_livestock_management_section(story, results, styles):
    """Agrega sección de manejo ganadero basada en nombres de especies"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import pandas as pd
    
    story.append(Paragraph("8. MANEJO GANADERO", styles["CustomHeading2"]))
    story.append(Spacer(1, 0.2*inch))
    
    rai_df = results.get("rai", pd.DataFrame())
    
    if not rai_df.empty:
        livestock_species = rai_df[rai_df["Especie"].str.contains("Bos|Equus|Capra|Ovis|ganado|cattle|horse|caballo|vaca|toro|burro|mula|oveja|cabra", 
                                                                   case=False, na=False)]
        
        if not livestock_species.empty:
            story.append(Paragraph("8.1 Detección de Ganado en el Área", styles["CustomHeading3"]))
            
            livestock_table_data = [["Especie", "Eventos", "RAI", "Impacto Potencial"]]
            for _, row in livestock_species.iterrows():
                especie = str(row.get("Especie", ""))
                eventos = int(row.get("Eventos_Independientes", 0))
                rai = row.get("RAI", 0)
                
                if rai > 15:
                    impacto = "Alto"
                elif rai > 5:
                    impacto = "Moderado"
                else:
                    impacto = "Bajo"
                
                livestock_table_data.append([especie, str(eventos), f"{rai:.2f}", impacto])
            
            livestock_table = Table(livestock_table_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.6*inch])
            livestock_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(livestock_table)
            story.append(Spacer(1, 0.2*inch))
            
            recommendations = """
            <para alignment="justify">
            <b>Recomendaciones de Manejo:</b><br/>
            • Implementar rotación de potreros<br/>
            • Mantener corredores biológicos libres de ganado<br/>
            • Establecer bebederos artificiales<br/>
            • Monitorear carga animal<br/>
            • Evaluar compatibilidad con conservación
            </para>
            """
            story.append(Paragraph(recommendations, styles["Justified"]))
        else:
            story.append(Paragraph("No se detectó presencia significativa de ganado en el área de estudio.", 
                                 styles["BodyText"]))
    else:
        story.append(Paragraph("No hay datos disponibles para evaluación de manejo ganadero.", styles["BodyText"]))
    
    story.append(PageBreak())
    return story
