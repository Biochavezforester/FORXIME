---
title: 'FORXIME/2: Standardization of Camera Trap Analysis in the Face of the Code Functionality Crisis in Ecology'
tags:
  - Python
  - camera traps
  - mammalogy
  - biodiversity
  - wildlife monitoring
  - ecological indices
  - temporal overlap
  - reproducibility
authors:
  - name: Erick Elio Chavez-Gurrola
    orcid: 0009-0007-7054-6999
    corresponding: true
    affiliation: 1
affiliations:
 - name: División de Estudios de Posgrado e Investigación, Instituto Tecnológico de El Salto, Tecnológico Nacional de México
   index: 1
date: 12 April 2026
bibliography: paper.bib
---

# Summary

FORXIME/2 is an open-source, web-based platform for the professional analysis of camera trap (phototrapping) data. Built with Python and Streamlit, it provides an intuitive, code-free graphical interface that automates the calculation of biodiversity indices (Shannon-Wiener, Simpson, Pielou evenness), temporal activity pattern analysis using Kernel Density Estimation and the Ridout & Linkie overlap coefficient [@ridout2009], site occupancy estimation via the Royle-Nichols model [@royle2003; @mackenzie2002], anthropogenic impact assessment, and sampling effort evaluation. FORXIME/2 generates interactive visualizations through Plotly [@plotly] and Folium, exports professional reports, and provides automated ecological interpretations in natural language. The platform is bilingual (Spanish/English) and is available in three deployment variants: source code, a portable Windows executable, and a cloud-hosted web application.

# Statement of Need

Camera trapping has become an indispensable tool for monitoring terrestrial mammal biodiversity. Thanks to its ease of use, it typically generates massive datasets with thousands of records of presence and temporal activity [@delisle2021]. This data is fundamental for estimating diversity indices and analyzing species activity patterns, enabling key ecological inferences for conservation [@gotelli2013].

To manage and analyze this avalanche of information, the scientific community has developed specialized software packages, primarily in the R programming language. Notable examples include `camtrapR`, which provides a comprehensive workflow for managing camera trap data and preparing occupancy analyses [@niedballa2016], and the `overlap` package, which implements statistical methods to quantify the overlap of temporal activity patterns among species [@meredith2024].

However, the effective use of these tools represents a significant barrier for a large segment of ecology and conservation professionals. While R has become the most widely used language in ecology publications and proficiency in it is an increasingly common requirement in job postings and postgraduate programs [@vancine2026], formal programming training remains limited in life science curricula. This training gap means that many biologists and environmental managers—with deep knowledge of their ecosystems but no computer science background—face a steep learning curve. For them, programming represents an obstacle that can slow down or even prevent data analysis, creating a technical bottleneck.

This difficulty not only affects individual efficiency but also has broader implications for scientific credibility. The reproducibility crisis in ecology has been widely documented, and one of its main causes is the low availability and lack of functionality of code in scientific publications [@culina2020]. A recent study analyzing nearly 500 ecology articles revealed that while 28% shared data and code, only 7% provided code that ran without errors [@kellner2024]. This situation underscores the need for solutions that not only facilitate analysis but also ensure the integrity and reproducibility of the results.

In response to this challenge, the development of software with graphical user interfaces (GUIs) has been promoted. These interfaces encapsulate the complexity of the underlying code, making advanced methods accessible to researchers without programming knowledge [@johnson2022]. Following this philosophy, FORXIME/2 is an open-source and freely accessible platform designed specifically to democratize camera trap data analysis. By eliminating the need to write and debug scripts in R or Python, FORXIME/2 allows environmental professionals to focus on interpreting results and making data-driven conservation decisions.

# Software Design

FORXIME/2 is implemented as a modular Python application using Streamlit [@streamlit] as the web framework. The analytical core is organized into independent modules:

- **`statistical_analysis`**: Computes Shannon-Wiener, Simpson, and Pielou indices, Bray-Curtis dissimilarity dendrograms, species accumulation curves, Royle-Nichols occupancy models, and co-occurrence matrices.
- **`temporal_analysis`**: Performs circular Kernel Density Estimation for 24-hour activity patterns and calculates the Ridout & Linkie overlap coefficient (Δ1 for n < 50, Δ4 for n > 75) with bootstrap confidence intervals.
- **`environmental_vars`**: Queries OpenStreetMap/Overpass API and elevation services to compute distances to rivers, cities, elevation, biome estimation, and human modification indices.
- **`anthropogenic_impact`**: Detects non-wildlife records (humans, dogs, livestock, vehicles), calculates per-site impact percentages, and correlates anthropogenic pressure with biodiversity metrics.
- **`sampling_evaluation`**: Assesses sampling effort (trap-days per camera), detects false positives, evaluates camera spacing, and compares single vs. paired station effectiveness.
- **`visualization`**: Generates interactive charts (Plotly) and maps (Folium) with multiple base layers (satellite, topographic, OpenStreetMap).
- **`interpretation`**: Produces automated explanations in natural language adapted to the user's level, providing ecological context and management recommendations.

All numerical computations rely on NumPy, Pandas [@mckinney2010], and SciPy [@virtanen2020]. Data input accepts standardized Excel templates or manual entry, ensuring consistent data formatting across studies.

# Research Impact Statement

FORXIME/2 is designed to have a direct impact on the research workflow of wildlife ecologists, particularly in Latin America and other regions where programming training in biology curricula is limited. By standardizing the analytical pipeline for camera trap data and providing reproducible, automated outputs, the platform addresses two critical challenges simultaneously: the accessibility gap that prevents many field biologists from performing advanced analyses, and the reproducibility crisis that undermines the credibility of computational ecology. Its open-source architecture and bilingual interface further promote adoption and community-driven extension.

# AI Usage Disclosure

Generative AI tools were used during the development of FORXIME/2 for code refactoring, interface design suggestions, and drafting documentation. All AI-generated outputs were reviewed, verified, and manually edited by the author.

# Acknowledgements

The author thanks the open-source communities behind Streamlit, Plotly, SciPy, and Pandas for making their tools freely available. This work was conducted at the División de Estudios de Posgrado e Investigación, Instituto Tecnológico de El Salto, Tecnológico Nacional de México.

# References
