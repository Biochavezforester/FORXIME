"""
Tests para el módulo de evaluación de muestreo de FORXIME/2.
Cubre: esfuerzo de muestreo, espaciamiento de cámaras,
y clasificación de esfuerzo.
"""
import pytest
import numpy as np
import pandas as pd
from modules.sampling_evaluation import (
    calculate_sampling_effort,
    evaluate_camera_spacing,
    identify_false_triggers,
)


@pytest.fixture
def sample_dataframe():
    """DataFrame con datos mínimos para pruebas de muestreo."""
    np.random.seed(99)
    dates = pd.date_range("2025-09-01", periods=100, freq="D")
    records = []
    cameras = {
        "CAM001": (485200, 2645000),
        "CAM002": (486200, 2646000),
        "CAM003": (487200, 2647000),
    }
    species = ["Odocoileus virginianus", "Lynx rufus", "Pecari tajacu"]
    for cam, (x, y) in cameras.items():
        n = np.random.randint(20, 50)
        for _ in range(n):
            records.append({
                "Camara": cam,
                "Coordenada_X_UTM": x,
                "Coordenada_Y_UTM": y,
                "Especie_Categoria": np.random.choice(species),
                "Fecha": np.random.choice(dates),
                "Eventos_Independientes": np.random.choice([1, 2]),
            })
    return pd.DataFrame(records)


class TestSamplingEffort:
    def test_returns_dataframe(self, sample_dataframe):
        result = calculate_sampling_effort(sample_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_columns(self, sample_dataframe):
        result = calculate_sampling_effort(sample_dataframe)
        expected_cols = {"Camara", "Dias_Trampa", "Riqueza", "Total_Eventos",
                         "Tasa_Captura", "Clasificacion_Esfuerzo"}
        assert expected_cols == set(result.columns)

    def test_positive_trap_days(self, sample_dataframe):
        result = calculate_sampling_effort(sample_dataframe)
        assert (result["Dias_Trampa"] >= 1).all()

    def test_effort_classification_values(self, sample_dataframe):
        result = calculate_sampling_effort(sample_dataframe)
        valid_classes = {"Insuficiente", "Aceptable", "Bueno", "Excelente"}
        assert set(result["Clasificacion_Esfuerzo"].unique()).issubset(valid_classes)


class TestCameraSpacing:
    def test_returns_dict(self, sample_dataframe):
        result = evaluate_camera_spacing(sample_dataframe)
        assert isinstance(result, dict)
        assert "average_min_distance_m" in result

    def test_positive_distance(self, sample_dataframe):
        result = evaluate_camera_spacing(sample_dataframe)
        assert result["average_min_distance_m"] > 0

    def test_single_camera(self):
        """Con una sola cámara, no se puede evaluar espaciamiento."""
        df = pd.DataFrame({
            "Camara": ["CAM001"],
            "Coordenada_X_UTM": [485200],
            "Coordenada_Y_UTM": [2645000],
        })
        result = evaluate_camera_spacing(df)
        assert "No hay suficientes cámaras" in result["evaluation"]


class TestFalseTriggers:
    def test_no_false_triggers(self, sample_dataframe):
        result = identify_false_triggers(sample_dataframe)
        assert result["total_false_triggers"] == 0

    def test_detects_false_triggers(self):
        """Debe detectar registros con keywords de disparos vacíos."""
        df = pd.DataFrame({
            "Camara": ["CAM001", "CAM001", "CAM001"],
            "Especie_Categoria": ["Vacio", "Lynx rufus", "Lluvia"],
            "Eventos_Independientes": [1, 1, 1],
        })
        result = identify_false_triggers(df)
        assert result["total_false_triggers"] == 2
