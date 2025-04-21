from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from roman_photoz.roman_catalog_handler import RomanCatalogHandler


@pytest.fixture
def mock_catalog_data(roman_catalog_handler):
    """Create mock catalog data for testing"""
    # Get the actual filter names used by the handler
    filter_names = roman_catalog_handler.filter_names

    # Create fields dynamically based on actual filter names
    field_list = [("id", "i4")]
    for name in filter_names:
        field_name = f"{name.replace('roman_', '')}_flux_psf"
        field_err_name = f"{name.replace('roman_', '')}_flux_psf_err"
        field_list.append((field_name, "f8"))
        field_list.append((field_err_name, "f8"))

    field_list.extend([("context", "i4"), ("zspec", "f8"), ("string_data", "S20")])

    dt = np.dtype(field_list)

    # Create sample data
    data = np.zeros(3, dtype=dt)
    data["id"] = [1, 2, 3]
    data["context"] = [1, 1, 2]
    data["zspec"] = [0.5, 1.0, 1.5]
    data["string_data"] = [b"source1", b"source2", b"source3"]

    # Add test values for each filter field
    for i, name in enumerate(filter_names):
        field_name = f"{name.replace('roman_', '')}_flux_psf"
        field_err_name = f"{name.replace('roman_', '')}_flux_psf_err"
        data[field_name] = [100.0 + i * 10, 150.0 + i * 10, 200.0 + i * 10]
        data[field_err_name] = [5.0 + i * 0.5, 7.5 + i * 0.5, 10.0 + i * 0.5]

    return data


@pytest.fixture
def roman_catalog_handler():
    """Create a basic RomanCatalogHandler instance for testing"""
    return RomanCatalogHandler("test_catalog.asdf")


class TestRomanCatalogHandler:
    """Test class for the RomanCatalogHandler"""

    def test_init_default(self):
        """Test initialization with default parameters"""
        handler = RomanCatalogHandler()
        assert handler.cat_name == ""
        assert handler.cat_array is None
        assert handler.catalog is None
        assert handler.cat_temp_filename == "cat_temp_file.csv"
        assert isinstance(handler.filter_names, list)
        assert len(handler.filter_names) > 0

    def test_init_with_catalog(self):
        """Test initialization with a catalog name"""
        catalog_name = "test_catalog.asdf"
        handler = RomanCatalogHandler(catalog_name)
        assert handler.cat_name == catalog_name

    def test_init_filter_list_none(self):
        """Test initialization when filter list is None"""
        with patch(
            "roman_photoz.roman_catalog_handler.default_roman_config"
        ) as mock_config:
            mock_config.get.return_value = None
            with pytest.raises(
                ValueError, match="Filter list not found in default config file"
            ):
                RomanCatalogHandler()

    @patch("roman_photoz.roman_catalog_handler.rdm.open")
    def test_read_catalog(self, mock_open, mock_catalog_data):
        """Test reading a catalog file"""
        # Setup mock
        mock_dm = MagicMock()
        mock_dm.source_catalog.as_array.return_value = mock_catalog_data
        mock_open.return_value = mock_dm

        # Initialize handler and read catalog
        handler = RomanCatalogHandler("test_catalog.asdf")
        handler.read_catalog()

        # Check that the catalog was read correctly
        mock_open.assert_called_once_with("test_catalog.asdf")
        assert handler.cat_array is not None
        assert len(handler.cat_array) == 3
        assert handler.cat_array["id"][0] == 1

    def test_format_catalog(self, roman_catalog_handler, mock_catalog_data):
        """Test formatting a catalog"""
        # Setup
        roman_catalog_handler.cat_array = mock_catalog_data

        # Execute
        roman_catalog_handler.format_catalog()

        # Check that the catalog was formatted correctly
        assert roman_catalog_handler.catalog is not None
        assert "id" in roman_catalog_handler.catalog.dtype.names

        # Check that filter fields were added correctly
        for filter_name in roman_catalog_handler.filter_names:
            flux_field = f"flux_psf_{filter_name}"
            flux_err_field = f"flux_psf_err_{filter_name}"
            assert flux_field in roman_catalog_handler.catalog.dtype.names
            assert flux_err_field in roman_catalog_handler.catalog.dtype.names

        # Check that additional required fields were added
        assert "context" in roman_catalog_handler.catalog.dtype.names
        assert "zspec" in roman_catalog_handler.catalog.dtype.names
        assert "string_data" in roman_catalog_handler.catalog.dtype.names

        # Check that data was copied correctly for a sample field
        assert roman_catalog_handler.catalog["id"][0] == mock_catalog_data["id"][0]
        assert (
            roman_catalog_handler.catalog["zspec"][1] == mock_catalog_data["zspec"][1]
        )

    @patch("roman_photoz.roman_catalog_handler.RomanCatalogHandler.read_catalog")
    @patch("roman_photoz.roman_catalog_handler.RomanCatalogHandler.format_catalog")
    def test_process(
        self,
        mock_format_catalog,
        mock_read_catalog,
        roman_catalog_handler,
        mock_catalog_data,
    ):
        """Test processing a catalog"""
        # Setup
        roman_catalog_handler.catalog = mock_catalog_data

        # Execute
        result = roman_catalog_handler.process()

        # Check that methods were called
        mock_read_catalog.assert_called_once()
        mock_format_catalog.assert_called_once()

        # Check that process returns the catalog
        assert result is roman_catalog_handler.catalog

    @patch("roman_photoz.roman_catalog_handler.rdm.open")
    def test_end_to_end_process(self, mock_open, mock_catalog_data):
        """Test the entire process flow from read to format"""
        # Setup mock
        mock_dm = MagicMock()
        mock_dm.source_catalog.as_array.return_value = mock_catalog_data
        mock_open.return_value = mock_dm

        # Initialize handler
        handler = RomanCatalogHandler("test_catalog.asdf")

        # Process the catalog
        result = handler.process()

        # Check that the catalog was processed correctly
        assert result is not None
        assert "id" in result.dtype.names
        assert "context" in result.dtype.names
        assert "zspec" in result.dtype.names
        assert "string_data" in result.dtype.names


if __name__ == "__main__":
    pytest.main(["-v", "test_roman_catalog_handler.py"])
