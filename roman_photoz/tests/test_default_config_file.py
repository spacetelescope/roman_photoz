import os
from pathlib import Path
from unittest.mock import patch

import pytest

import lephare as lp
from roman_photoz.default_config_file import CWD, LEPHAREDIR, default_roman_config


def test_lepharedir_environment_variable():
    """Test that LEPHAREDIR is correctly set from environment or fallback."""
    # We need to ensure the module is reloaded after environment changes
    import importlib
    import sys
    
    # Remove the module if it's already imported to ensure a fresh import
    if "roman_photoz.default_config_file" in sys.modules:
        del sys.modules["roman_photoz.default_config_file"]
    
    # Test when environment variable is set
    test_lepharedir = "/test/lephare/dir"
    with patch.dict(os.environ, {"LEPHAREDIR": test_lepharedir}, clear=True):
        import roman_photoz.default_config_file
        assert roman_photoz.default_config_file.LEPHAREDIR == test_lepharedir
        
        # Clean up for next test
        del sys.modules["roman_photoz.default_config_file"]

    # Test fallback to lp.LEPHAREDIR
    with patch.dict(os.environ, {}, clear=True), \
         patch("lephare.LEPHAREDIR", "/fallback/lephare/dir"):
        import roman_photoz.default_config_file
        assert roman_photoz.default_config_file.LEPHAREDIR == "/fallback/lephare/dir"


def test_cwd_is_current_directory():
    """Test that CWD is the current working directory."""
    with patch("os.getcwd", return_value="/mock/current/dir"):
        from importlib import reload
        import roman_photoz.default_config_file
        reload(roman_photoz.default_config_file)
        assert roman_photoz.default_config_file.CWD == "/mock/current/dir"


def test_default_config_contains_required_keys():
    """Test that default_roman_config contains all required configuration keys."""
    required_keys = [
        "FILTER_LIST", "FILTER_REP", "FILTER_FILE",
        "CAT_IN", "CAT_OUT", "PARA_OUT",
        "GAL_LIB", "GAL_LIB_IN", "GAL_LIB_OUT",
        "ZPHOTLIB", "Z_INTERP", "Z_METHOD", "Z_RANGE", "Z_STEP",
    ]
    
    for key in required_keys:
        assert key in default_roman_config, f"Required key '{key}' missing from default_roman_config"


def test_para_out_path_is_valid():
    """Test that PARA_OUT path is a valid path relative to the module."""
    para_out_path = default_roman_config["PARA_OUT"]
    assert isinstance(para_out_path, str)
    
    # Verify it points to an expected location under the package
    path_obj = Path(para_out_path)
    assert "roman_photoz" in path_obj.parts
    assert "data" in path_obj.parts
    assert path_obj.name == "default_roman_output.para"


def test_filter_list_format():
    """Test that FILTER_LIST is properly formatted."""
    filter_list = default_roman_config["FILTER_LIST"]
    
    # Should be a comma-separated list of filter paths
    filters = filter_list.split(",")
    assert len(filters) == 8, "Expected 8 filters in FILTER_LIST"
    
    # Each filter should follow the expected pattern
    for filter_path in filters:
        assert filter_path.startswith("roman/roman_F"), f"Filter {filter_path} doesn't follow naming convention"
        assert filter_path.endswith(".pb"), f"Filter {filter_path} doesn't have .pb extension"


def test_filter_rep_uses_lepharedir():
    """Test that FILTER_REP uses the LEPHAREDIR value."""
    filter_rep = default_roman_config["FILTER_REP"]
    assert LEPHAREDIR in filter_rep
    assert filter_rep == f"{LEPHAREDIR}/filt"


def test_all_variable_contains_default_roman_config():
    """Test that __all__ contains 'default_roman_config'."""
    from roman_photoz.default_config_file import __all__
    assert "default_roman_config" in __all__