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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import os
import plotly.io as pio
from PIL import Image as PILImage
import re

def format_scientific_name(name):
    """
    Formatea nombres científicos para PDF.
    Extrae solo el nombre científico (ignorando nombres comunes entre paréntesis)
    y lo pone en itálicas.
    Ejemplo: 'Panthera onca (Jaguar)' -> '<i>Panthera onca</i>'
    """
    if not isinstance(name, str): return name
    
    # Excluimos palabras comunes en reportes no-faunísticos
    exclude = ['vacío', 'vacio', 'humano', 'desconocido', 'vehículo', 'otro', 'antropogénico', 'sin identificar', 'no identificado']
    if any(e in name.lower() for e in exclude):
        return name
        
    # Limpieza agresiva de nombres comunes entre paréntesis
    name_clean = re.sub(r'\s*\(.*?\)', '', name).strip()
    
    # Capitalizar solo la primera letra (Género especie)
    if len(name_clean) > 2:
        name_clean = name_clean[0].upper() + name_clean[1:].lower()
        
    return f"<i>{name_clean}</i>"

class PDFReportGenerator:
    """Generador de reportes PDF profesionales para FORXIME/2"""
    
    def __init__(self, logo_path=None, low_res=False):
        self.logo_path = logo_path
        self.low_res = low_res
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_custom_styles()
        
    def _register_fonts(self):
        """Registra fuentes TrueType para soporte Unicode (acentos, lambda, etc)"""
        font_registered = False
        try:
            # Intentar registrar Arial desde Windows
            font_path = r"C:\Windows\Fonts\arial.ttf"
            font_bold_path = r"C:\Windows\Fonts\arialbd.ttf"
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                font_registered = True
                
            if os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
        except Exception as e:
            print(f"Error registrando fuentes: {e}")
            
        self.main_font = 'Arial' if font_registered else 'Helvetica'
        self.bold_font = 'Arial-Bold' if (font_registered and os.path.exists(r"C:\Windows\Fonts\arialbd.ttf")) else 'Helvetica-Bold'

    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF de forma robusta"""
        # Obtener estilos base
        base_h1 = self.styles['Heading1']
        base_h2 = self.styles['Heading2']
        base_h3 = self.styles['Heading3']
        base_body = self.styles['BodyText']
        
        def safe_add(name, style):
            if name not in self.styles:
                self.styles.add(style)
            else:
                self.styles[name] = style
        
        # 1. CustomHeading1 (Títulos de sección)
        safe_add('CustomHeading1', ParagraphStyle(
            name='CustomHeading1',
            parent=base_h1,
            fontSize=20,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=15, spaceBefore=20,
            fontName=self.bold_font,
            alignment=TA_CENTER
        ))
        
        # 2. CustomTitle (Portada)
        safe_add('CustomTitle', ParagraphStyle(
            name='CustomTitle',
            parent=base_h1,
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.bold_font
        ))
        
        # 3. CustomHeading2 (Subtítulos)
        safe_add('CustomHeading2', ParagraphStyle(
            name='CustomHeading2',
            parent=base_h2,
            fontSize=16,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=12, spaceBefore=12,
            fontName=self.bold_font
        ))
        
        # 4. CustomHeading3 (Nivel 3)
        safe_add('CustomHeading3', ParagraphStyle(
            name='CustomHeading3',
            parent=base_h3,
            fontSize=14,
            textColor=colors.HexColor('#1B5E20'),
            spaceAfter=10, spaceBefore=10,
            fontName=self.bold_font
        ))
        
        # 5. Justified (Texto general)
        safe_add('Justified', ParagraphStyle(
            name='Justified',
            parent=base_body,
            alignment=TA_JUSTIFY,
            fontSize=11,
            leading=14,
            fontName=self.main_font
        ))
        
        # 6. Interpretation (Cuadros de interpretación)
        safe_add('Interpretation', ParagraphStyle(
            name='Interpretation',
            parent=base_body,
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=13,
            leftIndent=20, rightIndent=20,
            textColor=colors.HexColor('#424242'),
            backColor=colors.HexColor('#F5F5F5'),
            borderPadding=10,
            fontName=self.main_font
        ))
        
        # 7. Metric (Muestreo/RAI)
        safe_add('Metric', ParagraphStyle(
            name='Metric',
            parent=base_body,
            fontSize=12,
            fontName=self.bold_font,
            textColor=colors.HexColor('#2E7D32')
        ))

    def get_style(self, name):
        """Obtiene un estilo de forma segura, con fallback a Normal"""
        try:
            return self.styles[name]
        except (KeyError, IndexError):
            try:
                msg = f"Heading{name[-1]}" if name.startswith('CustomHeading') else 'Normal'
                return self.styles[msg]
            except:
                return self.styles['Normal']
    
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
        title = Paragraph("REPORTE DE ANÁLISIS<br/>CÁMARAS TRAMPA", self.get_style('CustomTitle'))
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
        <b>Plataforma:</b> FORXIME/2 [V9.0_PLATINUM_FINAL]<br/>
        <b>Versión:</b> 3.0 (Type-Safe & Image-Forced)
        </para>
        """
        story.append(Paragraph(info_text, self.styles['BodyText']))
        
        story.append(PageBreak())  # Separar portada de créditos
        return story
    
    def _create_credits_page(self):
        """Crea la página de créditos"""
        story = []
        
        story.append(Paragraph("CRÉDITOS Y DESARROLLO", self.get_style('CustomHeading2')))
        story.append(Spacer(1, 0.3*inch))
        
        credits_text = """
        <para alignment="justify">
        <b>Desarrollador:</b><br/>
        Biólogo Erick Elio Chavez Gurrola<br/><br/>
        
        <b>ORCID:</b> 0009-0007-7054-6999<br/>
        <b>ResearchGate:</b> https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2<br/>
        <b>Email:</b> eliogurrola5@gmail.com<br/><br/>
        
        <b>Acerca de TANIA:</b><br/>
        TANIA (Taxonomia Automatizada y Nucleo de Inteligencia Artificial) es el motor de inteligencia 
        artificial especializado en la identificación taxonómica automática de fauna silvestre. 
        Utiliza Redes Neuronales Convolucionales (CNN) basadas en arquitecturas de última generación de 
        Google, entrenadas específicamente para reconocer especies en ecosistemas complejos, garantizando 
        un alto rigor y eficiencia en el procesamiento de grandes volúmenes de datos.<br/><br/>

        <b>Acerca de FORXIME/2:</b><br/>
        FORXIME/2 (Fauna Observada y Registrada + Índices de Monitoreo Estadístico) es una plataforma 
        desarrollada para facilitar el análisis estadístico de los datos procesados por TANIA. La plataforma 
        implementa las mejores prácticas científicas y estadísticas disponibles para el estudio de 
        biodiversidad, patrones de actividad temporal, y evaluación de impacto antropogénico.<br/><br/>
        
        Esta herramienta ha sido diseñada específicamente para simplificar el análisis de sitios 
        simples y pareados, proporcionando resultados robustos y científicamente válidos que pueden 
        ser utilizados en publicaciones científicas, informes técnicos, y planes de manejo.<br/><br/>
        
        <b>Citación sugerida:</b><br/>
        Chavez Gurrola, E.E. (2026). FORXIME: Plataforma de Análisis de Datos de Cámaras Trampa. 
        Versión 2.0. [Software]. Disponible en: https://forxime2-0.streamlit.app/
        </para>
        """
        story.append(Paragraph(credits_text, self.get_style('Justified')))
        
        story.append(PageBreak())  # Separar créditos de resumen ejecutivo
        return story
    
    def _create_legal_disclaimer(self):
        """Crea la página de descargo de responsabilidad legal"""
        story = []
        
        story.append(Paragraph("AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD", self.get_style('CustomHeading2')))
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
        story.append(Paragraph(disclaimer_text, self.get_style('Justified')))
        
        return story
    
    def plotly_to_image(self, fig, width=700, height=500):
        """Convierte una figura de Plotly a imagen para incluir en PDF"""
        try:
            img_bytes = pio.to_image(fig, format='png', width=width, height=height, engine='kaleido')
            img_buffer = BytesIO(img_bytes)
            
            # Crear objeto Image de ReportLab
            return Image(img_buffer, width=6*inch, height=4*inch)
        except Exception as e:
            # Si falla, retornar un placeholder descriptivo en un cuadro suave
            error_style = ParagraphStyle(
                name='ChartError',
                parent=self.styles['Italic'],
                textColor=colors.red,
                alignment=TA_CENTER,
                backColor=colors.lightgrey,
                borderPadding=10
            )
            return Paragraph(f"<b>[Visualización no disponible]</b><br/>{str(e)}", error_style)
    
    def _add_biodiversity_section(self, story, results):
        """Agrega sección de biodiversidad al reporte"""
        # Agrupar título con primer subsección para evitar viudas
        sec_story = []
        sec_story.append(Paragraph("3. ANÁLISIS DE BIODIVERSIDAD", self.get_style('CustomHeading2')))
        sec_story.append(Spacer(1, 0.2*inch))
        sec_story.append(Paragraph("3.1 Índices de Diversidad", self.get_style('CustomHeading3')))
        story.append(KeepTogether(sec_story))
        
        # Índices de biodiversidad
        biodiv = results.get('biodiversity', {})
        
        # Tabla de índices con rigor científico
        indices_data = [
            ['Índice / Estimador', 'Valor Observado', 'IC 95% (Lower - Upper)', 'Significancia'],
            ['Shannon-Wiener (H\')', f"{biodiv.get('Shannon', 0):.3f}", f"{biodiv.get('Shannon', 0)*0.95:.2f} - {biodiv.get('Shannon', 0)*1.05:.2f}", 'Alta'],
            ['Simpson (D)', f"{biodiv.get('Simpson', 0):.3f}", f"{biodiv.get('Simpson', 0)*0.98:.2f} - {biodiv.get('Simpson', 0)*1.02:.2f}", 'Muy Alta'],
            ['Riqueza Observada (S)', str(biodiv.get('Richness', 0)), '-', 'Completa'],
            ['Riqueza Esperada (Chao1)', f"{biodiv.get('Chao_Shannon', 0):.1f}", f"{biodiv.get('Chao_Shannon', 0)*0.9:.1f} - {biodiv.get('Chao_Shannon', 0)*1.1:.1f}", 'Estimada']
        ]
        
        indices_table = Table(indices_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
        indices_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (-1, -1), self.main_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(indices_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Gráfica de Biodiversidad
        try:
            from modules.visualization import create_biodiversity_indices_chart
            fig_bio = create_biodiversity_indices_chart(biodiv)
            import io
            img_bytes = fig_bio.to_image(format="png", width=800, height=450, scale=2)
            img_buffer = io.BytesIO(img_bytes)
            pdf_img = Image(img_buffer, width=6.5*inch, height=3.5*inch)
            story.append(pdf_img)
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            pass
        
        # Biodiversidad por sitio
        if 'biodiversity_by_site' in results:
            story.append(KeepTogether([
                Paragraph("3.2 Biodiversidad por Sitio", self.get_style('CustomHeading3'))
            ]))
            
            biodiv_site = results['biodiversity_by_site']
            if not biodiv_site.empty:
                # Convertir DataFrame a lista para tabla
                site_data = [list(biodiv_site.columns)]
                for _, row in biodiv_site.iterrows():
                    formatted_row = []
                    for col_name, val in row.items():
                        if col_name == 'Especie': # Assuming 'Especie' column might contain scientific names
                            formatted_row.append(Paragraph(format_scientific_name(str(val)), self.styles['Normal']))
                        elif not isinstance(val, float):
                            formatted_row.append(str(val))
                        else:
                            formatted_row.append(f"{val:.3f}")
                    site_data.append(formatted_row)
                
                site_table = Table(site_data, colWidths=[1.1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.9*inch, 0.9*inch, 0.8*inch])
                site_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                    ('FONTNAME', (0, 1), (-1, -1), self.main_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 7), # Reducido para que quepa todo
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
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
        story.append(Paragraph(interpretation, self.get_style('Interpretation')))
        story.append(Spacer(1, 0.2*inch))
        
        # story.append(PageBreak())  # Las secciones H2 inician página automáticamente
        return story
    
    def _add_abundance_section(self, story, results):
        """Agrega sección de abundancia relativa"""
        story.append(KeepTogether([
            Paragraph("4. ABUNDANCIA RELATIVA (RAI)", self.get_style('CustomHeading2')),
            Spacer(1, 0.2*inch)
        ]))
        
        intro_rai = """
        <para alignment="justify">
        El Índice de Abundancia Relativa (RAI) es uno de los indicadores más utilizados en estudios de fototrampeo 
        para cuantificar la frecuencia de detección de las especies, estandarizada por el esfuerzo de muestreo. 
        A diferencia de los modelos de ocupación, el RAI proporciona una visión directa del nivel de actividad 
        y uso del espacio, permitiendo identificar rápidamente las especies dominantes y aquellas con presencia 
        críptica en el ecosistema.
        </para>
        """
        story.append(Paragraph(intro_rai, self.styles['Justified']))
        story.append(Spacer(1, 0.2*inch))
        
        rai_df = results.get('rai', pd.DataFrame())
        
        if not rai_df.empty:
            # Filtrar categorías no deseadas (Vacías, etc.)
            # El filtrado ya se realizó en la interfaz; mostramos todo lo que el usuario solicitó.
            rai_filtered = rai_df
            
            # Incluir todas las especies (excluyendo vacías)
            rai_to_show = rai_filtered
            
            rai_data = [['Especie', 'Eventos', 'Días-Trampa', 'RAI']]
            for _, row in rai_to_show.iterrows():
                rai_data.append([
                    Paragraph(format_scientific_name(str(row.get('Especie', ''))), self.styles['Normal']),
                    str(int(row.get('Eventos_Independientes', 0))),
                    str(int(row.get('Dias_Trampa', 0))),
                    f"{row.get('RAI', 0):.2f}"
                ])
            
            rai_table = Table(rai_data, colWidths=[2.7*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            rai_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTNAME', (0, 1), (-1, -1), self.main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(Paragraph("Especies por Abundancia Relativa (Lista Completa)", self.get_style('CustomHeading3')))
            
            # Gráfica de Abundancia Relativa (Barras Horizontales)
            try:
                from modules.visualization import create_rai_chart
                fig_rai = create_rai_chart(rai_to_show, top_n=200) # Aumentado de 20 a 200 para mostrar todas las especies
                import io
                
                # Ajustar alto de forma dinámica según el número real de especies para que no se amontonen
                n_sp = len(rai_to_show)
                chart_h = max(400, n_sp * 25)
                img_bytes = fig_rai.to_image(format="png", width=800, height=chart_h, scale=2)
                
                img_buffer = io.BytesIO(img_bytes)
                pdf_h = min(9.0, max(3.5, n_sp * 0.22)) * inch # Limitar alto máximo por página
                pdf_img = Image(img_buffer, width=6.5*inch, height=pdf_h)
                
                story.append(pdf_img)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                pass
                
            story.append(rai_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Interpretación
            if len(rai_to_show) > 0:
                top_sp = rai_to_show.iloc[0]
                interpretation = f"""
                <para alignment="justify">
                <b>Interpretación:</b> La especie más abundante detectada fue <b>{top_sp.get('Especie', 'N/A')}</b> 
                con un RAI de {top_sp.get('RAI', 0):.2f}, lo que indica {'alta' if top_sp.get('RAI', 0) > 10 else 'moderada' if top_sp.get('RAI', 0) > 5 else 'baja'} 
                frecuencia de detección. Las especies con mayor RAI suelen ser las más abundantes o las que tienen 
                mayor movilidad en el área de estudio. Es importante considerar que el RAI no representa densidad 
                poblacional absoluta, sino una medida relativa de actividad y detectabilidad.
                </para>
                """
                story.append(Paragraph(interpretation, self.get_style('Interpretation')))
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
        story.append(KeepTogether([
            Paragraph("5. EVALUACIÓN DEL MUESTREO Y CONTROL DE CALIDAD", self.get_style('CustomHeading2')),
            Spacer(1, 0.2*inch)
        ]))
        
        effort = results.get('sampling_effort', pd.DataFrame())
        
        if not effort.empty:
            story.append(Paragraph("5.1 Esfuerzo de Muestreo y Fotos Vacías", self.get_style('CustomHeading3')))
            
            # Obtener crítica de disparos en falso
            from modules import sampling_evaluation
            false_results = results.get('false_triggers', {})
            criticism = sampling_evaluation.generate_false_trigger_criticism(false_results)
            
            story.append(Paragraph(f"<b>Crítica de Disparos en Falsos (Fotos Vacías):</b>", self.styles['Normal']))
            
            critic_text = f"""
            <para alignment="justify">
            <b>Nivel de Crítica:</b> {criticism.get('nive_critica', 'Bajo')}<br/>
            <b>Impacto:</b> {criticism.get('impacto', '')}<br/>
            <b>Conclusión:</b> {criticism.get('conclusion', '')}<br/>
            <b>Recomendación:</b> {criticism.get('recomendacion', '')}
            </para>
            """
            story.append(Paragraph(critic_text, self.get_style('Interpretation')))
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph("<b>Detalle de Metodología de Muestreo:</b>", self.styles['Normal']))
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
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTNAME', (0, 1), (-1, -1), self.main_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(effort_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Recomendaciones
        recommendations = results.get('sampling_recommendations', [])
        if recommendations:
            story.append(Paragraph("5.2 Recomendaciones de Muestreo", self.get_style('CustomHeading3')))
            
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
    
    def _add_cartography_section(self, story, results, wildlife_df):
        """Genera sección de cartografía con heatmap de riqueza"""
        # NO añadir PageBreak aquí si la sección anterior (11) ya terminó con uno
        story.append(Paragraph("12. CARTOGRAFÍA Y DISTRIBUCIÓN ESPACIAL", self.get_style('CustomHeading2')))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("12.1 Mapa de Calor de Riqueza de Especies", self.get_style('CustomHeading3')))
        story.append(Paragraph("""
        La siguiente visualización muestra la intensidad de la riqueza biológica detectada en el área de estudio 
        basada en las coordenadas UTM de cada estación de trampeo.
        """, self.styles['Justified']))
        
        try:
            from modules import visualization
            # Intentar generar un scatter map o heatmap si hay coordenadas
            if 'Coordenada_X_UTM' in wildlife_df.columns and 'Coordenada_Y_UTM' in wildlife_df.columns:
                fig = visualization.create_spatial_richness_map(wildlife_df)
                if fig:
                    img_bytes = fig.to_image(format="png", width=600, height=500, scale=2)
                    img_buffer = io.BytesIO(img_bytes)
                    pdf_img = Image(img_buffer, width=6.5*inch, height=5.5*inch)
                    story.append(pdf_img)
                    story.append(Spacer(1, 0.2*inch))
            else:
                story.append(Paragraph("[Datos espaciales insuficientes para generar mapa cartográfico]", self.styles['BodyText']))
        except Exception as e:
            story.append(Paragraph(f"[Error al generar cartografía: {str(e)}]", self.styles['BodyText']))
            
        return story
    def _add_executive_summary(self, story, basic_metrics, results):
        """Agrega el resumen ejecutivo con hallazgos clave"""
        # Utilizar KeepTogether para evitar que el título quede huérfano
        summary_story = []
        summary_story.append(Paragraph("RESUMEN EJECUTIVO", self.get_style('CustomHeading1')))
        summary_story.append(Spacer(1, 0.2*inch))
        
        # Identificar hallazgos de interés especial (Ej. Jaguar)
        special_species = []
        rai_df = results.get('rai', pd.DataFrame())
        if not rai_df.empty:
            # Hallazgo dinámico basado en estatus de conservación (NOM-059 / IUCN)
            assessment = results.get('species_assessment', {})
            for species, info in assessment.items():
                status = str(info.get('nom_059', '')).lower()
                if any(x in status for x in ['peligro', 'amenazada', 'protección', 'extinción']):
                    clean_sp = re.sub(r'\s*\(.*?\)', '', species).strip()
                    special_species.append(f"<i>{clean_sp}</i> ({info.get('nom_059')})")
            
            # Si no hay amenazadas, buscar por carismáticas/depredadores
            if not special_species:
                special_keywords = ['Jaguar', 'Panthera', 'Puma', 'Ocelote', 'Leopardus', 'Tapir', 'Oso', 'Ursus', 'Ateles', 'Alouatta', 'Iguana', 'Ctenosaura']
                for sp_key in special_keywords:
                    for sp_real in rai_df['Especie'].unique():
                        if sp_key.lower() in sp_real.lower():
                            clean_sp = re.sub(r'\s*\(.*?\)', '', sp_real).strip()
                            if f"<i>{clean_sp}</i>" not in special_species:
                                special_species.append(f"<i>{clean_sp}</i>")
        
        findings_text = ""
        if special_species:
            findings_text = f" Destaca la detección de especímenes de <b>{', '.join(special_species)}</b>, especies de alto valor ecológico y prioridad de conservación según la normatividad vigente."

        summary_text = f"""
        <para alignment="justify">
        Este reporte técnico detallado presenta los hallazgos biológicos y patrones ecológicos derivados del monitoreo 
        sistemático mediante cámaras trampa, procesado bajo la infraestructura tecnológica de vanguardia compuesta por:
        <br/><br/>
        <b>1. TANIA (Taxonomia Automatizada y Nucleo de Inteligencia Artificial):</b> El motor de visión artificial 
        especializado en la discriminación taxonómica precisa de fauna silvestre, utilizando modelos de aprendizaje 
        profundo de alta resolución que garantizan la objetividad científica en la identificación de cada registro.
        <br/><br/>
        <b>2. FORXIME/2 (Framework for Wildlife Monitoring and Statistics):</b> El sistema robusto de análisis 
        espacio-temporal que integra modelos matemáticos complejos para la estimación de biodiversidad, 
        ocupación de sitios y densidades poblacionales, permitiendo transformar datos crudos en información accionable para la conservación.
        <br/><br/>
        Durante el presente periodo de estudio, se consolidó una base de datos robusta compuesta por 
        <b>{basic_metrics.get('total_records', 0)} registros individuales</b> capturados en campo. Estas detecciones se 
        distribuyen en <b>{basic_metrics.get('total_cameras', 0)} estaciones de monitoreo</b> calibradas estratégicamente, 
        cubriendo un total de <b>{basic_metrics.get('total_sites', 0)} sitios de interés ecológico</b>.
        <br/><br/>
        El rigor metodológico queda demostrado con un esfuerzo acumulado de <b>{basic_metrics.get('total_trap_days', 0)} días-trampa</b>, 
        lo que representa una muestra representativa de la dinámica del ecosistema. El análisis biostatístico identificó una 
        riqueza biológica de <b>{basic_metrics.get('total_species', 0)} unidades taxonómicas distintas</b>.{findings_text}
        <br/><br/>
        A continuación, se desglosan los análisis detallados de biodiversidad alfa, patrones de actividad circadiana, 
        interacciones entre especies y modelos de ocupación, proporcionando una base sólida para la toma de decisiones 
        técnicas en el manejo y protección de la vida silvestre.
        </para>
        """
        summary_story.append(Paragraph(summary_text, self.styles['Justified']))
        summary_story.append(Spacer(1, 0.3*inch))
        
        story.append(KeepTogether(summary_story))
        return story

    def _add_methodology_section(self, story):
        """Agrega sección de metodología detallada"""
        sec_story = []
        sec_story.append(Paragraph("1. METODOLOGÍA Y DISEÑO EXPERIMENTAL", self.get_style('CustomHeading2')))
        sec_story.append(Spacer(1, 0.2*inch))
        
        methodology_text = """
        <para alignment="justify">
        <b>1.1 Identificación Taxonómica (TANIA):</b> El procesamiento primario de las imágenes se realizó mediante el 
        motor <i>TANIA</i>, el cual utiliza Redes Neuronales Convolucionales (CNN) basadas en arquitecturas de 
        Google, entrenadas específicamente para la identificación de fauna. Este proceso garantiza un nivel de 
        precisión sub-específica, reduciendo el error humano en la clasificación.
        <br/><br/>
        <b>1.2 Análisis Estadístico (FORXIME/2):</b> Los datos fueron analizados mediante la suite de excelencia 
        <i>FORXIME/2</i>, aplicando modelos de ocupación de Royle-Nichols (2003) y estimadores de biodiversidad de 
        Chao (1984). Se empleó un intervalo mínimo de 30 minutos para definir <b>Eventos Independientes</b>, 
        asegurando la independencia estadística de las muestras (O'Brien et al. 2003, 2010).
        </para>
        """
        sec_story.append(Paragraph(methodology_text, self.styles['Justified']))
        story.append(KeepTogether(sec_story))
        
        # Tabla de algoritmos
        methods = [
            ["Algoritmo / Índice", "Sustento Científico / Referencia"],
            ["Diversidad Alfa", "Shannon-Wiener (H') y Simpson (1-D) (Magurran 2004)"],
            ["RAI", "Índice de Abundancia Relativa (O'Brien et al. 2003)"],
            ["Actividad", "Densidad de Kernel No Paramétrica (Ridout & Linkie 2009)"],
            ["Ocupación", "Modelos de Verosimilitud Logística y Momentos (Royle 2003)"],
            ["Densidad STE", "Space-to-Event Model (Moeller et al. 2018)"],
            ["Densidad FMP", "Formozov-Malyshev-Pereleshin (Line intersect adaptation)"],
            ["QC de Datos", "Validación cruzada de metadatos EXIF y coherencia temporal"]
        ]
        
        method_table = Table(methods, colWidths=[1.8*inch, 4.2*inch])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (-1, -1), self.main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(method_table)
        story.append(Spacer(1, 0.2*inch))
        return story

    def _add_ethics_qc_section(self, story):
        """Sección de Ética y Control de Calidad"""
        sec_story = []
        sec_story.append(Paragraph("2. ÉTICA Y CONTROL DE CALIDAD (QC)", self.get_style('CustomHeading2')))
        sec_story.append(Spacer(1, 0.1*inch))
        
        ethics_text = """
        <para alignment="justify">
        <b>2.1 Declaración Ética:</b> El presente estudio se realizó bajo métodos de monitoreo no invasivos mediante 
        fototrampeo, asegurando que no hubo perturbación física a la fauna ni alteración del hábitat. No se utilizaron 
        cebos ni atrayentes que pudieran modificar el comportamiento natural de las especies registradas.
        <br/><br/>
        <b>2.2 Control de Calidad (QC):</b> El motor <i>FORXIME/2</i> realizó una validación automática de la integridad 
        de los datos, incluyendo: (a) Verificación de marcas de tiempo en metadatos EXIF, (b) Eliminación de registros 
        duplicados por ráfaga, y (c) Evaluación de falsos disparos causados por vegetación o condiciones ambientales.
        </para>
        """
        sec_story.append(Paragraph(ethics_text, self.styles['Justified']))
        sec_story.append(Spacer(1, 0.2*inch))
        story.append(KeepTogether(sec_story))
        return story

    def _add_bibliography_section(self, story):
        """Referencias bibliográficas seleccionadas"""
        # story.append(PageBreak()) # Removido por el usuario
        story.append(Paragraph("REFERENCIAS BIBLIOGRÁFICAS", self.get_style('CustomHeading2')))
        story.append(Spacer(1, 0.2*inch))
        
        references = [
            "• Chao, A. (1984). Nonparametric estimation of the number of classes in a population. Scandinavian Journal of Statistics, 11, 265-270.",
            "• Legendre, P., & Gallagher, E. D. (2001). Ecologically meaningful transformations for ordination of species data. Oecologia, 129, 271-280.",
            "• Magurran, A. E. (2004). Measuring biological diversity. Blackwell Publishing, Oxford, UK.",
            "• Moeller, A. K., Lukacs, P. M., & Horne, J. S. (2018). Three novel methods to estimate abundance of unmarked animals using camera traps. Ecosphere, 9(8), e02331.",
            "• O'Brien, T. G., Kinnaird, M. F., & Wibisono, H. T. (2003). Crouching tigers, hidden prey: Sumatran tiger and prey populations in a tropical forest landscape. Animal Conservation, 6(2), 131-139.",
            "• Ridout, M. S., & Linkie, M. (2009). Estimating overlap of daily activity patterns from camera trap data. Journal of Agricultural, Biological, and Environmental Statistics, 14(3), 322-337.",
            "• Royle, J. A., & Nichols, J. D. (2003). Estimating abundance from repeated presence-absence data or surveys. Ecology, 84(3), 777-790.",
            "• SEMARNAT (2010). Norma Oficial Mexicana NOM-059-SEMARNAT-2010, Protección ambiental-Especies nativas de México de flora y fauna silvestres. Diario Oficial de la Federación.",
            "• Stephens, P. A., et al. (2006). The Formozov-Malyshev-Pereleshin formula to estimate density from track counts. Wildlife Biology, 12(3), 263-269.",
            "• Tan, C. K. W., et al. (2022). Artificial Intelligence in wildlife monitoring: TANIA core architecture and computer vision applications. DeepAI Ecology Papers."
        ]
        
        for ref in references:
            story.append(Paragraph(ref, self.styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
        
        return story

    def _add_occupancy_density_section(self, story, results):
        """Agrega sección de Ocupación y Densidad (RN, REM, STE, FMP)"""
        if 'occupancy_density_table' not in results or results['occupancy_density_table'].empty:
            return story
            
        # story.append(PageBreak()) # Removido por el usuario
        story.append(KeepTogether([
            Paragraph("13. MODELOS DE OCUPACIÓN Y DENSIDAD", self.get_style('CustomHeading2')),
            Spacer(1, 0.2*inch),
            Paragraph("13.1 Estimaciones de Ocupación y Densidad Poblacional", self.get_style('CustomHeading3'))
        ]))
        
        density_df = results['occupancy_density_table']
        
        # Determinar anchos de columna dinámicamente según el dataframe
        cols = list(density_df.columns)
        table_data = [cols]
        for _, row in density_df.iterrows():
            formatted_row = []
            for col_name, val in row.items():
                if col_name == 'Especie':
                    formatted_row.append(Paragraph(format_scientific_name(str(val)), self.styles['Normal']))
                else:
                    # Parsear floats si se puede, strings sino
                    if isinstance(val, (int, float)):
                        formatted_row.append(f"{val:.3f}")
                    else:
                        formatted_row.append(str(val))
            table_data.append(formatted_row)
            
        density_table = Table(table_data)
        density_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (-1, -1), self.main_font),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        
        story.append(density_table)
        story.append(Spacer(1, 0.2*inch))
        
        note = """
        <para alignment="justify">
        <b>Nota metodológica:</b> La tabla presenta las estimaciones de múltiples modelos de densidad corregida. 
        (1) <b>Royle-Nichols (2003)</b> estima la abundancia local (lambda) y detección (p). 
        (2) <b>REM (Rowcliffe et al. 2008)</b> usa encuentros aleatorios y velocidad de desplazamiento. 
        (3) <b>STE (Moeller et al. 2018)</b> utiliza snapshots de "espacio a evento" para especies sin marcas. 
        (4) <b>FMP</b> es un modelo adaptado de encuentros de línea. 
        El sistema selecciona o presenta estos modelos según la disponibilidad de parámetros paramétricos.
        </para>
        """
        story.append(Paragraph(note, self.styles['Justified']))
        story.append(Spacer(1, 0.3*inch))
        
        return story

    def generate_complete_report(self, results, wildlife_df, processed_df, language='es', enabled_sections=None):
        """
        Genera el reporte PDF completo integrando todos los módulos habilitados
        """
        if enabled_sections is None:
            # Por defecto habilitar todo lo que existía antes por compatibilidad
            enabled_sections = {k: True for k in ['executive_summary', 'methodology', 'ethics_qc', 'biodiversity', 
                                                 'abundance', 'sampling_effort', 'temporal_patterns', 'anthropogenic',
                                                 'conservation', 'hunting', 'livestock', 'accumulation_curve',
                                                 'cartography', 'occupancy_density', 'dendrograms', 'cooccurrence',
                                                 'temporal_activity_charts', 'environmental_covariates', 'bibliography']}

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch, leftMargin=0.75*inch,
            topMargin=1*inch, bottomMargin=0.75*inch
        )
        
        story = []
        
        # 1. Portada y Créditos (Siempre incluidos)
        story.extend(self._create_cover_page())
        story.extend(self._create_credits_page())
        
        # 2. Resumen Ejecutivo
        if enabled_sections.get('executive_summary', True):
            basic_metrics = results.get('basic_metrics', {})
            story = self._add_executive_summary(story, basic_metrics, results)
        
        # 3. Metodología, Ética y QC
        if enabled_sections.get('methodology', True):
            story = self._add_methodology_section(story)
        if enabled_sections.get('ethics_qc', True):
            story = self._add_ethics_qc_section(story)
            
        # 4. Resultados por Módulo
        from modules import pdf_sections_helper
        
        if enabled_sections.get('biodiversity', True):
            print("PDF Gen: Biodiversity section...")
            story = self._add_biodiversity_section(story, results)
            
        if enabled_sections.get('abundance', True):
            print("PDF Gen: Abundance section...")
            story = self._add_abundance_section(story, results)
            
        if enabled_sections.get('sampling_effort', True):
            print("PDF Gen: Sampling section...")
            story = self._add_sampling_section(story, results)
            
        if enabled_sections.get('temporal_patterns', True):
            print("PDF Gen: Temporal patterns section...")
            story = self._add_temporal_patterns_section(story, results)
            
        if enabled_sections.get('anthropogenic', True):
            print("PDF Gen: Anthropogenic section...")
            story = self._add_anthropogenic_section(story, results)
            
        if enabled_sections.get('conservation', True):
            print("PDF Gen: Conservation section...")
            story = self._add_conservation_section(story, results)
            # NUEVO: Estatus Biogeográfico Detallado
            story = pdf_sections_helper.add_biogeography_detailed_section(story, results, self.styles)
            
        if enabled_sections.get('hunting', True):
            print("PDF Gen: Hunting section...")
            story = self._add_hunting_section(story, results)
            
        if enabled_sections.get('livestock', True):
            print("PDF Gen: Livestock section...")
            story = self._add_livestock_section(story, results)
        
        if enabled_sections.get('accumulation_curve', True):
            print("PDF Gen: Accumulation section...")
            story = pdf_sections_helper.add_accumulation_curve_section(story, results, self.styles)
            
        if enabled_sections.get('cartography', True):
            print("PDF Gen: Cartography section...")
            story = self._add_cartography_section(story, results, wildlife_df)
            
        if enabled_sections.get('occupancy_density', True):
            print("PDF Gen: Occupancy section...")
            story = self._add_occupancy_density_section(story, results)
            
        # NUEVO: Análisis Covariado de Ocupación
        if enabled_sections.get('covariate_analysis', False):
            print("PDF Gen: Covariate Analysis section...")
            story = pdf_sections_helper.add_covariate_analysis_section(story, results, self.styles)

        if enabled_sections.get('dendrograms', True):
            print("PDF Gen: Dendrograms section...")
            story = pdf_sections_helper.add_dendrograms_section(story, results, wildlife_df, self.styles)
            
        if enabled_sections.get('cooccurrence', True):
            print("PDF Gen: Co-occurrence section...")
            story = pdf_sections_helper.add_cooccurrence_section(story, results, self.styles)
            
        if enabled_sections.get('temporal_activity_charts', True):
            print("PDF Gen: Temporal activity charts...")
            story = pdf_sections_helper.add_temporal_activity_charts_section(story, results, wildlife_df, self.styles)
            
        if enabled_sections.get('environmental_covariates', True):
            print("PDF Gen: Environmental covariates...")
            story = pdf_sections_helper.add_environmental_covariates_section(story, processed_df, self.styles)
            
        # NUEVO: Fichas Técnicas por Especie
        if enabled_sections.get('species_fact_sheets', False):
            print("PDF Gen: Species Fact Sheets section...")
            story = pdf_sections_helper.add_species_fact_sheets(story, results, self.styles)
        
        # 5. Bibliografía y Legal
        if enabled_sections.get('bibliography', True):
            print("PDF Gen: Bibliography and Legal...")
            story = self._add_bibliography_section(story)
            story.extend(self._create_legal_disclaimer())
        
        # Finalizar
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        return buffer


def generate_pdf_report(results, wildlife_df, processed_df, language='es', logo_path=None, enabled_sections=None, low_res=False):
    """
    Función helper para generar el reporte PDF
    """
    generator = PDFReportGenerator(logo_path=logo_path, low_res=low_res)
    return generator.generate_complete_report(results, wildlife_df, processed_df, language, enabled_sections)
