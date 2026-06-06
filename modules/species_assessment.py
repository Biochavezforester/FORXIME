"""
Módulo de evaluación de riesgo de especies y prioridades de conservación para FORXIME/2
"""
import pandas as pd
import numpy as np


# Lista de especies amenazadas (IUCN Red List 2024)
# Fuente: https://www.iucnredlist.org
THREATENED_SPECIES = {
    # Críticamente en Peligro (CR)
    'CR': [
        'phocoena sinus', 'vaquita marina', 'vaquita',        # CR - confirmado 2023
        'ambystoma mexicanum', 'ajolote', 'axolotl',          # CR - confirmado 2020
        'dermatemys mawii', 'tortuga blanca',                  # CR - confirmado
        'rhinoceros sondaicus', 'rinoceronte de java',         # CR - confirmado
        'pongo abelii', 'orangután de sumatra',                # CR - confirmado
        'gorilla beringei', 'gorila de montaña',               # CR (subsp. beringei)
        'campephilus imperialis', 'carpintero imperial'        # CR (posiblemente extinto)
    ],
    # En Peligro (EN)
    'EN': [
        'panthera tigris', 'tigre',                           # EN - confirmado 2022
        'elephas maximus', 'elefante asiático',               # EN - confirmado
        'pan troglodytes', 'chimpancé',                       # EN - confirmado
        'lycaon pictus', 'perro salvaje africano',            # EN - confirmado
        'tapirus bairdii', 'tapir centroamericano', 'tapir',  # EN - confirmado
        'alouatta palliata', 'mono aullador', 'saraguato',    # VU en IUCN 2021 (no EN)
        'ateles geoffroyi', 'mono araña',                     # EN - confirmado
        'chelonia mydas', 'tortuga verde',                    # NOTA: reclasificada LC en oct.2025 por IUCN
        'hippopotamus amphibius', 'hipópotamo',               # EN - reclasificado 2022 (era VU)
        'canis lupus baileyi', 'lobo mexicano',               # EN - como subespecie en México
        'trichechus manatus', 'manatí'                        # VU global / EN subespecies
    ],
    # Vulnerable (VU)
    'VU': [
        'panthera pardus', 'leopardo',                        # VU - confirmado 2019
        'panthera leo', 'león',                               # VU - confirmado 2014 (código decía NT: error corregido)
        'alouatta palliata', 'mono aullador', 'saraguato',    # VU - IUCN 2021 (antes EN)
        'tapirus terrestris', 'tapir sudamericano',           # VU - confirmado
        'tayassu pecari', 'pecarí de labios blancos',        # VU - confirmado 2011
        'crocodylus acutus', 'cocodrilo de río',             # VU - confirmado
        'myrmecophaga tridactyla', 'oso hormiguero gigante',  # VU - (no nativa México; solo IUCN)
        'leopardus tigrinus', 'tigrina',                      # VU - (oncilla norteña, no nativa México)
        'tremarctos ornatus', 'oso de anteojos',              # VU - (no nativa México; solo IUCN)
        'trichechus manatus', 'manatí'                        # VU global
    ],
    # Casi Amenazada (NT)
    'NT': [
        'panthera onca', 'jaguar',                            # NT - confirmado 2018
        'leopardus wiedii', 'tigrillo', 'margay'              # NT - confirmado 2015
    ]
    # Nota: jaguarundi (Herpailurus yagouaroundi) = LC según IUCN 2015
    # Nota: Puma concolor = LC según IUCN 2015
    # Nota: Leopardus pardalis (ocelote) = LC según IUCN 2015
}

# NOM-059-SEMARNAT-2010 y modificaciones posteriores (DOF)
# Fuente: https://www.dof.gob.mx / SEMARNAT
NOM_059_SPECIES = {
    # Probablemente extinta en el medio silvestre (E)
    'E': [
        'antilocapra americana peninsularis', 'berrendo peninsular',  # subespecie E
        'antilocapra americana sonoriensis', 'berrendo sonorense',     # subespecie E
        'campephilus imperialis', 'carpintero imperial',               # E / posiblemente extinto
        'ursus arctos', 'oso pardo'                                    # E en México (extinto localmente)
    ],
    # En peligro de extinción (P)
    'P': [
        'panthera onca', 'jaguar',                                    # P - correcto NOM-059
        'tapirus bairdii', 'tapir centroamericano', 'tapir',          # P - correcto
        'trichechus manatus', 'manatí',                               # P - correcto
        'ursus americanus', 'oso negro',                              # P - correcto en México
        'leopardus pardalis', 'ocelote',                              # P - correcto (LC global, P México)
        'leopardus wiedii', 'tigrillo', 'margay',                     # P - correcto
        'herpailurus yagouaroundi', 'jaguarundi',                     # P - correcto en México (LC global)
        'aquila chrysaetos', 'águila real',                           # A en NOM-059 (corregido abajo en 'A')
        'ara macao', 'guacamaya roja',                                # P - correcto
        'phocoena sinus', 'vaquita marina', 'vaquita',               # P - correcto
        'ateles geoffroyi', 'mono araña',                             # P - correcto
        'alouatta palliata', 'saraguato', 'mono aullador',           # P - correcto
        'tayassu pecari', 'pecarí de labios blancos',                # P - correcto en México
        'canis lupus baileyi', 'lobo mexicano',                       # P - correcto
        'ambystoma mexicanum', 'ajolote', 'axolotl',                 # P - correcto
        'dermatemys mawii', 'tortuga blanca',                         # P - correcto
        'chelonia mydas', 'tortuga verde', 'tortuga prieta',         # P - correcto en México
        'mazama temama', 'temazate rojo',                            # P - corregido (antes A, es P)
        'antilocapra americana', 'berrendo'                          # P - corregido (subesp. mexicanas P)
    ],
    # Amenazada (A)
    'A': [
        'aquila chrysaetos', 'águila real',                           # A - correcto en NOM-059
        'crocodylus acutus', 'cocodrilo de río',                     # A en NOM (antes Pr: corregido)
        'crax rubra', 'hocofaisán',                                   # A - correcto
        'spizaetus tyrannus', 'águila tirana',                       # A - correcto
        'harpia harpyja', 'harpía mayor', 'águila arpía',            # A - correcto en NOM-059
        'ctenosaura pectinata', 'iguana negra', 'iguana de roca',   # A - corregido (antes Pr)
        'boa constrictor', 'boa'                                      # A - corregido (antes Pr)
    ],
    # Sujeta a protección especial (Pr)
    'Pr': [
        'urocyon cinereoargenteus', 'zorra gris',                    # Pr - en NOM-059
        'iguana iguana', 'iguana verde',                             # Pr - correcto
        'meleagris gallopavo', 'guajolote silvestre', 'pavo salvaje' # Pr - en NOM-059
        # Nota: Mephitis macroura NO aparece en NOM-059 (eliminada)
        # Nota: Didelphis virginiana NO aparece en NOM-059 (eliminada)
        # Nota: Procyon lotor NO aparece en NOM-059 (eliminada)
    ]
}

# Apéndices CITES (vigentes 2024)
# Fuente: https://cites.org/eng/app/appendices.php
CITES_SPECIES = {
    # Apéndice I: Comercio internacional prohibido
    'I': [
        'panthera onca', 'jaguar',                            # Ap. I - correcto
        'leopardus pardalis', 'ocelote',                      # Ap. I - correcto
        'leopardus wiedii', 'tigrillo', 'margay',             # Ap. I - correcto
        'herpailurus yagouaroundi', 'jaguarundi',             # Ap. I - correcto
        'puma concolor', 'puma',                              # Ap. I (poblaciones neotropicales)
        'tapirus bairdii', 'tapir centroamericano', 'tapir',  # Ap. I - correcto
        'tapirus terrestris', 'tapir sudamericano',           # Ap. I - correcto
        'phocoena sinus', 'vaquita marina', 'vaquita',       # Ap. I - correcto
        'ara macao', 'guacamaya roja',                        # Ap. I - correcto
        'panthera tigris', 'tigre',                           # Ap. I - correcto
        'panthera pardus', 'leopardo',                        # Ap. I - correcto
        'panthera leo', 'león',                               # Ap. I (pob. de África occidental)
        'gorilla beringei', 'gorila',                         # Ap. I - correcto
        'elephas maximus', 'elefante asiático',               # Ap. I - correcto
        'trichechus manatus', 'manatí',                       # Ap. I - correcto
        'dermatemys mawii', 'tortuga blanca',                 # Ap. I - correcto
        'chelonia mydas', 'tortuga verde', 'tortuga prieta', # Ap. I - correcto
        'crocodylus acutus', 'cocodrilo de río',             # Ap. I (algunas poblaciones)
        'tremarctos ornatus', 'oso de anteojos',             # Ap. I - correcto
        'canis lupus baileyi', 'lobo mexicano',               # Ap. I - correcto
        'ateles geoffroyi', 'mono araña',                     # Ap. I - correcto
        'alouatta palliata', 'saraguato', 'mono aullador',   # Ap. I - correcto
        'harpia harpyja', 'harpía mayor', 'águila arpía'    # Ap. I - correcto
    ],
    # Apéndice II: Comercio regulado con permisos
    'II': [
        'lynx rufus', 'gato montés',                          # Ap. II - correcto
        'tayassu pecari', 'pecarí de labios blancos',        # Ap. II - correcto
        'pecari tajacu', 'pecarí de collar', 'jabalí',       # Ap. II - correcto para algunas pob.
        'ursus americanus', 'oso negro',                      # Ap. II - correcto
        'hippopotamus amphibius', 'hipópotamo',               # Ap. II (propuesta a Ap.I rechazada en CoP19)
        'dermatemys mawii', 'tortuga blanca',                 # Ap. II - correcto
        'iguana iguana', 'iguana verde',                      # Ap. II - correcto
        'ctenosaura pectinata', 'iguana negra',               # Ap. II - correcto
        'boa constrictor', 'boa',                             # Ap. II - correcto
        'aquila chrysaetos', 'águila real',                   # Ap. II - correcto
        'lycaon pictus', 'perro salvaje africano',            # Ap. II - correcto
        'myrmecophaga tridactyla', 'oso hormiguero gigante',  # Ap. II - correcto
        'puma concolor', 'puma'                               # Ap. II (pob. neotropicales; algunas en Ap.I)
    ],
    # Apéndice III: Protección en país de origen
    'III': [
        'odocoileus virginianus', 'venado cola blanca',       # Ap. III (Guatemala)
        'nasua narica', 'coatí', 'tejón',                    # Ap. III (Honduras)
        'crax rubra', 'hocofaisán',                           # Ap. III (Honduras/Guatemala)
        'procyon lotor', 'mapache'                            # Ap. III (Honduras)
    ]
}

# Estatus biogeográfico
BIOGEOGRAPHIC_STATUS = {
    # Endémicas de México
    'endemic': [
        'bassariscus astutus', 'cacomixtle',
        'romerolagus diazi', 'teporingo',
        'cynomys mexicanus', 'perrito llanero mexicano'
    ],
    # Invasoras
    'invasive': [
        'sus scrofa', 'jabalí europeo', 'cerdo asilvestrado',
        'felis catus', 'gato doméstico', 'gato feral',
        'canis familiaris', 'perro doméstico', 'perro feral'
    ],
    # Exóticas (introducidas)
    'exotic': [
        'axis axis', 'venado axis',
        'dama dama', 'gamo',
        'cervus elaphus', 'ciervo rojo'
    ]
    # Por defecto, si no está en ninguna lista, se considera 'native' (nativa)
}

# Especies excluidas de evaluaciones de conservación (humanos y animales domésticos)
EXCLUDED_FROM_CONSERVATION = [
    'homo sapiens', 'humano', 'human', 'persona',
    'bos taurus', 'vaca', 'ganado', 'bovino', 'cow',
    'equus caballus', 'caballo', 'horse', 'equino', 'yegua',
    'canis familiaris', 'perro doméstico', 'perro feral',
    'felis catus', 'gato doméstico', 'gato feral',
    'sus scrofa domesticus', 'cerdo doméstico', 'puerco',
    'ovis aries', 'oveja', 'borrego',
    'capra hircus', 'cabra', 'chivo',
    'gallus gallus', 'gallina', 'pollo',
    'meleagris gallopavo domesticus', 'guajolote doméstico',
    'equus asinus', 'burro', 'asno', 'mula'
]

# Lista de nombres comunes en español/inglés que NO son nombres científicos
# Se ampliará automáticamente mediante la función has_valid_scientific_name()
COMMON_NAMES_ONLY = [
    # Mamíferos
    'venado', 'ciervo', 'ardilla', 'rata', 'ratón', 'murcielago', 'muriélago',
    'zorro', 'lobo', 'coyote', 'puma', 'gato', 'perro', 'caballo', 'vaca',
    'toro', 'cerdo', 'jabalí', 'tejon', 'tejón', 'mapache', 'tlacuache',
    'zarigüeya', 'armadillo', 'conejo', 'liebre', 'tapir', 'oso', 'puerco',
    'tejon', 'nutria', 'marta', 'coмédor', 'comadreja', 'tejoncillo',
    # Aves
    'pajaro', 'pájaro', 'ave', 'halcon', 'halcón', 'aguililla', 'aguila', 'águila',
    'buho', 'búcho', 'lechuza', 'loro', 'perico', 'tucán', 'tucan',
    'zanate', 'zopilote', 'gaviota', 'pato', 'garza', 'pelicano', 'col ibri',
    'cuervo', 'cojolite', 'faisán', 'faisan', 'codorniz', 'paloma', 'torcaza',
    'chachalaca', 'pavo', 'guajolote', 'colibrí',
    # Reptiles/Anfibios
    'serpiente', 'vibora', 'víbora', 'cascabel', 'boa', 'iguana', 'lagartija',
    'cocodrilo', 'tortuga', 'sapo', 'rana',
    # Genéricos
    'animal', 'mamifero', 'mamífero', 'reptil', 'anfibio', 'insecto',
    'desconocido', 'sin identificar', 'no identificado', 'no determinado'
]


# ─────────────────────────────────────────────────────────────────────────────
# Taxones superiores (deben definirse ANTES de has_valid_scientific_name)
# ─────────────────────────────────────────────────────────────────────────────
HIGHER_TAXA = [
    # Clados / Superordenes de aves
    'neoaves', 'palaeognathae', 'galloanserae', 'neognathae',
    # Clases
    'aves', 'mammalia', 'reptilia', 'amphibia', 'actinopterygii', 'chondrichthyes',
    'insecta', 'arachnida', 'malacostraca',
    # Órdenes comunes
    'rodentia', 'carnivora', 'artiodactyla', 'chiroptera', 'primates',
    'passeriformes', 'falconiformes', 'accipitriformes', 'strigiformes',
    'galliformes', 'anseriformes', 'columbiformes', 'psittaciformes',
    'piciformes', 'coraciiformes', 'apodiformes', 'caprimulgiformes',
    'gruiformes', 'charadriiformes', 'pelecaniformes', 'suliformes',
    'ciconiiformes', 'cathartiformes', 'tinamiformes', 'struthioniformes',
    'squamata', 'testudines', 'crocodilia', 'anura', 'caudata',
    # Familias
    'felidae', 'canidae', 'mustelidae', 'procyonidae', 'ursidae',
    'cervidae', 'bovidae', 'tayassuidae', 'tapiridae', 'didelphidae',
    'sciuridae', 'muridae', 'cricetidae', 'leporidae',
    'accipitridae', 'falconidae', 'tytonidae', 'strigidae',
    'colubridae', 'viperidae', 'boidae', 'pythonidae',
    # Términos genéricos
    'sp.', 'spp.', 'sp', 'spp', 'indet', 'indeterminado', 'indeterminable',
    'desconocido', 'sin identificar', 'no identificado', 'no determinado',
    'ave', 'ave silvestre', 'mamifero', 'mamífero', 'reptil', 'anfibio',
    'roedor', 'ungulado', 'primate', 'rapaz', 'rapaz nocturna',
    'carnivoro', 'carnívoro', 'herbivoro', 'herbívoro',
]


def is_higher_taxon(species_name):
    """
    Detecta si el nombre corresponde a un taxón superior a especie
    (clase, orden, familia, clado) donde la conservación no es determinable.
    """
    if not species_name or not isinstance(species_name, str):
        return False
    name_lower = species_name.strip().lower()
    for taxon in HIGHER_TAXA:
        if name_lower == taxon or name_lower.startswith(taxon + ' '):
            return True
    # Una sola palabra (sin paréntesis) probablemente es género o taxón superior
    words = [w for w in name_lower.replace('(', '').replace(')', '').split() if w]
    if len(words) == 1 and len(name_lower) > 3:
        return True
    return False


def has_valid_scientific_name(species_name):
    """
    Valida si el nombre cumple con formato binomial científico.
    Estrategia: valida el formato binomial PRIMERO.
    Si pasa la validación (Género + epíteto), se acepta aunque el género
    coincida con un nombre común (ej. 'Puma concolor', 'Boa constrictor').
    Solo se aplica la lista COMMON_NAMES_ONLY para rechazar nombres de una
    sola palabra o frases sin formato binomial.
    """
    import re
    if not species_name or not isinstance(species_name, str):
        return False

    name = species_name.strip()
    name_lower = name.lower()

    # 1. Taxones superiores conocidos siempre se rechazan
    if is_higher_taxon(name):
        return False

    # 2. Limpiar paréntesis y evaluar palabras
    name_clean = re.sub(r'\s*\(.*?\)', '', name).strip()
    words = [w for w in name_clean.split() if w]

    # 3. Si tiene menos de 2 palabras: verificar contra nombres comunes
    if len(words) < 2:
        for common in COMMON_NAMES_ONLY:
            if name_lower == common:
                return False
        return False  # nombre de 1 palabra sin formato binomial siempre se rechaza

    genus = words[0]
    epithet = words[1]

    # 4. Validar formato binomial estricto
    #    Género: empieza con mayúscula, solo letras latínas
    if not re.match(r'^[A-Z][a-z]+$', genus):
        return False

    #    Epíteto: solo letras minúsculas
    if not re.match(r'^[a-z]+$', epithet):
        return False

    #    Longitud mínima razonable
    if len(genus) < 3 or len(epithet) < 3:
        return False

    # 5. Si pasa la validación binomial, se acepta aunque el género
    #    coincida con un nombre común (Puma, Boa, Tapir, etc.)
    return True


def is_excluded_species(species_name):
    """Excluye de evaluaciones: domésticos, taxones superiores y nombres no científicos."""
    import re
    species_lower = str(species_name).lower()

    # 1. Domésticos / humanos
    for ex_sp in EXCLUDED_FROM_CONSERVATION:
        if re.search(r'\b' + re.escape(ex_sp) + r'\b', species_lower):
            return True

    # 2. Taxones superiores
    if is_higher_taxon(species_name):
        return True

    # 3. Sin nomenclatura binomial válida (nombres comunes, géneros solos, etc.)
    if not has_valid_scientific_name(species_name):
        return True

    return False







def assess_species_conservation_status(species_name):
    """
    Evalúa el estado de conservación de una especie (IUCN Red List).
    Retorna 'No determinable' si el nombre no corresponde a una especie.
    """
    if is_higher_taxon(species_name):
        return 'No determinable'
    
    species_lower = species_name.lower()
    
    for category, species_list in THREATENED_SPECIES.items():
        if any(sp in species_lower for sp in species_list):
            return category
    
    return 'LC'  # Least Concern (Preocupación Menor)


def assess_nom059_status(species_name):
    """
    Evalúa el estado según NOM-059-SEMARNAT-2010.
    Retorna 'No determinable' si el nombre no corresponde a una especie.
    """
    if is_higher_taxon(species_name):
        return 'No determinable'
    
    species_lower = species_name.lower()
    
    for category, species_list in NOM_059_SPECIES.items():
        if any(sp in species_lower for sp in species_list):
            return category
    
    return None

def assess_cites_status(species_name):
    """
    Evalúa el estado según los Apéndices CITES.
    Retorna 'No determinable' si el nombre no corresponde a una especie.
    Retorna 'No listada' si es especie válida pero no aparece en ningún apéndice.
    """
    if is_higher_taxon(species_name):
        return 'No determinable'
    
    species_lower = species_name.lower()
    
    for category, species_list in CITES_SPECIES.items():
        if any(sp in species_lower for sp in species_list):
            return category
    
    return 'No listada'  # Especie válida pero no incluida en ningún apéndice CITES


def assess_biogeographic_status(species_name):
    """
    Evalúa el estatus biogeográfico de la especie
    
    Args:
        species_name: Nombre de la especie
    
    Returns:
        str: 'endemic', 'invasive', 'exotic', o 'native'
    """
    species_lower = species_name.lower()
    
    if any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['endemic']):
        return 'endemic'
    elif any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['invasive']):
        return 'invasive'
    elif any(sp in species_lower for sp in BIOGEOGRAPHIC_STATUS['exotic']):
        return 'exotic'
    else:
        return 'native'


def get_nom059_description(category, language='es'):
    """
    Obtiene descripción de categoría NOM-059
    
    Args:
        category: Categoría NOM-059
        language: Idioma
    
    Returns:
        str: Descripción
    """
    descriptions_es = {
        'E': 'Probablemente Extinta en el Medio Silvestre',
        'P': 'En Peligro de Extinción',
        'A': 'Amenazada',
        'Pr': 'Sujeta a Protección Especial'
    }
    
    descriptions_en = {
        'E': 'Probably Extinct in the Wild',
        'P': 'Endangered',
        'A': 'Threatened',
        'Pr': 'Subject to Special Protection'
    }
    
    if language == 'es':
        return descriptions_es.get(category, 'No listada')
    else:
        return descriptions_en.get(category, 'Not listed')

def get_cites_description(category, language='es'):
    """
    Obtiene descripción de apéndice CITES.
    Retorna 'No listada' para None, 'No listada' y 'No determinable'.
    """
    if not category or category in ('No listada', 'No determinable', 'none', 'None'):
        return 'No listada' if language == 'es' else 'Not listed'
    if category in ('I', 'II', 'III'):
        return f"Apéndice {category}" if language == 'es' else f"Appendix {category}"
    # Cualquier otro valor no reconocido
    return 'No listada' if language == 'es' else 'Not listed'


def get_biogeographic_description(status, language='es'):
    """
    Obtiene descripción de estatus biogeográfico
    
    Args:
        status: Estatus biogeográfico
        language: Idioma
    
    Returns:
        str: Descripción
    """
    descriptions_es = {
        'endemic': 'Endémica',
        'native': 'Nativa',
        'invasive': 'Invasora',
        'exotic': 'Exótica'
    }
    
    descriptions_en = {
        'endemic': 'Endemic',
        'native': 'Native',
        'invasive': 'Invasive',
        'exotic': 'Exotic'
    }
    
    if language == 'es':
        return descriptions_es.get(status, 'Desconocido')
    else:
        return descriptions_en.get(status, 'Unknown')

def calculate_conservation_priority_score(df, species):
    """
    Calcula puntaje de prioridad de conservación para una especie.
    
    Metodología (total 100 puntos):
      - NOM-059-SEMARNAT (40 pts): norma mexicana, máxima relevancia local
      - CITES (20 pts): regulación internacional de comercio
      - IUCN Red List (20 pts): contexto global
      - Rareza local / ocupación (10 pts): rareza en el área de estudio
      - Rol ecológico / especie clave (10 pts)
    
    Una especie en P (NOM-059) siempre obtiene mínimo 40 puntos → Prioridad Media o superior.
    """
    species_data = df[df['Especie_Categoria'] == species]
    score_components = {}

    # ── 1. NOM-059-SEMARNAT (0-40 puntos) ─────────────────────────────────────
    nom_status = assess_nom059_status(species)
    nom_scores = {
        'E':  40,   # Probablemente extinta en medio silvestre
        'P':  40,   # En peligro de extinción
        'A':  25,   # Amenazada
        'Pr': 15,   # Sujeta a protección especial
        'No determinable': 0,
        None: 0
    }
    score_components['nom059_score'] = nom_scores.get(nom_status, 0)
    score_components['nom059_status'] = nom_status if nom_status else 'No listada'

    # ── 2. CITES (0-20 puntos) ─────────────────────────────────────────────────
    cites_status = assess_cites_status(species)
    cites_scores = {
        'I':  20,   # Comercio internacional prohibido
        'II': 10,   # Comercio regulado
        'III': 5,   # Protección en país de origen
        'No determinable': 0,
        None: 0
    }
    score_components['cites_score'] = cites_scores.get(cites_status, 0)
    score_components['cites_status'] = cites_status if cites_status and cites_status != 'No determinable' else 'No listada'

    # ── 3. IUCN Red List (0-20 puntos) ─────────────────────────────────────────
    iucn_status = assess_species_conservation_status(species)
    iucn_scores = {
        'CR': 20,
        'EN': 16,
        'VU': 10,
        'NT':  5,
        'LC':  0,
        'No determinable': 0
    }
    score_components['iucn_score'] = iucn_scores.get(iucn_status, 0)
    score_components['iucn_category'] = iucn_status

    # ── 4. Rareza local: baja ocupación = mayor prioridad (0-10 puntos) ────────
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    total_sites = df[site_column].nunique()
    sites_occupied = species_data[site_column].nunique()
    occupancy = sites_occupied / total_sites if total_sites > 0 else 0

    if occupancy < 0.2:
        score_components['rarity'] = 10
    elif occupancy < 0.4:
        score_components['rarity'] = 7
    elif occupancy < 0.6:
        score_components['rarity'] = 4
    else:
        score_components['rarity'] = 0
    score_components['occupancy'] = occupancy

    # ── 5. Rol ecológico / especie clave (0-10 puntos) ─────────────────────────
    keystone_keywords = [
        'panthera', 'jaguar', 'puma', 'lobo', 'wolf', 'tapir', 'elefante',
        'elephant', 'ocelote', 'leopardus', 'tigrillo', 'jaguarundi',
        'ateles', 'alouatta', 'manatí', 'trichechus', 'vaquita'
    ]
    is_keystone = any(kw in species.lower() for kw in keystone_keywords)
    score_components['keystone_species'] = 10 if is_keystone else 0

    # ── Puntaje total (0-100) ──────────────────────────────────────────────────
    total_score = (
        score_components['nom059_score'] +
        score_components['cites_score'] +
        score_components['iucn_score'] +
        score_components['rarity'] +
        score_components['keystone_species']
    )
    score_components['total_score'] = min(total_score, 100)

    # ── Clasificación de prioridad ─────────────────────────────────────────────
    if total_score >= 65:
        priority = 'Crítica'
    elif total_score >= 45:
        priority = 'Alta'
    elif total_score >= 25:
        priority = 'Media'
    else:
        priority = 'Baja'

    score_components['priority_level'] = priority
    return score_components


def generate_conservation_priorities_report(df, language='es'):
    """
    Genera reporte de prioridades de conservación
    
    Args:
        df: DataFrame con datos
        language: Idioma
    
    Returns:
        DataFrame: Reporte de prioridades
    """
    priorities = []
    
    for species in df['Especie_Categoria'].unique():
        if is_excluded_species(species):
            continue
            
        score_data = calculate_conservation_priority_score(df, species)
        
        # Obtener clasificaciones adicionales
        nom059_status = assess_nom059_status(species)
        cites_status = assess_cites_status(species)
        biogeo_status = assess_biogeographic_status(species)
        
        # Cálculo de abundancia relativa para incluir en reporte
        species_data = df[df['Especie_Categoria'] == species]
        total_events = species_data['Eventos_Independientes'].sum() if 'Eventos_Independientes' in df.columns else 0
        all_events = df['Eventos_Independientes'].sum() if 'Eventos_Independientes' in df.columns else 1
        relative_abundance = total_events / all_events if all_events > 0 else 0

        priorities.append({
            'Especie': species,
            'Categoria_IUCN': score_data['iucn_category'],
            'NOM_059': get_nom059_description(score_data.get('nom059_status'), language) if score_data.get('nom059_status') not in (None, 'No listada', 'No determinable') else score_data.get('nom059_status', 'No listada'),
            'CITES': score_data.get('cites_status', 'No listada'),
            'Estatus_Biogeografico': get_biogeographic_description(biogeo_status, language),
            'Ocupacion': f"{score_data['occupancy']:.2%}",
            'Abundancia_Relativa': f"{relative_abundance:.2%}",
            'Especie_Clave': 'Sí' if score_data['keystone_species'] > 0 else 'No',
            'Puntaje_Total': score_data['total_score'],
            'Prioridad': score_data['priority_level']
        })

    
    priorities_df = pd.DataFrame(priorities).sort_values('Puntaje_Total', ascending=False)
    
    return priorities_df


def identify_critical_habitats(df):
    """
    Identifica hábitats críticos basado en presencia de especies amenazadas
    
    Args:
        df: DataFrame con datos
    
    Returns:
        DataFrame: Sitios críticos
    """
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    critical_sites = []
    
    for site in df[site_column].unique():
        site_data = df[df[site_column] == site]
        
        # Contar especies amenazadas
        threatened_count = 0
        threatened_species = []
        
        for species in site_data['Especie_Categoria'].unique():
            if is_excluded_species(species):
                continue
                
            status = assess_species_conservation_status(species)
            if status in ['CR', 'EN', 'VU']:
                threatened_count += 1
                threatened_species.append(f"{species} ({status})")
        
        # Calcular riqueza total
        richness = site_data['Especie_Categoria'].nunique()
        
        # Clasificar importancia
        if threatened_count >= 3:
            importance = 'Crítica'
        elif threatened_count >= 2:
            importance = 'Alta'
        elif threatened_count >= 1:
            importance = 'Media'
        else:
            importance = 'Baja'
        
        critical_sites.append({
            'Sitio': site,
            'Riqueza_Total': richness,
            'Especies_Amenazadas': threatened_count,
            'Lista_Especies_Amenazadas': '; '.join(threatened_species) if threatened_species else 'Ninguna',
            'Importancia_Conservacion': importance
        })
    
    critical_df = pd.DataFrame(critical_sites).sort_values('Especies_Amenazadas', ascending=False)
    
    return critical_df


def generate_species_fact_sheet(df, species, language='es'):
    """
    Genera ficha técnica de una especie
    
    Args:
        df: DataFrame con datos
        species: Nombre de la especie
        language: Idioma
    
    Returns:
        dict: Ficha técnica
    """
    species_data = df[df['Especie_Categoria'] == species]
    
    site_column = 'Sitio_Agrupado' if 'Sitio_Agrupado' in df.columns else 'Sitio'
    
    fact_sheet = {
        'species_name': species,
        'conservation_status': assess_species_conservation_status(species),
        'total_records': len(species_data),
        'independent_events': species_data['Eventos_Independientes'].sum(),
        'sites_detected': species_data[site_column].nunique(),
        'cameras_detected': species_data['Camara'].nunique(),
        'occupancy_rate': species_data[site_column].nunique() / df[site_column].nunique(),
        'detection_rate': len(species_data) / len(df),
        'first_detection': species_data['Fecha'].min(),
        'last_detection': species_data['Fecha'].max()
    }
    
    # Calcular prioridad de conservación
    priority_data = calculate_conservation_priority_score(df, species)
    fact_sheet['conservation_priority'] = priority_data['priority_level']
    fact_sheet['priority_score'] = priority_data['total_score']
    
    return fact_sheet


def generate_monitoring_recommendations(priorities_df, language='es'):
    """
    Genera recomendaciones de monitoreo basadas en prioridades
    
    Args:
        priorities_df: DataFrame con prioridades
        language: Idioma
    
    Returns:
        list: Recomendaciones
    """
    recommendations = []
    
    # Especies de prioridad crítica
    critical_species = priorities_df[priorities_df['Prioridad'] == 'Crítica']
    
    if len(critical_species) > 0:
        if language == 'es':
            rec = {
                'category': 'Especies de Prioridad Crítica',
                'priority': 'Crítica',
                'recommendation': f"Se identificaron {len(critical_species)} especies de prioridad crítica. "
                                f"Se recomienda:\n"
                                f"- Aumentar esfuerzo de monitoreo en sitios donde fueron detectadas\n"
                                f"- Implementar protocolos específicos de conservación\n"
                                f"- Evaluar amenazas inmediatas\n"
                                f"- Considerar establecimiento de áreas protegidas",
                'species_list': critical_species['Especie'].tolist()
            }
        else:
            rec = {
                'category': 'Critical Priority Species',
                'priority': 'Critical',
                'recommendation': f"{len(critical_species)} critical priority species identified. "
                                f"Recommended actions:\n"
                                f"- Increase monitoring effort at detection sites\n"
                                f"- Implement specific conservation protocols\n"
                                f"- Assess immediate threats\n"
                                f"- Consider establishing protected areas",
                'species_list': critical_species['Especie'].tolist()
            }
        
        recommendations.append(rec)
    
    # Especies raras (baja ocupación)
    rare_species = priorities_df[priorities_df['Ocupacion'].str.rstrip('%').astype(float) < 20]
    
    if len(rare_species) > 0:
        if language == 'es':
            rec = {
                'category': 'Especies Raras',
                'priority': 'Alta',
                'recommendation': f"Se detectaron {len(rare_species)} especies raras (ocupación <20%). "
                                f"Se recomienda:\n"
                                f"- Investigar causas de baja detección\n"
                                f"- Evaluar si son naturalmente raras o en declive\n"
                                f"- Aumentar número de cámaras en sitios de detección",
                'species_list': rare_species['Especie'].tolist()
            }
        
        recommendations.append(rec)
    
    return recommendations
