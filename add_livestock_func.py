# Script para agregar función de manejo ganadero
with open('modules/pdf_sections_helper.py', 'a', encoding='utf-8') as f:
    f.write('''

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
''')

print("Función agregada exitosamente")
