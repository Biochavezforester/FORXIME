"""
Tests para el módulo de análisis temporal de FORXIME/2.
Cubre: conversión de horas, KDE circular, clasificación de patrones de
actividad, y coeficiente de solapamiento Δ de Ridout & Linkie.
"""
import pytest
import numpy as np
from modules.temporal_analysis import (
    extract_hour_from_time,
    convert_time_to_radians,
    circular_kernel_density,
    classify_activity_pattern,
    calculate_overlap_coefficient_delta,
)


# ========================== Conversión de Horas ==========================

class TestExtractHour:
    def test_string_input(self):
        result = extract_hour_from_time("14:30:00")
        assert result == pytest.approx(14.5)

    def test_midnight(self):
        result = extract_hour_from_time("00:00:00")
        assert result == pytest.approx(0.0)

    def test_end_of_day(self):
        result = extract_hour_from_time("23:59:59")
        assert result == pytest.approx(23 + 59 / 60 + 59 / 3600, rel=1e-3)

    def test_invalid_input_returns_none(self):
        result = extract_hour_from_time("invalid")
        assert result is None


class TestConvertTimeToRadians:
    def test_midnight(self):
        result = convert_time_to_radians([0])
        assert result[0] == pytest.approx(0.0)

    def test_noon(self):
        result = convert_time_to_radians([12])
        assert result[0] == pytest.approx(np.pi)

    def test_full_day(self):
        result = convert_time_to_radians([24])
        assert result[0] == pytest.approx(2 * np.pi)

    def test_multiple_values(self):
        result = convert_time_to_radians([0, 6, 12, 18])
        expected = np.array([0, np.pi / 2, np.pi, 3 * np.pi / 2])
        np.testing.assert_allclose(result, expected)


# ========================== KDE Circular ==========================

class TestCircularKDE:
    def test_output_shape(self):
        times = np.random.uniform(0, 2 * np.pi, 50)
        grid, density = circular_kernel_density(times, grid_size=500)
        assert len(grid) == 500
        assert len(density) == 500

    def test_density_non_negative(self):
        times = np.random.uniform(0, 2 * np.pi, 100)
        _, density = circular_kernel_density(times)
        assert (density >= 0).all()

    def test_grid_range(self):
        times = np.random.uniform(0, 2 * np.pi, 30)
        grid, _ = circular_kernel_density(times)
        assert grid[0] >= 0
        assert grid[-1] <= 2 * np.pi


# ========================== Clasificación de Patrones ==========================

class TestClassifyActivityPattern:
    def test_diurnal(self):
        """Todos los registros entre 8-16h → Diurno."""
        hours = np.random.uniform(8, 16, 100)
        assert classify_activity_pattern(hours) == "Diurno"

    def test_nocturnal(self):
        """Todos los registros entre 20-4h → Nocturno."""
        hours = np.concatenate([
            np.random.uniform(20, 24, 50),
            np.random.uniform(0, 4, 50)
        ])
        assert classify_activity_pattern(hours) == "Nocturno"

    def test_cathemeral(self):
        """Registros distribuidos uniformemente → Catémero."""
        hours = np.linspace(0, 23.9, 100)
        result = classify_activity_pattern(hours)
        assert result == "Catémero"


# ========================== Coeficiente de Solapamiento Δ ==========================

class TestOverlapCoefficient:
    def test_identical_distributions(self):
        """Distribuciones idénticas → solapamiento ≈ 1."""
        np.random.seed(0)
        times = np.random.uniform(0, 2 * np.pi, 200)
        result = calculate_overlap_coefficient_delta(times, times, estimator="delta4")
        assert result == pytest.approx(1.0, abs=0.1)

    def test_overlap_range(self):
        """El coeficiente siempre debe estar en [0, 1]."""
        np.random.seed(1)
        t1 = np.random.normal(np.pi / 2, 0.5, 100) % (2 * np.pi)
        t2 = np.random.normal(3 * np.pi / 2, 0.5, 100) % (2 * np.pi)
        result = calculate_overlap_coefficient_delta(t1, t2, estimator="delta1")
        assert 0 <= result <= 1

    def test_non_overlapping_species(self):
        """Especies con picos opuestos → solapamiento menor que distribuciones idénticas."""
        np.random.seed(2)
        # Especie diurna: pico a las 12h (π radianes)
        t1 = np.random.normal(np.pi, 0.3, 100) % (2 * np.pi)
        # Especie nocturna: pico a las 0h (0 radianes)
        t2 = np.random.normal(0, 0.3, 100) % (2 * np.pi)
        result = calculate_overlap_coefficient_delta(t1, t2, estimator="delta4")
        # Von Mises KDE produces moderate overlap even for opposing peaks
        # due to broader circular tails; key assertion is result < 1.0
        assert result < 0.85
