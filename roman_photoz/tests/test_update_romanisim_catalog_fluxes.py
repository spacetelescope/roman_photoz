import numpy as np
import pytest
from astropy import units as u
from astropy.table import Table

from roman_photoz.update_romanisim_catalog_fluxes import (
    create_random_catalog,
    njy_to_mgy,
    scale_flux,
    update_fluxes,
)


@pytest.fixture
def sample_table():
    """Fixture: Provides a sample Astropy Table for testing."""
    return Table(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
        }
    )


def test_create_random_catalog_length(sample_table):
    """Test that create_random_catalog returns a table of the requested length."""
    out = create_random_catalog(sample_table, n=3, seed=42)
    assert len(out) == 3


def test_create_random_catalog_reproducibility(sample_table):
    """Test that create_random_catalog is reproducible given the same seed."""
    out1 = create_random_catalog(sample_table, n=2, seed=99)
    out2 = create_random_catalog(sample_table, n=2, seed=99)
    assert np.all(out1["A"] == out2["A"])
    assert np.all(out1["B"] == out2["B"])


def test_njy_to_mgy_scalar():
    """Test njy_to_mgy conversion for a scalar value."""
    flux_njy = 3631e9 * u.nJy  # 1 maggy
    flux_mgy = njy_to_mgy(flux_njy)
    assert np.isclose(flux_mgy.value, 1.0)


def test_njy_to_mgy_array():
    """Test njy_to_mgy conversion for an array of values."""
    flux_njy = np.array([3631e9, 7262e9]) * u.nJy
    flux_mgy = njy_to_mgy(flux_njy)
    assert np.allclose(flux_mgy.value, [1.0, 2.0])


def test_scale_flux_default():
    """Test scale_flux returns the original flux when no scaling factor is provided."""
    flux = np.array([1, 2, 3])
    scaled = scale_flux(flux)
    assert np.allclose(scaled, flux)


def test_scale_flux_with_factor():
    """Test scale_flux applies the provided scaling factor correctly."""
    flux = np.array([1, 2, 3])
    factor = np.array([2, 0.5, 1])
    scaled = scale_flux(flux, factor)
    assert np.allclose(scaled, [2, 1, 3])


def test_update_fluxes(monkeypatch):
    """Test update_fluxes updates flux columns and copies label/redshift columns, including fudge_factor and scaling."""
    # Patch get_roman_filter_list to return a fixed list
    monkeypatch.setattr(
        "roman_photoz.utils.get_roman_filter_list",
        lambda uppercase=True: ["F213", "F184"],
    )
    target = Table({"F213": [1.0, 2.0], "F184": [3.0, 4.0]})
    flux = Table(
        {
            "segment_f213_flux": [1e9, 2e9] * u.Unit("nJy"),
            "segment_f184_flux": [3e9, 4e9] * u.Unit("nJy"),
            "label": [10, 20],
            "redshift_true": [0.1, 0.2],
        }
    )
    fudge_factor = 100

    # Test without scaling
    updated = update_fluxes(target, flux)
    assert "label" in updated.colnames
    assert "redshift_true" in updated.colnames
    assert np.all(updated["label"] == [10, 20])
    np.testing.assert_allclose(
        np.asarray(updated["F184"]),
        njy_to_mgy(flux["segment_f184_flux"]).value * fudge_factor,
    )
    np.testing.assert_allclose(
        np.asarray(updated["F213"]), np.asarray(target["F213"]) * fudge_factor
    )

    # Test with scaling
    updated_scaled = update_fluxes(target, flux, apply_scaling=True, ref_filter="F213")
    # Compute scaling factor
    ref_target_vals = np.asarray(target["F213"])
    ref_flux_vals = np.asarray(njy_to_mgy(flux["segment_f213_flux"]))
    scaling_factor = ref_target_vals / ref_flux_vals
    expected_f184 = scale_flux(
        njy_to_mgy(flux["segment_f184_flux"]).value * fudge_factor, scaling_factor
    )
    np.testing.assert_allclose(np.asarray(updated_scaled["F184"]), expected_f184)
    # F213 should still be target * fudge_factor
    np.testing.assert_allclose(
        np.asarray(updated_scaled["F213"]), np.asarray(target["F213"]) * fudge_factor
    )


def test_process_catalog_return_vs_save(tmp_path, monkeypatch):
    """
    Test that SimulatedCatalog.process() can either return the catalog to memory or save it to a file,
    and that update_fluxes raises an error if the catalog is not returned.
    """

    # Dummy SimulatedCatalog with process method
    class DummySimulatedCatalog:
        def __init__(self, table):
            self.table = table

        def process(self, return_catalog=False, output_path=None):
            if return_catalog:
                return self.table
            elif output_path:
                self.table.write(output_path)
                return None
            else:
                return None

    # Create a dummy table
    table = Table({"F213": [1.0], "F184": [2.0], "label": [1], "redshift_true": [0.1]})
    simcat = DummySimulatedCatalog(table)

    # Test returning catalog to memory
    returned = simcat.process(return_catalog=True)
    assert isinstance(returned, Table)
    assert np.all(returned["F213"] == [1.0])

    # Test saving to file
    output_file = tmp_path / "test_catalog.fits"
    result = simcat.process(return_catalog=False, output_path=output_file)
    assert result is None
    assert output_file.exists()

    # Test update_fluxes raises error if catalog is not returned
    with pytest.raises(ValueError):
        update_fluxes(table, None)
