import pytest
import numpy as np
import pandas as pd
from modules.statistical_analysis import (
    calculate_shannon_index,
    calculate_simpson_index,
    calculate_species_richness,
    calculate_pielou_evenness
)

def test_calculate_shannon_index():
    # Dataset simple: 2 especies con 5 individuos cada una
    data = [5, 5]
    # Shannon = -(0.5 * ln(0.5) + 0.5 * ln(0.5)) = -ln(0.5) = 0.6931...
    expected = -np.log(0.5)
    assert calculate_shannon_index(data) == pytest.approx(expected)

def test_calculate_shannon_empty():
    assert calculate_shannon_index([]) == 0
    assert calculate_shannon_index([0, 0]) == 0

def test_calculate_simpson_index():
    # Dataset: 2 especies con 2 individuos cada una
    # n = 4, sum(n(n-1)) = 2(2-1) + 2(2-1) = 2 + 2 = 4
    # D = 4 / (4 * 3) = 4 / 12 = 0.333...
    # Simpson (1-D) = 0.666...
    data = [2, 2]
    expected = 1 - (4 / 12)
    assert calculate_simpson_index(data) == pytest.approx(expected)

def test_calculate_species_richness():
    species = ["Jaguar", "Puma", "Jaguar", "Ocelote"]
    assert calculate_species_richness(species) == 3

def test_calculate_pielou_evenness():
    # Equidad perfecta: [5, 5] should be 1.0
    data = [5, 5]
    assert calculate_pielou_evenness(np.array(data)) == pytest.approx(1.0)
    
    # Solo una especie: should be 0.0
    assert calculate_pielou_evenness(np.array([10])) == 0
