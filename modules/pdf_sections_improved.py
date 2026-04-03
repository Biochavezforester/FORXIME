"""
Actualización del módulo PDF helper con mejoras solicitadas
"""

# Función para generar justificaciones de conservación basadas en características ecológicas
def generate_conservation_justification(species_name, rai=0, status='', biogeographic=''):
    """
    Genera justificación de conservación basada en múltiples criterios
    """
    justifications = []
    
    # Justificación por RAI
    if rai > 10:
        justifications.append("Alta frecuencia de detección")
    elif rai > 5:
        justifications.append("Frecuencia moderada de detección")
    else:
        justifications.append("Baja frecuencia de detección - requiere monitoreo")
    
    # Justificación por estatus de conservación
    if 'peligro' in status.lower() or 'amenazada' in status.lower():
        justifications.append("Especie en riesgo según NOM-059")
    elif 'protección especial' in status.lower():
        justifications.append("Requiere protección especial")
    
    # Justificación por biogeografía
    if 'endémica' in biogeographic.lower() or 'endemic' in biogeographic.lower():
        justifications.append("Especie endémica de importancia nacional")
    elif 'nativa' in biogeographic.lower():
        justifications.append("Especie nativa del ecosistema")
    
    # Justificaciones específicas por especie (basadas en conocimiento ecológico)
    species_lower = species_name.lower()
    
    # Grandes felinos
    if any(cat in species_lower for cat in ['panthera', 'puma', 'leopardus', 'jaguar', 'ocelote']):
        justifications.append("Depredador tope - indicador de salud ecosistémica")
        justifications.append("Requiere grandes extensiones de hábitat")
    
    # Ungulados
    if any(ung in species_lower for cat in ['odocoileus', 'venado', 'pecari', 'pecarí', 'mazama', 'tapirus']):
        justifications.append("Especie clave para dispersión de semillas")
        justifications.append("Presa importante para depredadores")
    
    # Osos
    if 'ursus' in species_lower or 'oso' in species_lower:
        justifications.append("Especie paraguas - protege múltiples especies")
        justifications.append("Alta sensibilidad a perturbación humana")
    
    # Primates
    if any(primate in species_lower for primate in ['ateles', 'alouatta', 'mono', 'saraguato']):
        justifications.append("Dispersor de semillas de árboles grandes")
        justifications.append("Indicador de bosques maduros")
    
    # Tapir
    if 'tapirus' in species_lower or 'tapir' in species_lower:
        justifications.append("Ingeniero de ecosistemas")
        justifications.append("Dispersor de semillas de larga distancia")
    
    # Si no hay justificaciones específicas, agregar genéricas
    if len(justifications) == 0:
        justifications.append("Componente de la biodiversidad local")
        justifications.append("Requiere evaluación de estatus poblacional")
    
    return " | ".join(justifications[:3])  # Máximo 3 justificaciones


# Actualizar la función de conservación en pdf_sections_helper.py
def add_conservation_section_improved(story, results, styles):
    """Agrega sección de conservación con justificaciones generadas"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import pandas as pd
    
    story.append(Paragraph("6. PRIORIDADES DE CONSERVACIÓN", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    conservation = results.get('conservation_priorities', pd.DataFrame())
    
    if not conservation.empty:
        # Mostrar top 10 especies prioritarias
        top_conservation = conservation.head(10)
        
        cons_data = [['Especie', 'Prioridad', 'Justificación']]
        for _, row in top_conservation.iterrows():
            especie = str(row.get('Especie', ''))
            prioridad = str(row.get('Prioridad', ''))
            
            # Generar justificación si está vacía
            justificacion_original = str(row.get('Justificacion', ''))
            if not justificacion_original or justificacion_original == 'nan' or len(justificacion_original) < 5:
                # Obtener datos adicionales
                rai = row.get('RAI', 0)
                status = row.get('Estatus_NOM059', '')
                biogeographic = row.get('Biogeografico', '')
                justificacion = generate_conservation_justification(especie, rai, status, biogeographic)
            else:
                justificacion = justificacion_original
            
            # Truncar si es muy largo
            if len(especie) > 30:
                especie = especie[:27] + "..."
            if len(justificacion) > 60:
                justificacion = justificacion[:57] + "..."
            
            cons_data.append([especie, prioridad, justificacion])
        
        cons_table = Table(cons_data, colWidths=[2*inch, 1.2*inch, 3.3*inch])
        cons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(cons_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Interpretación
        interpretation = """
        <para alignment="justify">
        <b>Interpretación:</b> Las especies listadas requieren atención prioritaria para su conservación 
        debido a su estatus de riesgo, importancia ecológica, o baja frecuencia de detección. Se recomienda 
        implementar medidas de protección de hábitat, monitoreo continuo, y evaluación de conectividad entre 
        poblaciones para asegurar su viabilidad a largo plazo.
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


# Función para agregar sección de manejo ganadero
def add_livestock_management_section(story, results, styles):
    """Agrega sección de manejo ganadero"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import pandas as pd
    
    story.append(Paragraph("8. MANEJO GANADERO", styles['CustomHeading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Buscar datos de ganado en los resultados
    livestock_data = results.get('livestock_management', {})
    rai_df = results.get('rai', pd.DataFrame())
    
    # Filtrar especies de ganado
    if not rai_df.empty:
        livestock_species = rai_df[rai_df['Especie'].str.contains('Bos|Equus|Capra|Ovis|ganado|cattle|horse|caballo|vaca|toro', 
                                                                   case=False, na=False)]
        
        if not livestock_species.empty:
            story.append(Paragraph("8.1 Detección de Ganado en el Área", styles['CustomHeading3']))
            
            livestock_table_data = [['Especie', 'Eventos', 'RAI', 'Impacto Potencial']]
            for _, row in livestock_species.iterrows():
                especie = str(row.get('Especie', ''))
                eventos = int(row.get('Eventos_Independientes', 0))
                rai = row.get('RAI', 0)
                
                # Evaluar impacto
                if rai > 15:
                    impacto = "Alto"
                elif rai > 5:
                    impacto = "Moderado"
                else:
                    impacto = "Bajo"
                
                livestock_table_data.append([especie, str(eventos), f"{rai:.2f}", impacto])
            
            livestock_table = Table(livestock_table_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.6*inch])
            livestock_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(livestock_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Recomendaciones
            recommendations = """
            <para alignment="justify">
            <b>Recomendaciones de Manejo:</b><br/>
            • Implementar rotación de potreros para reducir sobrepastoreo<br/>
            • Mantener corredores biológicos libres de ganado<br/>
            • Establecer bebederos artificiales para evitar concentración en fuentes naturales<br/>
            • Monitorear carga animal para prevenir degradación del hábitat<br/>
            • Considerar cercado de áreas críticas para fauna silvestre<br/>
            • Evaluar compatibilidad entre actividad ganadera y conservación
            </para>
            """
            story.append(Paragraph(recommendations, styles['Justified']))
        else:
            story.append(Paragraph("No se detectó presencia significativa de ganado en el área de estudio.", 
                                 styles['BodyText']))
    else:
        story.append(Paragraph("No hay datos disponibles para evaluación de manejo ganadero.", styles['BodyText']))
    
    story.append(PageBreak())
    return story
