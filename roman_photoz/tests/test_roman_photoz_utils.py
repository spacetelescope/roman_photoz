import numpy as np
import pytest

from roman_photoz.utils import (
    ROMAN_EXTINCTION_COEFFICIENTS,
    deredden_flux,
    get_extinction_coefficient,
    get_roman_filter_list,
)


def test_extinction_coefficients_values():
    """
    Test purpose: Verify that ROMAN_EXTINCTION_COEFFICIENTS contains all required
    Roman filters with the exact A/SFD values from issue #64.
    """
    expected = {
        "f062": 2.2662,
        "f087": 1.2895,
        "f106": 0.8506,
        "f129": 0.5757,
        "f146": 0.4427,
        "f158": 0.3755,
        "f184": 0.2680,
        "f212": 0.2039,
        "f213": 0.2039,
    }
    for filter_name, coeff in expected.items():
        assert filter_name in ROMAN_EXTINCTION_COEFFICIENTS
        assert ROMAN_EXTINCTION_COEFFICIENTS[filter_name] == pytest.approx(coeff)


def test_get_extinction_coefficient_variations():
    """
    Test purpose: Verify that get_extinction_coefficient handles uppercase,
    lowercase, 'roman_' prefixes, and '.pb' extensions correctly.
    """
    assert get_extinction_coefficient("F062") == pytest.approx(2.2662)
    assert get_extinction_coefficient("f062") == pytest.approx(2.2662)
    assert get_extinction_coefficient("roman/roman_F062.pb") == pytest.approx(2.2662)
    assert get_extinction_coefficient("roman_f158") == pytest.approx(0.3755)
    assert get_extinction_coefficient("F213") == pytest.approx(0.2039)
    assert get_extinction_coefficient("F212") == pytest.approx(0.2039)


def test_get_extinction_coefficient_invalid_filter():
    """
    Test purpose: Verify that get_extinction_coefficient raises KeyError for unrecognized filters.
    """
    with pytest.raises(KeyError, match="Extinction coefficient not found"):
        get_extinction_coefficient("unknown_band")


def test_deredden_flux_zero_ebv():
    """
    Test purpose: Verify that deredden_flux with dust_ebv=0 leaves flux unchanged.
    """
    flux = np.array([100.0, 200.0, 300.0])
    dust_ebv = np.zeros(3)
    dered = deredden_flux(flux, dust_ebv, "f158")
    np.testing.assert_allclose(dered, flux)


def test_deredden_flux_calculation():
    """
    Test purpose: Verify that deredden_flux calculates the exact scaling
    factor flux * 10 ** (dust_ebv * coeff / 2.5).
    """
    flux = np.array([100.0, 200.0])
    dust_ebv = np.array([0.1, 0.2])
    filter_name = "f062"
    coeff = 2.2662
    expected = flux * (10.0 ** (dust_ebv * coeff / 2.5))

    dered = deredden_flux(flux, dust_ebv, filter_name)
    np.testing.assert_allclose(dered, expected)


def test_get_roman_filter_list_coverage():
    """
    Test purpose: Verify that all filters in get_roman_filter_list have valid extinction coefficients.
    """
    filters = get_roman_filter_list()
    for f in filters:
        coeff = get_extinction_coefficient(f)
        assert coeff > 0
