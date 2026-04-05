# FORXIME/2 🐆📷 [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19425714.svg)](https://doi.org/10.5281/zenodo.19425714)

**Plataforma Profesional de Análisis de Datos de Cámaras Trampa**

Desarrollado por: **Biólogo Erick Elio Chavez Gurrola**

---

## 📋 Descripción

FORXIME/2 es una plataforma web completa y profesional para el análisis estadístico y ecológico de datos de cámaras trampa (fototrampeo). Diseñada para biólogos, ecólogos e investigadores de vida silvestre, esta herramienta permite procesar datos de cámaras trampa, realizar análisis estadísticos avanzados, evaluar patrones de actividad temporal, analizar variables ambientales y generar visualizaciones profesionales con interpretaciones automáticas.

## ✨ Características Principales

### 📊 Análisis Estadístico Completo

- **Índices de Biodiversidad**: Shannon-Wiener, Simpson, Riqueza de Especies, Equitatividad de Pielou
- **Dendrograma de Bray-Curtis**: Análisis de similitud entre sitios
- **Modelo Royle-Nichols**: Estimación de ocupación y abundancia relativa
- **Índice de Abundancia Relativa (RAI)**: Eventos por 100 días-trampa
- **Ocupación Naive**: Proporción de sitios ocupados
- **Curvas de Acumulación**: Evaluación de completitud del muestreo
- **Matrices de Co-ocurrencia**: Análisis de asociaciones entre especies

### ⏰ Análisis Temporal Avanzado

- **Patrones de Actividad**: Clasificación diurno/nocturno/crepuscular/catémero
- **Kernel Density Estimation (KDE)**: Análisis circular de actividad
- **Solapamiento Temporal - Método Ridout & Linkie**: Coeficiente Δ con intervalos de confianza bootstrap
- **Solapamiento Temporal - Método KDE**: Área de solapamiento de curvas de densidad
- **Análisis Depredador-Presa**: Evaluación de sincronía temporal
- **Análisis de Competidores**: Partición temporal del nicho

### 🌍 Variables Ambientales

- **Distancia a Ríos**: Usando OpenStreetMap/Overpass API
- **Distancia a Ciudades**: Identificación de asentamientos cercanos
- **Elevación**: API de elevación gratuita
- **Estimación de Bioma**: Basado en coordenadas y elevación
- **Índice de Modificación Humana**: Evaluación de perturbación
- **Análisis de Correlación**: Influencia de variables en biodiversidad

### 👥 Impacto Antropogénico

- **Identificación Automática**: Detección de registros no-fauna silvestre
- **Métricas por Sitio**: Porcentaje de impacto antropogénico
- **Categorización**: Humanos, perros, ganado, vehículos
- **Correlación con Biodiversidad**: Análisis de efectos en fauna
- **Recomendaciones de Manejo**: Sugerencias basadas en datos

### 📈 Evaluación de Muestreo

- **Esfuerzo de Muestreo**: Días-trampa por cámara
- **Detección de Falsos Positivos**: Identificación de disparos sin fauna
- **Evaluación de Espaciamiento**: Análisis de distancia entre cámaras
- **Sitios Dobles vs Sencillos**: Comparación de efectividad
- **Recomendaciones**: Mejoras para el diseño de muestreo

### 🗺️ Visualizaciones Profesionales

- **Mapas Interactivos (Folium)**: Múltiples capas (satélite, topográfico, OSM)
- **Gráficas Interactivas (Plotly)**: Barras, líneas, radiales, heatmaps
- **Dendrogramas**: Clustering jerárquico
- **Curvas de Actividad**: Gráficas radiales 24 horas
- **Mapas de Calor**: Riqueza y co-ocurrencia

### 🌐 Interfaz Multiidioma

- **Español** (idioma principal)
- **Inglés**
- Cambio dinámico de idioma en toda la aplicación

### 💡 Interpretaciones Automáticas

- Explicaciones en lenguaje natural de todos los análisis
- Adaptadas al nivel del usuario
- Contexto ecológico y significado biológico
- Recomendaciones de manejo

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/FORXIME2.git
cd FORXIME2
```

1. **Crear entorno virtual (recomendado)**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

1. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

1. **Ejecutar la aplicación**

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 📖 Uso

### 1. Preparación de Datos

#### Opción A: Archivo Excel

1. Descarga la plantilla Excel desde la sección "Procesar Datos"
2. Completa las columnas requeridas:
   - `Sitio`: Nombre del sitio de muestreo
   - `Camara`: Identificador de la cámara
   - `Coordenada_X_UTM`: Coordenada Este en UTM
   - `Coordenada_Y_UTM`: Coordenada Norte en UTM
   - `Zona_UTM`: Zona UTM (ej: 12N, 13S)
   - `Especie_Categoria`: Nombre de la especie
   - `Fecha`: Fecha de captura (DD/MM/AAAA)
   - `Hora`: Hora de captura (HH:MM:SS)
   - `Eventos_Independientes`: Número de eventos independientes

#### Opción B: Entrada Manual

1. Completa el formulario en la interfaz
2. Agrega registros uno por uno
3. Opcionalmente, añade observaciones de comportamiento

### 2. Procesamiento

1. Carga tus datos (Excel o manual)
2. Haz clic en "Procesar Datos"
3. El sistema automáticamente:
   - Agrupa cámaras cercanas (<10m)
   - Calcula todos los índices
   - Realiza análisis temporal
   - Evalúa impacto antropogénico
   - Genera recomendaciones

### 3. Visualización de Resultados

Explora las pestañas de resultados:

- 📊 Biodiversidad
- 🌳 Dendrograma
- 📈 Abundancia
- ⏰ Patrones Temporales
- 🔄 Solapamiento Temporal
- 🗺️ Mapa del Área de Estudio
- 👥 Impacto Antropogénico
- 📋 Evaluación de Muestreo

### 4. Exportación

- Descarga resultados en formato Excel
- Incluye todas las tablas y métricas

---

## 📊 Formato de Datos

### Columnas Requeridas

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| Sitio | Texto | Nombre del sitio | Sitio_A |
| Camara | Texto | ID de cámara | CAM001 |
| Coordenada_X_UTM | Número | Coordenada Este | 500000 |
| Coordenada_Y_UTM | Número | Coordenada Norte | 2500000 |
| Zona_UTM | Texto | Zona UTM | 12N |
| Especie_Categoria | Texto | Nombre de especie | Panthera onca |
| Fecha | Fecha | Fecha de captura | 01/01/2024 |
| Hora | Hora | Hora de captura | 08:30:00 |
| Eventos_Independientes | Número | Eventos independientes | 1 |

### Columnas Opcionales (Comportamiento)

- `Es_Cria`: Sí/No
- `Lactante`: Sí/No
- `Periodo_Ensenanza`: Sí/No
- `Rascando_Arboles`: Sí/No
- `Usando_Letrina`: Sí/No
- `Salud_Fisica`: Buena/Regular/Mala
- `Observaciones`: Texto libre

---

## 🔬 Metodología Científica

### Índices de Biodiversidad

- **Shannon-Wiener**: Mide diversidad considerando riqueza y equitatividad
- **Simpson**: Probabilidad de que dos individuos seleccionados al azar sean de especies diferentes
- **Pielou**: Equitatividad en la distribución de abundancias

### Análisis Temporal

- **Ridout & Linkie (2009)**: Coeficiente Δ para solapamiento temporal
  - Δ1 para n < 50
  - Δ4 para n > 75
- **Kernel Density Estimation**: Análisis circular para datos de 24 horas

### Modelo Royle-Nichols

- Estima ocupación (ψ) y abundancia relativa (λ)
- Considera detección imperfecta
- Requiere ≥10 sitios y ≥3 ocasiones de muestreo

### Similitud de Bray-Curtis

- Mide disimilitud en composición de especies entre sitios
- Valores: 0 (idénticos) a 1 (completamente diferentes)
---

## 🎓 Cómo Citar

Si utilizas FORXIME/2 en tu investigación o informes técnicos, por favor cita el software de la siguiente manera:

**Formato sugerido:**
> Chavez Gurrola, E. E. (2026). FORXIME/2: Plataforma Profesional de Análisis de Datos de Cámaras Trampa (Versión 2.0.0) [Software]. Disponible en https://github.com/Biochavezforester/FORXIME2, DOI: 10.5281/zenodo.19425714

Este repositorio incluye un archivo `CITATION.cff` que permite a gestores de referencias (como Zotero o Mendeley) capturar los metadatos automáticamente. En GitHub, puedes usar el botón **"Cite this repository"** en la barra lateral derecha.

---

## 💻 Tecnologías Utilizadas

- **Streamlit**: Framework de aplicación web
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos
- **SciPy**: Análisis estadísticos
- **Plotly**: Visualizaciones interactivas
- **Folium**: Mapas interactivos
- **Matplotlib/Seaborn**: Gráficas estáticas
- **PyProj**: Transformaciones de coordenadas
- **Geopy**: Cálculos geoespaciales
- **Requests**: Consultas a APIs

---

## 🔬 Calidad de Software y Ciencia Abierta

Este proyecto cumple con los estándares de **The Journal of Open Source Software (JOSS)**:

- **Licencia OSI**: Código abierto bajo Licencia MIT.
- **Borrador del Artículo**: Consultar [paper.md](paper.md) para la descripción científica (mastozoología).
- **Pruebas Automatizadas**: Contiene una suite de pruebas en el directorio `tests/` para verificar la precisión de los cálculos bioestadísticos.

Para ejecutar las pruebas:
```bash
pytest tests/
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 💝 Donaciones

Si esta plataforma ha sido útil para tu investigación, considera hacer una donación para apoyar su desarrollo continuo:

### 🇲🇽 Desde México (BBVA)

**Tarjeta:** 4152 3144 0105 9541  
**Titular:** Erick Elio Chavez Gurrola

### 🌎 Internacional (PayPal)

**Email:** <eliogurrola5@gmail.com>

---

## 📧 Contacto

**Biólogo Erick Elio Chavez Gurrola**  
Email: <eliogurrola5@gmail.com>  
ORCID: [0009-0007-7054-6999](https://orcid.org/0009-0007-7054-6999)  
ResearchGate: [Erick Elio Chavez Gurrola](https://www.researchgate.net/profile/Erick-Elio-Chavez-Gurrola-2)

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- A la comunidad de ecólogos y biólogos que trabajan en conservación
- A los desarrolladores de las librerías open-source utilizadas
- A todos los que contribuyen con feedback y sugerencias

---

## 📚 Referencias Científicas

- Ridout, M. S., & Linkie, M. (2009). Estimating overlap of daily activity patterns from camera trap data. *Journal of Agricultural, Biological, and Environmental Statistics*, 14(3), 322-337.
- Royle, J. A., & Nichols, J. D. (2003). Estimating abundance from repeated presence–absence data or point counts. *Ecology*, 84(3), 777-790.
- MacKenzie, D. I., et al. (2002). Estimating site occupancy rates when detection probabilities are less than one. *Ecology*, 83(8), 2248-2255.

---

**FORXIME/2** - Transformando datos de cámaras trampa en conocimiento científico 🐆🔬
