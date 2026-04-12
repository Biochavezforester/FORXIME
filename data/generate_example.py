"""
Script para generar el dataset de ejemplo de FORXIME/2.
Ejecutar una sola vez: python data/generate_example.py
El archivo resultante (ejemplo_fototrampeo.xlsx) se incluye en el repositorio.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# ---------------------------------------------------------------------------
# Definición de sitios de muestreo (Sierra Madre Occidental, Durango, México)
# ---------------------------------------------------------------------------
sites = [
    {"Sitio": "Arroyo_Seco",    "Camara": "CAM001", "X": 485200, "Y": 2645000, "Zona": "13N"},
    {"Sitio": "Arroyo_Seco",    "Camara": "CAM002", "X": 485205, "Y": 2645003, "Zona": "13N"},  # paired
    {"Sitio": "Mesa_Venado",    "Camara": "CAM003", "X": 486100, "Y": 2646200, "Zona": "13N"},
    {"Sitio": "Canada_Oso",     "Camara": "CAM004", "X": 487300, "Y": 2644800, "Zona": "13N"},
    {"Sitio": "Canada_Oso",     "Camara": "CAM005", "X": 487305, "Y": 2644805, "Zona": "13N"},  # paired
    {"Sitio": "Cerro_Prieto",   "Camara": "CAM006", "X": 488500, "Y": 2647100, "Zona": "13N"},
    {"Sitio": "Potrero_Viejo",  "Camara": "CAM007", "X": 484000, "Y": 2643500, "Zona": "13N"},
    {"Sitio": "Rincon_Agua",    "Camara": "CAM008", "X": 489200, "Y": 2645800, "Zona": "13N"},
    {"Sitio": "Barranca_Honda", "Camara": "CAM009", "X": 486700, "Y": 2642900, "Zona": "13N"},
    {"Sitio": "Llano_Grande",   "Camara": "CAM010", "X": 485800, "Y": 2648000, "Zona": "13N"},
    {"Sitio": "Pino_Solo",      "Camara": "CAM011", "X": 490100, "Y": 2644200, "Zona": "13N"},
    {"Sitio": "Agua_Fria",      "Camara": "CAM012", "X": 483500, "Y": 2646500, "Zona": "13N"},
]

# ---------------------------------------------------------------------------
# Especies y sus parámetros de actividad (hora pico, SD, frecuencia relativa)
# ---------------------------------------------------------------------------
species_config = [
    # Especie                    hora_pico  sd   peso_freq  patron
    ("Odocoileus virginianus",      6.0,    2.5,   0.25,  "crepuscular"),
    ("Lynx rufus",                 22.0,    3.0,   0.12,  "nocturno"),
    ("Pecari tajacu",               9.0,    3.5,   0.15,  "diurno"),
    ("Nasua narica",               11.0,    2.0,   0.10,  "diurno"),
    ("Urocyon cinereoargenteus",   20.0,    2.5,   0.08,  "nocturno"),
    ("Meleagris gallopavo",         7.5,    1.5,   0.06,  "diurno"),
    ("Sylvilagus floridanus",       5.5,    2.0,   0.07,  "crepuscular"),
    ("Sciurus aberti",             12.0,    2.0,   0.05,  "diurno"),
    ("Puma concolor",               2.0,    4.0,   0.04,  "nocturno"),
    ("Canis latrans",              19.0,    3.0,   0.03,  "nocturno"),
    ("Spilogale gracilis",         23.0,    2.0,   0.02,  "nocturno"),
    ("Conepatus leuconotus",       21.0,    2.0,   0.01,  "nocturno"),
    # Especies antropogénicas (para probar el módulo de impacto)
    ("Humano",                     10.0,    3.0,   0.015, "diurno"),
    ("Perro",                      10.0,    4.0,   0.005, "diurno"),
]

# ---------------------------------------------------------------------------
# Período de muestreo
# ---------------------------------------------------------------------------
start_date = datetime(2025, 9, 1)
end_date   = datetime(2025, 12, 15)
n_days     = (end_date - start_date).days

# ---------------------------------------------------------------------------
# Generar registros
# ---------------------------------------------------------------------------
records = []

for site_info in sites:
    # Cada cámara genera entre 30 y 120 registros
    n_records = np.random.randint(30, 120)

    for _ in range(n_records):
        # Seleccionar especie con probabilidad ponderada
        weights = np.array([sp[3] for sp in species_config])
        weights /= weights.sum()
        sp_idx = np.random.choice(len(species_config), p=weights)
        sp_name, peak_hour, sd_hour, _, _ = species_config[sp_idx]

        # Generar hora basada en distribución normal centrada en la hora pico
        hour = np.random.normal(peak_hour, sd_hour) % 24
        minutes = int((hour % 1) * 60)
        seconds = np.random.randint(0, 60)
        hour_int = int(hour)
        time_str = f"{hour_int:02d}:{minutes:02d}:{seconds:02d}"

        # Generar fecha aleatoria dentro del periodo
        day_offset = np.random.randint(0, n_days)
        date_obj = start_date + timedelta(days=day_offset)
        date_str = date_obj.strftime("%d/%m/%Y")

        # Eventos independientes (la mayoría son 1, a veces 2-3)
        events = np.random.choice([1, 1, 1, 1, 2, 2, 3], p=[0.55, 0.1, 0.05, 0.05, 0.10, 0.10, 0.05])

        records.append({
            "Sitio":                  site_info["Sitio"],
            "Camara":                 site_info["Camara"],
            "Coordenada_X_UTM":       site_info["X"],
            "Coordenada_Y_UTM":       site_info["Y"],
            "Zona_UTM":               site_info["Zona"],
            "Especie_Categoria":      sp_name,
            "Fecha":                  date_str,
            "Hora":                   time_str,
            "Eventos_Independientes": int(events),
        })

# ---------------------------------------------------------------------------
# Crear DataFrame y guardar
# ---------------------------------------------------------------------------
df = pd.DataFrame(records)

output_path = os.path.join(os.path.dirname(__file__), "ejemplo_fototrampeo.xlsx")
df.to_excel(output_path, index=False, engine="openpyxl")

print(f"Dataset de ejemplo generado: {output_path}")
print(f"  Total registros : {len(df)}")
print(f"  Cámaras          : {df['Camara'].nunique()}")
print(f"  Sitios            : {df['Sitio'].nunique()}")
print(f"  Especies          : {df['Especie_Categoria'].nunique()}")
print(f"  Rango de fechas   : {start_date.date()} – {end_date.date()}")
