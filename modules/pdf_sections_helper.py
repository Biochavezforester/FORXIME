"""
Secciones adicionales para el módulo PDF de FORXIME
Este archivo contiene las implementaciones de las secciones faltantes
"""

import pandas as pd
import numpy as np
import io
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from modules.pdf_export import format_scientific_name

def safe_get_style(styles, name, default='Normal'):
    """Obtiene un estilo de forma segura del diccionario de estilos"""
    try:
        return styles[name]
    except (KeyError, IndexError):
        # Fallback a estilos estándar de reportlab si los custom fallan
        return styles.get(default, styles['Normal'])

def add_temporal_patterns_section(story, results, styles):
    """Agrega sección de patrones temporales"""

def add_temporal_patterns_section(story, results, styles):
    """Agrega sección de patrones temporales"""
    
    story.append(KeepTogether([
        Paragraph("6. PATRONES DE ACTIVIDAD TEMPORAL", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    activity_patterns = results.get('activity_patterns', {})
    
    if activity_patterns:
        # Mostrar todas las especies detectadas
        species_list = list(activity_patterns.keys())
        
        for idx, species in enumerate(species_list, 1):
            pattern_data = activity_patterns[species]
            
            formatted_species = format_scientific_name(species)
            story.append(KeepTogether([
                Paragraph(f"6.{idx} {formatted_species}", safe_get_style(styles, 'CustomHeading3'))
            ]))
            
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
                ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading2').fontName), # Usar fontName dinámico
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(pattern_table)
            story.append(Spacer(1, 0.2*inch))
    else:
        story.append(Paragraph("No hay datos suficientes para análisis temporal.", styles['BodyText']))
    
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_anthropogenic_section(story, results, styles):
    """Agrega sección de impacto antropogénico"""
    
    story.append(KeepTogether([
        Paragraph("7. IMPACTO ANTROPOGÉNICO", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
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
            ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Impacto por sitio
        anthro_by_site = results.get('anthropogenic_by_site', pd.DataFrame())
        if not anthro_by_site.empty:
            story.append(KeepTogether([
                Paragraph("7.1 Impacto por Sitio", safe_get_style(styles, 'CustomHeading3'))
            ]))
            
            site_data = [list(anthro_by_site.columns)]
            for _, row in anthro_by_site.iterrows():
                site_data.append([str(val) if not isinstance(val, float) else f"{val:.1f}" 
                                for val in row])
            
            site_table = Table(site_data)
            site_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(site_table)
    else:
        story.append(Paragraph("No hay datos de impacto antropogénico disponibles.", styles['BodyText']))
    
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_conservation_section(story, results, styles):
    """Agrega sección de conservación con justificaciones generadas"""
    
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

    
    # Diccionario de estatus NOM-059 (Ejemplo ampliado para México)
    # Diccionario de estatus NOM-059 (Extendido y Normalizado)
    NOM_059_DB = {
        # En peligro de extinción (P)
        'panthera onca': 'P (Peligro de extinción)', 'jaguar': 'P (Peligro de extinción)',
        'leopardus pardalis': 'P (Peligro de extinción)', 'ocelote': 'P (Peligro de extinción)',
        'leopardus wiedii': 'P (Peligro de extinción)', 'tigrillo': 'P (Peligro de extinción)',
        'herpailurus yagouaroundi': 'P (Peligro de extinción)', 'jaguarundi': 'P (Peligro de extinción)',
        'tapirus bairdii': 'P (Peligro de extinción)', 'tapir': 'P (Peligro de extinción)',
        'trichechus manatus': 'P (Peligro de extinción)', 'manatí': 'P (Peligro de extinción)',
        'ursus americanus': 'P (Peligro de extinción)', 'oso negro': 'P (Peligro de extinción)',
        'ateles geoffroyi': 'P (Peligro de extinción)', 'mono araña': 'P (Peligro de extinción)',
        'alouatta palliata': 'P (Peligro de extinción)', 'saraguato': 'P (Peligro de extinción)',
        'tayassu pecari': 'P (Peligro de extinción)', 'pecarí de labios blancos': 'P (Peligro de extinción)',
        'canis lupus baileyi': 'P (Peligro de extinción)', 'lobo mexicano': 'P (Peligro de extinción)',
        'ara macao': 'P (Peligro de extinción)', 'guacamaya roja': 'P (Peligro de extinción)',
        'phocoena sinus': 'P (Peligro de extinción)', 'vaquita marina': 'P (Peligro de extinción)',
        'ambystoma mexicanum': 'P (Peligro de extinción)', 'ajolote': 'P (Peligro de extinción)',
        'dermatemys mawii': 'P (Peligro de extinción)', 'tortuga blanca': 'P (Peligro de extinción)',
        'chelonia mydas': 'P (Peligro de extinción)', 'tortuga verde': 'P (Peligro de extinción)',
        'mazama temama': 'P (Peligro de extinción)', 'temazate': 'P (Peligro de extinción)',
        'antilocapra americana': 'P (Peligro de extinción)', 'berrendo': 'P (Peligro de extinción)',
        # Amenazada (A)
        'aquila chrysaetos': 'A (Amenazada)', 'águila real': 'A (Amenazada)',
        'crocodylus acutus': 'A (Amenazada)', 'cocodrilo de río': 'A (Amenazada)',
        'crax rubra': 'A (Amenazada)', 'hocofaisán': 'A (Amenazada)',
        'ctenosaura pectinata': 'A (Amenazada)', 'iguana negra': 'A (Amenazada)',
        'boa constrictor': 'A (Amenazada)', 'boa': 'A (Amenazada)',
        'harpia harpyja': 'A (Amenazada)', 'harpía': 'A (Amenazada)',
        # Sujeta a protección especial (Pr)
        'urocyon cinereoargenteus': 'Pr (Protección especial)', 'zorra gris': 'Pr (Protección especial)',
        'iguana iguana': 'Pr (Protección especial)', 'iguana verde': 'Pr (Protección especial)',
        'meleagris gallopavo': 'Pr (Protección especial)', 'guajolote silvestre': 'Pr (Protección especial)',
        # No listadas en NOM-059
        'puma concolor': 'No listada', 'puma': 'No listada',
        'lynx rufus': 'No listada (cinegética)', 'gato montés': 'No listada (cinegética)',
        'odocoileus virginianus': 'No listada (cinegética)', 'venado cola blanca': 'No listada (cinegética)',
        'pecari tajacu': 'No listada (cinegética)', 'pecarí de collar': 'No listada (cinegética)',
        'nasua narica': 'No listada', 'coatí': 'No listada', 'tejón': 'No listada',
        'procyon lotor': 'No listada', 'mapache': 'No listada',
        'didelphis virginiana': 'No listada', 'tlacuache': 'No listada',
        'sciurus': 'No listada', 'ardilla': 'No listada',
        'neotoma': 'No listada', 'rata de campo': 'No listada',
        'mephitis macroura': 'No listada', 'zorrillo': 'No listada',
        'meleagris gallopavo': 'Pr (Protección especial)', 'guajolote': 'Pr (Protección especial)',
        'canis latrans': 'No listada', 'coyote': 'No listada'
    }

    story.append(KeepTogether([
        Paragraph("8. PRIORIDADES DE CONSERVACIÓN Y ESTATUS LEGAL", styles['CustomHeading2']),
        Spacer(1, 0.2*inch)
    ]))
    
    conservation = results.get('conservation_priorities', pd.DataFrame())
    
    if not conservation.empty:
        top_conservation = conservation
        
        cons_data = [['Especie', 'Prioridad', 'Estatus\n(NOM/IUCN/CITES)', 'Justificación']]
        for _, row in top_conservation.iterrows():
            especie = str(row.get('Especie', ''))
            prioridad = str(row.get('Prioridad', ''))
            
            # Obtener estatus de las columnas (o fallback)
            nom_status = str(row.get('NOM_059', 'No listada'))
            iucn_status = str(row.get('Categoria_IUCN', 'LC'))
            cites_status = str(row.get('CITES', 'No listada'))
            
            # Si en PDF se usa el propio dict (por compatibilidad)
            if nom_status == 'No listada' or nom_status == 'nan':
                sp_clean = especie.lower().strip()
                for key, val in NOM_059_DB.items():
                    if key in sp_clean or sp_clean in key:
                        nom_status = val
                        break
            
            # Combinar estatus
            combined_status = f"NOM: {nom_status}\nIUCN: {iucn_status}"
            if cites_status != 'No listada' and cites_status != 'nan':
                combined_status += f"\nCITES: {cites_status}"
            
            # Generar justificación
            justificacion_original = str(row.get('Justificacion', ''))
            if not justificacion_original or justificacion_original == 'nan' or len(justificacion_original) < 5:
                rai = row.get('RAI', 0)
                justificacion = generate_justification(especie, rai)
            else:
                justificacion = justificacion_original
            
            # Truncar para que quepa
            if len(especie) > 25: especie = especie[:22] + "..."
            if len(justificacion) > 60: justificacion = justificacion[:57] + "..."
            
            # Formatear nombre científico en itálicas (usando Paragraph si es necesario)
            from modules.pdf_export import format_scientific_name
            formatted_name = Paragraph(format_scientific_name(especie), styles['Normal'])
            
            cons_data.append([formatted_name, prioridad, combined_status, justificacion])
        
        cons_table = Table(cons_data, colWidths=[1.8*inch, 0.7*inch, 1.5*inch, 2.5*inch])
        cons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
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
        story.append(KeepTogether([
            Paragraph("8.1 Hábitats Críticos Identificados", styles['CustomHeading3'])
        ]))
        
        hab_data = [list(habitats.columns)]
        for _, row in habitats.iterrows():
            hab_data.append([str(val) for val in row])
        
        hab_table = Table(hab_data)
        hab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        
        story.append(hab_table)
    
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_hunting_section(story, results, styles):
    """Agrega sección de información cinegética"""
    
    story.append(KeepTogether([
        Paragraph("9. INFORMACIÓN CINEGÉTICA", styles['CustomHeading2']),
        Spacer(1, 0.2*inch)
    ]))
    
    hunting_info = results.get('hunting_info', {})
    
    if hunting_info and hunting_info.get('has_game_species', False):
        # Especies con potencial cinegético
        species_list = hunting_info.get('species_list')
        
        if species_list is not None and len(species_list) > 0:
            story.append(KeepTogether([
                Paragraph("9.1 Especies con Potencial Cinegético Detectadas", styles['CustomHeading3'])
            ]))
            
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
                    ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
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
    
    story.append(KeepTogether([
        Paragraph("10. MANEJO GANADERO", styles["CustomHeading2"]),
        Spacer(1, 0.2*inch)
    ]))
    
    rai_df = results.get("rai", pd.DataFrame())
    
    if not rai_df.empty:
        # ELIMINAR FILTROS HARDCODED: Si el usuario seleccionó la categoría, DEBE aparecer.
        livestock_species = rai_df
        
        if not livestock_species.empty:
            story.append(KeepTogether([
                Paragraph("10.1 Detección de Ganado en el Área", styles["CustomHeading3"])
            ]))
            
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
                
                # Usar Paragraph para soportar itálicas en el nombre científico
                formatted_name = Paragraph(format_scientific_name(especie), styles['Normal'])
                livestock_table_data.append([formatted_name, str(eventos), f"{rai:.2f}", impacto])
            
            livestock_table = Table(livestock_table_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.6*inch])
            livestock_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
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
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_accumulation_curve_section(story, results, styles):
    """Agrega sección de curva de acumulación de especies"""
    
    story.append(KeepTogether([
        Paragraph("11. CURVA DE ACUMULACIÓN DE ESPECIES", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    accumulation = results.get('accumulation', None)
    
    if accumulation is not None and not accumulation.empty:
        try:
            from modules.visualization import create_accumulation_curve_plot
            fig = create_accumulation_curve_plot(accumulation)
            
            # Exportar figura interactiva a un formato estático para PDF
            img_bytes = fig.to_image(format="png", width=800, height=450, scale=2)
            img_buffer = io.BytesIO(img_bytes)
            
            # Ajustar tamaño de la imagen en el PDF
            pdf_img = Image(img_buffer, width=6.5*inch, height=3.5*inch)
            story.append(pdf_img)
            story.append(Spacer(1, 0.2*inch))
            
            interpretation = """
            <para alignment="justify">
            <b>Interpretación:</b> La gráfica muestra el ritmo al que se detectan nuevas especies a lo largo del tiempo. 
            Si la curva se aplana (llega a una asíntota), indica que el esfuerzo de muestreo fue suficiente 
            para registrar la mayoría de las especies de la zona. Si la curva sigue subiendo abruptamente, 
            hay especies aún no detectadas y se requiere más esfuerzo de muestreo.
            </para>
            """
            story.append(Paragraph(interpretation, safe_get_style(styles, 'Interpretation')))
            
        except Exception as e:
            story.append(Paragraph(f"Error generando gráfica de acumulación: {str(e)}", styles['BodyText']))
    else:
        story.append(Paragraph("No hay datos disponibles para generar la curva de acumulación.", styles['BodyText']))
    
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_dendrograms_section(story, results, wildlife_df, styles):
    """Agrega sección de dendrogramas de similitud (Normal y Hellinger)"""
    from modules.statistical_analysis import create_bray_curtis_dendrogram
    from modules.visualization import create_dendrogram_plot
    import matplotlib.pyplot as plt
    
    story.append(KeepTogether([
        Paragraph("14. SIMILITUD ENTRE SITIOS (DENDROGRAMAS)", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    try:
        # 1. Dendrograma Normal (Abundancia cruda)
        print(f"DEBUG: Starting dendrogram section (wildlife_df rows: {len(wildlife_df)})")
        dendro_norm = create_bray_curtis_dendrogram(wildlife_df, transform_hellinger=False)
        print(f"DEBUG: dendro_norm result: {'Success' if dendro_norm else 'None'}")
        
        if dendro_norm:
            story.append(KeepTogether([
                Paragraph("14.1 Similitud Basada en Abundancia Absoluta (Bray-Curtis)", safe_get_style(styles, 'CustomHeading3'))
            ]))
            
            fig1 = create_dendrogram_plot(dendro_norm['linkage_matrix'], dendro_norm['site_names'])
            img_buffer1 = io.BytesIO()
            fig1.savefig(img_buffer1, format='png', dpi=150, bbox_inches='tight')
            img_buffer1.seek(0)
            
            pdf_img1 = Image(img_buffer1, width=6.5*inch, height=3.5*inch)
            story.append(pdf_img1)
            story.append(Spacer(1, 0.1*inch))
            
            nota1 = """
            <para alignment="justify">
            <i>Nota Metodológica:</i> Este agrupamiento utiliza los conteos crudos de abundancia relativa.
            Puede verse fuertemente influenciado por especies muy abundantes o por la diferencia general
            en el número total de registros entre cámaras trampa.
            </para>
            """
            story.append(Paragraph(nota1, safe_get_style(styles, 'Interpretation')))
            story.append(Spacer(1, 0.3*inch))
        
        # 2. Dendrograma Hellinger
        dendro_hell = create_bray_curtis_dendrogram(wildlife_df, transform_hellinger=True)
        print(f"DEBUG: dendro_hell result: {'Success' if dendro_hell else 'None'}")
        
        if dendro_hell:
            story.append(KeepTogether([
                Paragraph("14.2 Similitud Balanceada (Transformación de Hellinger)", safe_get_style(styles, 'CustomHeading3'))
            ]))
            
            fig2 = create_dendrogram_plot(dendro_hell['linkage_matrix'], dendro_hell['site_names'])
            # Quitar el superpuesto suptitle dado por matplotlib y dejar el título natural del canvas
            if hasattr(fig2, '_suptitle') and fig2._suptitle:
                fig2._suptitle.set_text('')
            
            # Forzar limpieza de títulos internos para evitar solapamiento
            for ax in fig2.axes:
                ax.set_title("")
                
            img_buffer2 = io.BytesIO()
            # Ajustar bbox para evitar recortes excesivos o exceso de espacio blanco
            fig2.savefig(img_buffer2, format='png', dpi=150, bbox_inches='tight', pad_inches=0.1)
            img_buffer2.seek(0)
            
            pdf_img2 = Image(img_buffer2, width=6.5*inch, height=3.5*inch)
            story.append(pdf_img2)
            story.append(Spacer(1, 0.1*inch))
            
            nota2 = """
            <para alignment="justify">
            <i>Nota Metodológica:</i> La transformación de Hellinger mitiga el sesgo de las especies extremadamente abundantes 
            y resuelve el problema del "doble cero" (dos sitios no deberían considerarse similares solo porque a ambos les falta 
            la misma especie rara). <b>Este agrupamiento es más robusto y biológicos</b> para comparar comunidades de fauna.
            </para>
            """
            story.append(Paragraph(nota2, safe_get_style(styles, 'Interpretation')))
            
        if not dendro_norm and not dendro_hell:
            story.append(Paragraph("Aviso: No hay suficientes cámaras distintas (mínimo 2) para generar un dendrograma de similitud entre sitios.", styles['BodyText']))
            
    except Exception as e:
        story.append(Paragraph(f"<b>[Análisis de Similitud no disponible]</b><br/>{str(e)}", styles['BodyText']))

    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_cooccurrence_section(story, results, styles):
    """Agrega sección de matriz de co-ocurrencia (Heatmap)"""
    
    story.append(KeepTogether([
        Paragraph("15. MATRIZ DE CO-OCURRENCIA DE ESPECIES", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    co_occ = results.get('co_occurrence', None)
    
    if co_occ is not None and not co_occ.empty:
        try:
            from modules.visualization import create_occupancy_heatmap
            fig = create_occupancy_heatmap(co_occ)
            
            img_bytes = fig.to_image(format="png", width=800, height=800, scale=2)
            img_buffer = io.BytesIO(img_bytes)
            
            pdf_img = Image(img_buffer, width=6.5*inch, height=6.5*inch)
            story.append(pdf_img)
            story.append(Spacer(1, 0.2*inch))
            
            interpretation = """
            <para alignment="justify">
            <b>Interpretación:</b> La matriz térmica (heatmap) indica en cuántas cámaras diferentes dos especies fueron detectadas compartiendo el mismo sitio.
            Valores altos en la diagonal muestran las especies más ampliamente distribuidas, mientras que valores altos fuera de 
            la diagonal indican especies que frecuentemente ocupan los mismos hábitats (posible tolerancia o uso similar de recursos).
            </para>
            """
            story.append(Paragraph(interpretation, safe_get_style(styles, 'Interpretation')))
            
        except Exception as e:
            story.append(Paragraph(f"Error generando mapa de calor: {str(e)}", styles['BodyText']))
    else:
        story.append(Paragraph("No hay suficientes datos para establecer co-ocurrencias entre especies.", styles['BodyText']))
    
    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_temporal_activity_charts_section(story, results, wildlife_df, styles):
    """Agrega gráficas circulares de actividad para todas las especies detectadas"""
    
    story.append(KeepTogether([
        Paragraph("16. GRÁFICAS DE ACTIVIDAD TEMPORAL POR ESPECIE", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    intro = """
    <para alignment="justify">
    Las siguientes gráficas radiales (Densidad Kernel) y lineales ilustran los patrones de actividad diarios registrados para cada especie.
    Las líneas punteadas indican el amanecer y atardecer promedios (06:00 y 18:00 hrs). 
    </para>
    """
    
    nota_forxime = """
    <para alignment="justify">
    <i><b>Nota de Análisis de Solapamiento Temporal:</b> Para evaluar posibles interacciones de competencia, evasión o depredación, los análisis de solapamiento entre pares de especies específicas pueden realizarse de manera interactiva a través del módulo de Patrones Temporales en FORXIME (versión en vivo), donde podrá calcular los coeficientes de Ridout-Linkie.</i>
    </para>
    """
    story.append(KeepTogether([
        Paragraph(intro, styles['BodyText']),
        Spacer(1, 0.05*inch),
        Paragraph(nota_forxime, safe_get_style(styles, 'Interpretation')),
        Spacer(1, 0.2*inch)
    ]))
    
    activity_patterns = results.get('activity_patterns', {})
    
    # Preparar df para la función de gráfica (asume columna Hora)
    if 'Hora' not in wildlife_df.columns:
        if 'Fecha_Captura' in wildlife_df.columns:
            # Usar asignación segura
            wildlife_df = wildlife_df.copy()
            wildlife_df['Hora'] = pd.to_datetime(wildlife_df['Fecha_Captura']).dt.hour + pd.to_datetime(wildlife_df['Fecha_Captura']).dt.minute/60
        elif 'Fecha' in wildlife_df.columns:
            wildlife_df = wildlife_df.copy()
            wildlife_df['Hora'] = pd.to_datetime(wildlife_df['Fecha']).dt.hour + pd.to_datetime(wildlife_df['Fecha']).dt.minute/60

    from modules.visualization import create_activity_pattern_plot
    if 'Eventos_Independientes' in wildlife_df.columns:
        species_counts = wildlife_df.groupby('Especie_Categoria')['Eventos_Independientes'].sum().sort_values(ascending=False)
    else:
        species_counts = wildlife_df['Especie_Categoria'].value_counts().sort_values(ascending=False)
        
    # Removido el filtro de < 3 registros para asegurar que TODAS las especies aparezcan como solicitó el usuario.
    # Solo filtramos si hay 0 registros (lo cual no debería ocurrir con el wildlife_df actual).
    if not species_counts.empty:
        valid_species = species_counts.index.tolist()
    else:
        valid_species = []
    
    if valid_species:
        idx = 1
        for species in valid_species:
            try:
                from modules.pdf_export import format_scientific_name
                formatted_species = format_scientific_name(species)
                
                # Diagnostic Print
                print(f"KALEIDO_DEBUG: Generating charts for {species} (DF rows: {len(wildlife_df)})")
                
                # Obtener figuras por separado
                fig_circ = create_activity_pattern_plot(wildlife_df, species, plot_type='circular')
                fig_lin = create_activity_pattern_plot(wildlife_df, species, plot_type='linear')
                
                if fig_circ and fig_lin:
                    # Generar imágenes ULTRA-OPTIMIZADAS (format='jpeg' y scale=0.8)
                    # El formato JPEG es órdenes de magnitud más pequeño que PNG para este número de gráficas.
                    img_bytes_circ = fig_circ.to_image(format="jpeg", width=400, height=300, scale=0.8)
                    img_bytes_lin = fig_lin.to_image(format="jpeg", width=400, height=250, scale=0.8)
                    
                    print(f"KALEIDO_DEBUG: Success. Bytes: {len(img_bytes_circ)} / {len(img_bytes_lin)}")
                    
                    pdf_img_circ = Image(io.BytesIO(img_bytes_circ), width=3.25*inch, height=2.6*inch)
                    pdf_img_lin = Image(io.BytesIO(img_bytes_lin), width=3.25*inch, height=2.4*inch)
                    
                    # Colocarlas lado a lado empleando una tabla
                    charts_table = Table([[pdf_img_circ, pdf_img_lin]], colWidths=[3.25*inch, 3.25*inch])
                    charts_table.setStyle(TableStyle([
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 10)
                    ]))
                    
                    # COMBINAR TODO EN UN SOLO KEEPTOGETHER PARA EVITAR TÍTULOS HUÉRFANOS
                    elements = [
                        Paragraph(f"16.{idx} Actividad Biológica: {format_scientific_name(species)}", styles['CustomHeading3']),
                        Spacer(1, 0.1*inch),
                        charts_table,
                        Spacer(1, 0.2*inch)
                    ]
                    story.append(KeepTogether(elements))
                    idx += 1
                else:
                    print(f"KALEIDO_DEBUG: SKIP {species} (Fig is None)")
            except Exception as e:
                import traceback
                print(f"ERROR GENERANDO GRÁFICA PARA {species}: {e}")
                traceback.print_exc()

        if idx == 1:
            story.append(Paragraph("No hubo densidad suficiente para generar curvas radiales.", styles['BodyText']))
    else:
        story.append(Paragraph("Las especies detectadas no cuentan con suficientes registros (<3) para estimar densidades Kernel.", styles['BodyText']))

    # story.append(PageBreak()) # Removido para minimizar espacios en blanco
    return story


def add_environmental_covariates_section(story, processed_df, styles):
    """Agrega tabla de covariables ambientales de Google Earth Engine si existen"""
    
    story.append(KeepTogether([
        Paragraph("17. COVARIABLES AMBIENTALES POR CÁMARA", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    # Check for GEE Covariates
    covariate_cols = ['Altitud_m', 'Pendiente_grados', 'NDVI', 'Cobertura_Vegetal_pct', 'Dist_Agua_m', 'Dist_Carretera_m']
    available_covs = [col for col in covariate_cols if col in processed_df.columns]
    
    if not available_covs:
        msg = """
        <para alignment="justify">
        No se extrajeron covariables ambientales espaciales para este proyecto. El módulo integrado de conectividad 
        con Google Earth Engine de TANIA permite recuperar automáticamente datos satelitales topográficos y de 
        vegetación (SRTM, Landsat, Sentinel-2) para todas las estaciones de muestreo reportadas, enriqueciendo 
        los posteriores Modelos de Efectos Mixtos y de Ocupación con covariables.
        </para>
        """
        story.append(Paragraph(msg, styles['BodyText']))
        story.append(PageBreak())
        return story
        
    intro = """
    <para alignment="justify">
    Datos espaciales y ambientales extraídos para cada estación mediante instrumentación de Google Earth Engine.
    Estas covariables dictaminan las variables explicativas durante la confección de modelos logísticos de ocupación ecológica.
    </para>
    """
    story.append(Paragraph(intro, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    try:
        grouped = processed_df.groupby('Camara')[available_covs].median().reset_index()
        
        # Round numeric values for display
        for col in available_covs:
            grouped[col] = grouped[col].round(3)
            
        data = [["Cámara"] + [col.replace("_", " ") for col in available_covs]]
        
        for _, row in grouped.iterrows():
            row_data = [str(row['Camara'])]
            for col in available_covs:
                # Búsqueda insensible a mayúsculas/minúsculas para NDVI y otros
                val = row.get(col, pd.NA)
                
                # Si es NA, buscar en el dataframe original por si acaso
                if pd.isna(val) or val == '':
                    col_lower = col.lower()
                    alt_cols = [c for c in processed_df.columns if c.lower() == col_lower]
                    if alt_cols:
                        val = processed_df[processed_df['Camara'] == row['Camara']][alt_cols[0]].median()

                if pd.notna(val) and val != '':
                    row_data.append(f"{float(val):.3f}" if isinstance(val, (float, int)) else str(val))
                else:
                    row_data.append("N/D")
            data.append(row_data)
            
        # Calibrar anchos de columnas
        n_cols = len(data[0])
        col_widths = [1.2*inch] + [(6.5 - 1.2)/len(available_covs)*inch] * len(available_covs)
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), safe_get_style(styles, 'CustomHeading3').fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
        ]))
        
        story.append(table)
    except Exception as e:
        story.append(Paragraph(f"Error procesando covariables: {str(e)}", styles['BodyText']))

    story.append(PageBreak())
    return story

def add_covariate_analysis_section(story, results, styles):
    """Agrega sección de análisis de ocupación con covariables"""
    cov_results = results.get('covariate_analysis', {})
    if not cov_results:
        return story

    story.append(KeepTogether([
        Paragraph("18. ANÁLISIS COVARIADO DE OCUPACIÓN (RIDGE REGRESSION)", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch),
        Paragraph("Esta sección presenta el efecto de las covariables ambientales sobre la probabilidad de ocupación (Psi). Se utilizó un modelo de regresión logística con regularización Ridge para evitar sobreajuste y divergencia en casos de baja detectabilidad.", safe_get_style(styles, 'Normal'))
    ]))
    
    for sp, data in cov_results.items():
        if not data.get('success'): continue
        
        formatted_sp = format_scientific_name(sp)
        story.append(KeepTogether([
            Paragraph(f"18.{list(cov_results.keys()).index(sp)+1} Modelo para {formatted_sp}", safe_get_style(styles, 'CustomHeading3')),
            Spacer(1, 0.1*inch)
        ]))
        
        # Tabla de coeficientes
        coef_df = data.get('coef_table', pd.DataFrame())
        if not coef_df.empty:
            table_data = [['Variable', 'Beta', 'Err.Est', 'OR', 'p-valor']]
            for _, row in coef_df.iterrows():
                table_data.append([
                    row['Covariable'],
                    f"{row['Beta']:.3f}",
                    f"{row['SE']:.3f}",
                    f"{row['Odds_Ratio']:.3f}",
                    f"{row['p_valor']:.4f}"
                ])
            
            t = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            
            # Interpretaciones
            interpretations = data.get('interpretations', [])
            for inter in interpretations:
                story.append(Paragraph(f"• {inter}", safe_get_style(styles, 'Normal')))
            
            story.append(Spacer(1, 0.2*inch))
            
    return story

def add_biogeography_detailed_section(story, results, styles):
    """Agrega sección detallada de biogeografía y estatus legal"""
    assessment = results.get('species_assessment', {})
    if not assessment:
        return story
        
    story.append(KeepTogether([
        Paragraph("19. ESTATUS BIOGEOGRÁFICO Y LEGAL", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    table_data = [['Especie', 'NOM-059 (Méx)', 'IUCN', 'Biogeografía']]
    for sp, info in assessment.items():
        table_data.append([
            Paragraph(format_scientific_name(sp), safe_get_style(styles, 'Normal')),
            info['nom_059'],
            info['iucn'],
            info['biogeographic']
        ])
        
    t = Table(table_data, colWidths=[2.2*inch, 1.5*inch, 1*inch, 1.3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*inch))
    return story

def add_species_fact_sheets(story, results, styles):
    """Agrega fichas técnicas individuales por especie"""
    fact_sheets = results.get('species_fact_sheets', {})
    if not fact_sheets:
        return story
        
    story.append(KeepTogether([
        Paragraph("20. FICHAS TÉCNICAS DE ESPECIES DETECTADAS", safe_get_style(styles, 'CustomHeading2')),
        Spacer(1, 0.2*inch)
    ]))
    
    for sp, data in fact_sheets.items():
        story.append(KeepTogether([
            Paragraph(format_scientific_name(sp), safe_get_style(styles, 'CustomHeading3')),
            Spacer(1, 0.05*inch)
        ]))
        
        try:
            peak_val = data.get('peak_activity')
            if peak_val is not None:
                # Si es un string de tipo HH:MM:SS, extraer solo la hora
                if isinstance(peak_val, str) and ':' in peak_val:
                    peak_h = f"{int(peak_val.split(':')[0]):02d}:00h"
                else:
                    peak_h = f"{int(float(peak_val)):02d}:00h"
            else:
                peak_h = 'N/A'
        except:
            peak_h = 'N/A'
        
        info_text = f"""
        <b>Registros Totales:</b> {data['records']} | 
        <b>Sitios Ocupados:</b> {data['sites']} | 
        <b>Detección Inicial:</b> {data['first_detection'].strftime('%Y-%m-%d') if data['first_detection'] else 'N/A'} | 
        <b>Última Detección:</b> {data['last_detection'].strftime('%Y-%m-%d') if data['last_detection'] else 'N/A'} | 
        <b>Hora Pico:</b> {peak_h}
        """
        story.append(Paragraph(info_text, safe_get_style(styles, 'Normal')))
        story.append(Spacer(1, 0.15*inch))
        
    return story


