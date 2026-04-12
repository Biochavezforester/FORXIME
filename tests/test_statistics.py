"""
Tests para el módulo de análisis estadístico de FORXIME/2.
Cubre: Shannon, Simpson, Pielou, riqueza, Bray-Curtis, RAI,
ocupación naive, Royle-Nichols, acumulación de especies, 
co-ocurrencia y estimador Chao1.
"""
import pytest
import numpy as np
import pandas as pd
from modules.statistical_analysis import (
    calculate_shannon_index,
    calculate_simpson_index,
    calculate_species_richness,
    calculate_pielou_evenness,
    calculate_biodiversity_indices,
    calculate_biodiversity_by_site,
    calculate_relative_abundance_index,
    calculate_naive_occupancy,
    check_royle_nichols_assumptions,
    estimate_royle_nichols_simple,
    calculate_species_accumulation_curve,
    calculate_co_occurrence_matrix,
    estimate_sampling_completeness,
)


# ========================== Fixtures ==========================

@pytest.fixture
def sample_dataframe():
    """DataFrame realista con datos de cámaras trampa para pruebas."""
    np.random.seed(42)
    dates = pd.date_range("2025-09-01", periods=90, freq="D")
    records = []
    species_pool = [
        "Odocoileus virginianus", "Lynx rufus", "Pecari tajacu",
        "Nasua narica", "Puma concolor", "Meleagris gallopavo"
    ]
    cameras = {
        "CAM001": ("Sitio_A", 485200, 2645000, "13N"),
        "CAM002": ("Sitio_A", 485205, 2645003, "13N"),
        "CAM003": ("Sitio_B", 486100, 2646200, "13N"),
        "CAM004": ("Sitio_C", 487300, 2644800, "13N"),
        "CAM005": ("Sitio_D", 488500, 2647100, "13N"),
    }
    for cam, (sitio, x, y, zona) in cameras.items():
        n = np.random.randint(20, 50)
        for _ in range(n):
            sp = np.random.choice(species_pool)
            date = np.random.choice(dates)
            records.append({
                "Sitio": sitio,
                "Sitio_Agrupado": sitio,
                "Camara": cam,
                "Coordenada_X_UTM": x,
                "Coordenada_Y_UTM": y,
                "Zona_UTM": zona,
                "Especie_Categoria": sp,
                "Fecha": date,
                "Hora": f"{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}:00",
                "Eventos_Independientes": np.random.choice([1, 1, 2]),
            })
    return pd.DataFrame(records)


# ========================== Shannon Index ==========================

class TestShannonIndex:
    def test_equal_abundances(self):
        """Con abundancias iguales, Shannon = ln(S)."""
        data = [10, 10, 10, 10]
        expected = np.log(4)
        assert calculate_shannon_index(data) == pytest.approx(expected)

    def test_single_species(self):
        """Con una sola especie, Shannon = 0."""
        assert calculate_shannon_index([100]) == pytest.approx(0.0)

    def test_empty_input(self):
        assert calculate_shannon_index([]) == 0

    def test_zeros_only(self):
        assert calculate_shannon_index([0, 0, 0]) == 0

    def test_unequal_abundances(self):
        """Shannon debe ser menor que ln(S) con abundancias desiguales."""
        data = [90, 5, 3, 2]
        result = calculate_shannon_index(data)
        max_h = np.log(4)
        assert 0 < result < max_h

    def test_two_species_known_value(self):
        """Caso verificable: 2 especies [5,5] → Shannon = ln(2)."""
        data = [5, 5]
        expected = -np.log(0.5)
        assert calculate_shannon_index(data) == pytest.approx(expected)


# ========================== Simpson Index ==========================

class TestSimpsonIndex:
    def test_equal_abundances(self):
        data = [10, 10, 10, 10]
        result = calculate_simpson_index(data)
        # Con 4 especies iguales: 1 - D, donde D = 4*9*10 / (40*39) … 
        assert 0.7 < result < 0.8

    def test_single_species(self):
        assert calculate_simpson_index([100]) == pytest.approx(0.0)

    def test_empty_input(self):
        assert calculate_simpson_index([]) == 0

    def test_two_equal_species(self):
        """2 especies con 2 individuos cada una: Simpson = 1 - 4/12 = 0.667."""
        data = [2, 2]
        expected = 1 - (4 / 12)
        assert calculate_simpson_index(data) == pytest.approx(expected)

    def test_range(self):
        """Simpson(1-D) siempre debe estar entre 0 y 1."""
        data = [50, 30, 15, 4, 1]
        result = calculate_simpson_index(data)
        assert 0 <= result <= 1


# ========================== Species Richness ==========================

class TestSpeciesRichness:
    def test_unique_species(self):
        species = ["Jaguar", "Puma", "Ocelote"]
        assert calculate_species_richness(species) == 3

    def test_duplicates(self):
        species = ["Jaguar", "Puma", "Jaguar", "Ocelote"]
        assert calculate_species_richness(species) == 3

    def test_empty(self):
        assert calculate_species_richness([]) == 0

    def test_single(self):
        assert calculate_species_richness(["Jaguar"]) == 1


# ========================== Pielou Evenness ==========================

class TestPielouEvenness:
    def test_perfect_evenness(self):
        """Abundancias iguales → J = 1.0."""
        data = np.array([5, 5, 5, 5])
        assert calculate_pielou_evenness(data) == pytest.approx(1.0)

    def test_single_species(self):
        """Una sola especie → J = 0."""
        assert calculate_pielou_evenness(np.array([10])) == 0

    def test_range(self):
        """Pielou siempre debe estar en [0, 1]."""
        data = np.array([50, 5, 2, 1])
        result = calculate_pielou_evenness(data)
        assert 0 <= result <= 1

    def test_empty_with_zeros(self):
        """Array de ceros → J = 0."""
        assert calculate_pielou_evenness(np.array([0, 0])) == 0


# ========================== Biodiversity Indices (integrated) ===========

class TestBiodiversityIndices:
    def test_returns_all_keys(self, sample_dataframe):
        result = calculate_biodiversity_indices(sample_dataframe)
        expected_keys = {"Shannon", "Simpson", "Richness", "Pielou_Evenness", "Total_Individuals"}
        assert set(result.keys()) == expected_keys

    def test_values_are_numeric(self, sample_dataframe):
        result = calculate_biodiversity_indices(sample_dataframe)
        for key, value in result.items():
            assert isinstance(value, (int, float, np.integer, np.floating)), \
                f"{key} no es numérico: {type(value)}"

    def test_by_site_returns_dataframe(self, sample_dataframe):
        result = calculate_biodiversity_by_site(sample_dataframe)
        assert isinstance(result, pd.DataFrame)
        assert "Sitio" in result.columns
        assert len(result) == sample_dataframe["Sitio_Agrupado"].nunique()


# ========================== RAI ==========================

class TestRelativeAbundanceIndex:
    def test_rai_positive(self, sample_dataframe):
        result = calculate_relative_abundance_index(sample_dataframe)
        assert isinstance(result, pd.DataFrame)
        assert "RAI" in result.columns
        assert (result["RAI"] >= 0).all()

    def test_rai_columns(self, sample_dataframe):
        result = calculate_relative_abundance_index(sample_dataframe)
        assert "Especie" in result.columns
        assert "Eventos_Independientes" in result.columns


# ========================== Naive Occupancy ==========================

class TestNaiveOccupancy:
    def test_occupancy_range(self, sample_dataframe):
        result = calculate_naive_occupancy(sample_dataframe)
        assert (result["Ocupacion_Naive"] >= 0).all()
        assert (result["Ocupacion_Naive"] <= 1).all()

    def test_total_sites_column(self, sample_dataframe):
        result = calculate_naive_occupancy(sample_dataframe)
        expected_total = sample_dataframe["Sitio_Agrupado"].nunique()
        assert (result["Total_Sitios"] == expected_total).all()


# ========================== Royle-Nichols ==========================

class TestRoyleNichols:
    def test_sufficient_data(self):
        """Con datos suficientes, el modelo debe tener éxito."""
        # 15 sitios, 5 ocasiones
        dh = np.random.binomial(1, 0.3, size=(15, 5))
        # Asegurar al menos 10 detecciones
        dh[:5, 0] = 1
        dh[:3, 1] = 1
        result = estimate_royle_nichols_simple(dh)
        assert result["success"] is True
        assert 0 <= result["psi"] <= 1

    def test_insufficient_sites(self):
        dh = np.random.binomial(1, 0.3, size=(3, 5))
        result = estimate_royle_nichols_simple(dh)
        assert result["success"] is False

    def test_insufficient_occasions(self):
        dh = np.random.binomial(1, 0.3, size=(15, 2))
        result = estimate_royle_nichols_simple(dh)
        assert result["success"] is False

    def test_assumptions_check(self):
        dh = np.zeros((12, 4))
        dh[:6, :] = 1
        result = check_royle_nichols_assumptions(dh)
        assert result["sufficient_sites"] is True
        assert result["sufficient_occasions"] is True


# ========================== Species Accumulation ==========================

class TestSpeciesAccumulation:
    def test_monotonically_increasing(self, sample_dataframe):
        result = calculate_species_accumulation_curve(sample_dataframe)
        assert isinstance(result, pd.DataFrame)
        # La curva de acumulación debe ser monótonamente no decreciente
        values = result["Especies_Acumuladas"].values
        assert all(values[i] <= values[i + 1] for i in range(len(values) - 1))

    def test_starts_positive(self, sample_dataframe):
        result = calculate_species_accumulation_curve(sample_dataframe)
        assert result["Especies_Acumuladas"].iloc[0] >= 1


# ========================== Co-occurrence ==========================

class TestCoOccurrence:
    def test_symmetric_matrix(self, sample_dataframe):
        result = calculate_co_occurrence_matrix(sample_dataframe)
        assert isinstance(result, pd.DataFrame)
        # Debe ser simétrica
        np.testing.assert_array_equal(result.values, result.values.T)

    def test_diagonal_is_site_count(self, sample_dataframe):
        """La diagonal de co-ocurrencia debe ser el num de sitios donde aparece la especie."""
        result = calculate_co_occurrence_matrix(sample_dataframe)
        # Diagonal >= 1 para cada especie presente
        assert (np.diag(result.values) >= 1).all()


# ========================== Chao1 Estimator ==========================

class TestSamplingCompleteness:
    def test_completeness_range(self, sample_dataframe):
        result = estimate_sampling_completeness(sample_dataframe, method="chao1")
        assert 0 <= result["completeness_percent"] <= 100

    def test_observed_leq_estimated(self, sample_dataframe):
        result = estimate_sampling_completeness(sample_dataframe, method="chao1")
        assert result["observed_richness"] <= result["estimated_richness"]

    def test_returns_all_keys(self, sample_dataframe):
        result = estimate_sampling_completeness(sample_dataframe, method="chao1")
        expected = {"observed_richness", "estimated_richness",
                    "completeness_percent", "status", "recommendation",
                    "singletons", "doubletons", "method"}
        assert set(result.keys()) == expected
