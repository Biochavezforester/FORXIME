"""
Módulo de exportación a PDF para FORXIME/2
Genera reportes profesionales completos listos para artículos científicos y planes de manejo
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
                                 PageBreak, Image, KeepTogether, Frame, PageTemplate)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import os
import plotly.io as pio
from PIL import Image as PILImage


class PDFReportGenerator:
    """Generador de reportes PDF profesionales para FORXIME/2"""
    
    def __init__(self, logo_path=None):
        self.logo_path = logo_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos de nivel 3
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1B5E20'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto justificado
        self.styles.add(ParagraphStyle(
            name='Justified',
            parent=self.styles['BodyText'],
            alignment=TA_JUSTIFY,
            fontSize=11,
            leading=14
        ))
        
        # Estilo para interpretaciones
        self.styles.add(ParagraphStyle(
            name='Interpretation',
            parent=self.styles['BodyText'],
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=13,
            leftIndent=20,
            rightIndent=20,
            textColor=colors.HexColor('#424242'),
            backColor=colors.HexColor('#F5F5F5'),
            borderPadding=10
        ))
        
        # Estilo para métricas
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['BodyText'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2E7D32')
        ))
    
    def _add_header_footer(self, canvas, doc):
        """Agrega encabezado y pie de página a cada página"""
        canvas.saveState()
        
        # Encabezado con logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                canvas.drawImage(self.logo_path, 0.5*inch, letter[1] - 0.8*inch, 
                               width=1.5*inch, height=0.6*inch, preserveAspectRatio=True)
            except:
                pass
        
        # Línea separadora del encabezado
        canvas.setStrokeColor(colors.HexColor('#2E7D32'))
        canvas.setLineWidth(2)
        canvas.line(0.5*inch, letter[1] - 0.9*inch, letter[0] - 0.5*inch, letter[1] - 0.9*inch)
        
        # Pie de página
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        
        # Número de página
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.drawRightString(letter[0] - 0.5*inch, 0.5*inch, text)
        
        # Créditos en pie de página
        canvas.drawString(0.5*inch, 0.5*inch, "FORXIME/2 - Plataforma de Análisis de Cámaras Trampa")
        
        canvas.restoreState()
    
    def _create_cover_page(self):
        """Crea la portada del reporte"""
        story = []
        
        # Espaciado superior
        story.append(Spacer(1, 2*inch))
        
        # Logo grande en portada (proporción corregida)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Mantener proporción del logo (2.5:1 aproximadamente)
                img = Image(self.logo_path, width=2.5*inch, height=1*inch, kind='proportional')
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 0.5*inch))
            except:
                pass
        
        # Título principal
        title = Paragraph("REPORTE DE ANÁLISIS<br/>CÁMARAS TRAMPA", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Subtítulo (centrado)
        subtitle_style = ParagraphStyle(
            name='CenteredSubtitle',
            parent=self.styles['Heading2'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.HexColor('#1B5E20')
        )
        subtitle = Paragraph("Análisis Estadístico de Biodiversidad y Patrones Ecológicos", subtitle_style)
        story.append(subtitle)
        story.append(Spacer(1, 1*inch))
        
        # Información del reporte
        fecha = datetime.now().strftime("%d de %B de %Y")
        meses = {
            'January': 'enero', 'February': 'febrero', 'March': 'marzo',
            'April': 'abril', 'May': 'mayo', 'June': 'junio',
            'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
            'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
        }
        for eng, esp in meses.items():
            fecha = fecha.replace(eng, esp)
        
        info_text = f"""
        <para alignment="center">
        <b>Fecha de generación:</b> {fecha}<br/>
        <b>Plataforma:</b> FORXIME/2<br/>
        <b>Versión:</b> 2.0
        </para>
        """
        story.append(Paragraph(info_text, self.styles['BodyText']))
        
        story.append(PageBreak())  # Separar portada de créditos
        return story
    
    def _create_credits_page(self):
        """Crea la página de créditos"""
        story = []
        
        story.append(Paragraph("CRÉDITOS Y DESARROLLO", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.3*inch))
        
        credits_text = """
        <para alignment="justify">
        <b>Desarrollador:</b><br/>
        Biólogo Erick Elio Chavez Gurrola<br/><br/>
        
        <b>ORCID:</b> 0009-0007-7054-6999<br/>
        <b>ResearchGate:</b> https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2<br/>
        <b>Email:</b> eliogurrola5@gmail.com<br/><br/>
        
        <b>Acerca de FORXIME/2:</b><br/>
        FORXIME/2 (Fauna Observada y Registrada + Índices de Monitoreo Estadístico) es una plataforma 
        desarrollada para facilitar el análisis estadístico de datos de cámaras trampa. La plataforma 
        implementa las mejores prácticas científicas y estadísticas disponibles para el estudio de 
        biodiversidad, patrones de actividad temporal, y evaluación de impacto antropogénico.<br/><br/>
        
        Esta herramienta ha sido diseñada específicamente para simplificar el análisis de sitios 
        simples y pareados, proporcionando resultados robustos y científicamente válidos que pueden 
        ser utilizados en publicaciones científicas, informes técnicos, y planes de manejo.<br/><br/>
        
        <b>Citación sugerida:</b><br/>
        Chavez Gurrola, E.E. (2026). FORXIME/2: Plataforma de Análisis de Datos de Cámaras Trampa. 
        Versión 2.0. [Software]. Disponible en: https://forxime2-0.streamlit.app/
        </para>
        """
        story.append(Paragraph(credits_text, self.styles['Justified']))
        
        story.append(PageBreak())  # Separar créditos de resumen ejecutivo
        return story
    
    def _create_legal_disclaimer(self):
        """Crea la página de descargo de responsabilidad legal"""
        story = []
        
        story.append(Paragraph("AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.3*inch))
        
        disclaimer_text = """
        <para alignment="justify">
        <b>⚠️ AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD</b><br/><br/>
        
        Esta plataforma ha sido desarrollada por el Biólogo Erick Elio Chavez Gurrola para facilitar 
        el análisis estadístico de datos de cámaras trampa. Si bien se han implementado las mejores 
        prácticas científicas disponibles, los resultados pueden contener errores o imprecisiones.<br/><br/>
        
        <b>Responsabilidad del usuario:</b> Validar resultados antes de su uso, verificar coherencia de 
        análisis, interpretar correctamente en contexto, no utilizar sin revisión previa en publicaciones 
        o toma de decisiones, asegurar calidad de datos de entrada, y comprender limitaciones de métodos 
        estadísticos.<br/><br/>
        
        <b>Limitaciones:</b> Los análisis asumen independencia de observaciones, dependen de calidad de 
        datos, requieren tamaños de muestra mínimos, y las interpretaciones automáticas son orientativas.<br/><br/>
        
        <b>Recomendaciones:</b> Consulte expertos antes de publicar, verifique supuestos estadísticos, 
        compare con software alternativo, y documente decisiones metodológicas.<br/><br/>
        
        <b>Exención:</b> El desarrollador no se responsabiliza por decisiones de manejo, errores en 
        publicaciones, pérdidas económicas, o interpretaciones incorrectas derivadas del uso de esta 
        herramienta.<br/><br/>
        
        <b>Contacto:</b> eliogurrola5@gmail.com | ResearchGate: Erick Elio Chavez Gurrola<br/><br/>
        
        Al utilizar esta plataforma, el usuario acepta estos términos y reconoce su responsabilidad en 
        la validación e interpretación de resultados.
        </para>
        """
        story.append(Paragraph(disclaimer_text, self.styles['Justified']))
        
        return story
    
    def plotly_to_image(self, fig, width=700, height=500):
        """Convierte una figura de Plotly a imagen para incluir en PDF"""
        try:
            img_bytes = pio.to_image(fig, format='png', width=width, height=height, engine='kaleido')
            img = PILImage.open(BytesIO(img_bytes))
            
            # Guardar en buffer
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Crear objeto Image de ReportLab
            return Image(img_buffer, width=6*inch, height=4*inch)
        except Exception as e:
            # Si falla, retornar un placeholder
            return Paragraph(f"[Gráfica no disponible: {str(e)}]", self.styles['BodyText'])
    
    def _add_biodiversity_section(self, story, results):
        """Agrega sección de biodiversidad al reporte"""
        story.append(Paragraph("1. ANÁLISIS DE BIODIVERSIDAD", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # Índices de biodiversidad
        biodiv = results.get('biodiversity', {})
        
        story.append(Paragraph("1.1 Índices de Diversidad", self.styles['CustomHeading3']))
        
        # Tabla de índices
        indices_data = [
            ['Índice', 'Valor', 'Interpretación'],
            ['Shannon (H\')', f"{biodiv.get('Shannon', 0):.3f}", 'Diversidad general'],
            ['Simpson (D)', f"{biodiv.get('Simpson', 0):.3f}", 'Dominancia'],
            ['Riqueza (S)', str(biodiv.get('Richness', 0)), 'Número de especies'],
            ['Equitatividad de Pielou (J\')', f"{biodiv.get('Pielou_Evenness', 0):.3f}", 'Uniformidad']
        ]
        
        indices_table = Table(indices_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
        indices_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(indices_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Biodiversidad por sitio
        if 'biodiversity_by_site' in results:
            story.append(Paragraph("1.2 Biodiversidad por Sitio", self.styles['CustomHeading3']))
            
            biodiv_site = results['biodiversity_by_site']
            if not biodiv_site.empty:
                # Convertir DataFrame a lista para tabla
                site_data = [list(biodiv_site.columns)]
                for _, row in biodiv_site.iterrows():
                    site_data.append([str(val) if not isinstance(val, float) else f"{val:.3f}" 
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
                story.append(Spacer(1, 0.2*inch))
        
        # Interpretación de biodiversidad
        shannon = biodiv.get('Shannon', 0)
        simpson = biodiv.get('Simpson', 0)
        pielou = biodiv.get('Pielou_Evenness', 0)
        
        interpretation = f"""
        <para alignment="justify">
        <b>Interpretación:</b> El índice de Shannon ({shannon:.3f}) indica una diversidad 
        {'alta' if shannon > 2.5 else 'moderada' if shannon > 1.5 else 'baja'}, mientras que el índice de 
        Simpson ({simpson:.3f}) sugiere {'baja' if simpson < 0.3 else 'moderada' if simpson < 0.6 else 'alta'} 
        dominancia de pocas especies. La equitatividad de Pielou ({pielou:.3f}) revela una distribución 
        {'uniforme' if pielou > 0.7 else 'moderadamente uniforme' if pielou > 0.5 else 'desigual'} de las 
        especies en el área. Estos valores son indicativos de {'un ecosistema saludable con buena representación de especies' if shannon > 2.0 and pielou > 0.6 else 'un ecosistema con diversidad moderada que podría beneficiarse de acciones de conservación' if shannon > 1.5 else 'un ecosistema con baja diversidad que requiere atención inmediata'}.
        </para>
        """
        story.append(Paragraph(interpretation, self.styles['Interpretation']))
        story.append(Spacer(1, 0.2*inch))
        
        # story.append(PageBreak())  # Las secciones H2 inician página automáticamente
        return story
    
    def _add_abundance_section(self, story, results):
        """Agrega sección de abundancia relativa"""
        story.append(Paragraph("2. ABUNDANCIA RELATIVA (RAI)", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.2*inch))
        
        rai_df = results.get('rai', pd.DataFrame())
        
        if not rai_df.empty:
            # Filtrar categorías no deseadas (Vacías, etc.)
            rai_filtered = rai_df[~rai_df['Especie'].str.contains('Vac[ií]', case=False, na=False)]
            
            # Top 10 especies (excluyendo vacías)
            top_species = rai_filtered.head(10)
            
            rai_data = [['Especie', 'Eventos', 'Días-Trampa', 'RAI']]
            for _, row in top_species.iterrows():
                rai_data.append([
                    str(row.get('Especie', '')),
                    str(int(row.get('Eventos_Independientes', 0))),
                    str(int(row.get('Dias_Trampa', 0))),
                    f"{row.get('RAI', 0):.2f}"
                ])
            
            rai_table = Table(rai_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            rai_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(Paragraph("Top 10 Especies por Abundancia Relativa", self.styles['CustomHeading3']))
            story.append(rai_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Interpretación
            if len(top_species) > 0:
                top_sp = top_species.iloc[0]
                interpretation = f"""
                <para alignment="justify">
                <b>Interpretación:</b> La especie más abundante detectada fue <b>{top_sp.get('Especie', 'N/A')}</b> 
                con un RAI de {top_sp.get('RAI', 0):.2f}, lo que indica {'alta' if top_sp.get('RAI', 0) > 10 else 'moderada' if top_sp.get('RAI', 0) > 5 else 'baja'} 
                frecuencia de detección. Las especies con mayor RAI suelen ser las más abundantes o las que tienen 
                mayor movilidad en el área de estudio. Es importante considerar que el RAI no representa densidad 
                poblacional absoluta, sino una medida relativa de actividad y detectabilidad.
                </para>
                """
                story.append(Paragraph(interpretation, self.styles['Interpretation']))
                story.append(Spacer(1, 0.2*inch))
            
            # Nota metodológica
            note = """
            <para alignment="justify">
            <b>Nota metodológica:</b> El Índice de Abundancia Relativa (RAI) se calcula como 
            (Eventos Independientes / Días-Trampa) × 100. Este índice permite comparar la 
            abundancia relativa entre especies y sitios, estandarizado por el esfuerzo de muestreo.
            Las categorías no relacionadas con fauna silvestre (ej. "Vacías") han sido excluidas de este análisis.
            </para>
            """
            story.append(Paragraph(note, self.styles['Justified']))
        
        # story.append(PageBreak())  # Las secciones H2 inician página automáticamente
        return story
    
    def _add_sampling_section(self, story, results):
        """Agrega sección de evaluación de muestreo"""
        story.append(Paragraph("3. EVALUACIÓN DEL MUESTREO", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.2*inch))
        
        effort = results.get('sampling_effort', pd.DataFrame())
        
        if not effort.empty:
            story.append(Paragraph("3.1 Esfuerzo de Muestreo por Cámara", self.styles['CustomHeading3']))
            
            effort_data = [['Cámara', 'Días-Trampa', 'Riqueza', 'Eventos', 'Clasificación']]
            for _, row in effort.iterrows():
                effort_data.append([
                    str(row.get('Camara', '')),
                    str(int(row.get('Dias_Trampa', 0))),
                    str(int(row.get('Riqueza', 0))),
                    str(int(row.get('Total_Eventos', 0))),
                    str(row.get('Clasificacion_Esfuerzo', ''))
                ])
            
            effort_table = Table(effort_data)
            effort_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(effort_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Recomendaciones
        recommendations = results.get('sampling_recommendations', [])
        if recommendations:
            story.append(Paragraph("3.2 Recomendaciones de Muestreo", self.styles['CustomHeading3']))
            
            for rec in recommendations[:5]:  # Top 5 recomendaciones
                priority = rec.get('priority', 'Media')
                category = rec.get('category', '')
                recommendation = rec.get('recommendation', '')
                
                rec_text = f"""
                <para>
                <b>[{priority}] {category}:</b><br/>
                {recommendation}
                </para>
                """
                story.append(Paragraph(rec_text, self.styles['Justified']))
                story.append(Spacer(1, 0.1*inch))
        
        # story.append(PageBreak())  # Las secciones H2 inician página automáticamente
        return story
    
    def _add_temporal_patterns_section(self, story, results):
        from modules.pdf_sections_helper import add_temporal_patterns_section
        return add_temporal_patterns_section(story, results, self.styles)
    
    def _add_anthropogenic_section(self, story, results):
        from modules.pdf_sections_helper import add_anthropogenic_section
        return add_anthropogenic_section(story, results, self.styles)
    
    def _add_conservation_section(self, story, results):
        from modules.pdf_sections_helper import add_conservation_section
        return add_conservation_section(story, results, self.styles)
    
    def _add_hunting_section(self, story, results):
        from modules.pdf_sections_helper import add_hunting_section
        return add_hunting_section(story, results, self.styles)
    
    def _add_livestock_section(self, story, results):
        """Agrega sección de manejo ganadero"""
        from modules.pdf_sections_helper import add_livestock_management_section
        return add_livestock_management_section(story, results, self.styles)
    
    
    def generate_complete_report(self, results, wildlife_df, processed_df, language='es'):
        """
        Genera el reporte PDF completo
        
        Args:
            results: Diccionario con todos los resultados del análisis
            wildlife_df: DataFrame con datos de fauna silvestre
            processed_df: DataFrame con datos procesados
            language: Idioma del reporte ('es' o 'en')
        
        Returns:
            BytesIO: Buffer con el PDF generado
        """
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Historia del documento
        story = []
        
        # 1. Portada
        story.extend(self._create_cover_page())
        
        # 2. Créditos
        story.extend(self._create_credits_page())
        
        # 3. Resumen ejecutivo
        story.append(Paragraph("RESUMEN EJECUTIVO", self.styles['CustomHeading2']))
        story.append(Spacer(1, 0.2*inch))
        
        basic_metrics = results.get('basic_metrics', {})
        biodiv = results.get('biodiversity', {})
        
        # Resumen ejecutivo expandido (~1 cuartilla)
        summary_text = f"""
        <para alignment="justify">
        Este reporte presenta los resultados del análisis de datos de cámaras trampa procesados 
        mediante la plataforma FORXIME/2. El estudio registró un total de <b>{basic_metrics.get('total_records', 0)} 
        observaciones</b> de fauna silvestre, distribuidas en <b>{basic_metrics.get('total_cameras', 0)} cámaras</b> 
        ubicadas en <b>{basic_metrics.get('total_sites', 0)} sitios</b> de muestreo. Se identificaron 
        <b>{basic_metrics.get('total_species', 0)} especies o categorías</b> diferentes.<br/><br/>
        
        <b>Biodiversidad:</b> El análisis de biodiversidad reveló un índice de Shannon de {biodiv.get('Shannon', 0):.3f}, 
        indicando {'alta' if biodiv.get('Shannon', 0) > 2.5 else 'moderada' if biodiv.get('Shannon', 0) > 1.5 else 'baja'} 
        diversidad en el área de estudio. El índice de Simpson fue de {biodiv.get('Simpson', 0):.3f}, mientras que 
        la equitatividad de Pielou alcanzó {biodiv.get('Pielou_Evenness', 0):.3f}, lo que sugiere una distribución 
        {'uniforme' if biodiv.get('Pielou_Evenness', 0) > 0.7 else 'moderadamente uniforme' if biodiv.get('Pielou_Evenness', 0) > 0.5 else 'desigual'} 
        de las especies en el área.<br/><br/>
        
        <b>Metodología:</b> Los análisis incluyen evaluación de biodiversidad mediante índices de diversidad, 
        cálculo de abundancia relativa (RAI), análisis de patrones de actividad temporal, evaluación de impacto 
        antropogénico, identificación de prioridades de conservación, y recomendaciones de manejo. Todos los 
        análisis fueron realizados siguiendo las mejores prácticas científicas y estadísticas disponibles, 
        incluyendo el uso de eventos independientes (intervalo mínimo de 30 minutos entre registros de la misma 
        especie) para evitar sesgos por autocorrelación temporal.<br/><br/>
        
        <b>Esfuerzo de muestreo:</b> El esfuerzo total de muestreo alcanzó {basic_metrics.get('total_trap_days', 0)} 
        días-trampa, con un promedio de {basic_metrics.get('avg_days_per_camera', 0):.1f} días por cámara. 
        Este esfuerzo permitió obtener resultados estadísticamente robustos para la mayoría de las especies 
        detectadas.<br/><br/>
        
        <b>Hallazgos principales:</b> Los resultados de este estudio proporcionan información valiosa para la 
        toma de decisiones en materia de conservación y manejo de fauna silvestre. Las secciones subsecuentes 
        detallan los análisis específicos, interpretaciones ecológicas, y recomendaciones de manejo basadas 
        en los datos recopilados.
        </para>
        """
        story.append(Paragraph(summary_text, self.styles['Justified']))
        # story.append(PageBreak())  # Las secciones H2 inician página automáticamente
        
        # 4. Secciones de resultados
        story = self._add_biodiversity_section(story, results)
        story = self._add_abundance_section(story, results)
        story = self._add_temporal_patterns_section(story, results)
        story = self._add_anthropogenic_section(story, results)
        story = self._add_sampling_section(story, results)
        story = self._add_conservation_section(story, results)
        story = self._add_livestock_section(story, results)
        story = self._add_hunting_section(story, results)
        
        # 5. Descargo de responsabilidad legal (última página)
        story.extend(self._create_legal_disclaimer())
        
        # Construir PDF con encabezado y pie de página
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer


def generate_pdf_report(results, wildlife_df, processed_df, language='es', logo_path=None):
    """
    Función helper para generar el reporte PDF
    
    Args:
        results: Diccionario con resultados del análisis
        wildlife_df: DataFrame con datos de fauna
        processed_df: DataFrame con datos procesados
        language: Idioma ('es' o 'en')
        logo_path: Ruta al logo (opcional)
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generator = PDFReportGenerator(logo_path=logo_path)
    return generator.generate_complete_report(results, wildlife_df, processed_df, language)
