from unittest.mock import MagicMock, patch

import pytest
from astropy.table import Table

from roman_photoz.default_config_file import default_roman_config
from roman_photoz.roman_catalog_process import RomanCatalogProcess


@pytest.fixture
def roman_catalog_process():
    """Create a basic RomanCatalogProcess instance for testing"""
    return RomanCatalogProcess(config_filename=default_roman_config)


class TestRomanCatalogProcess:
    """Test class for the RomanCatalogProcess"""

    def test_init_with_default_model_filename(self):
        """Test initialization with default model filename"""
        rcp = RomanCatalogProcess(config_filename=default_roman_config)
        assert rcp.model_filename == "roman_model.pkl"
        assert "roman_model.pkl" in rcp.informer_model_path

    def test_init_with_custom_model_filename(self):
        """Test initialization with custom model filename"""
        custom_model = "custom_model.pkl"
        rcp = RomanCatalogProcess(
            config_filename=default_roman_config, model_filename=custom_model
        )
        assert rcp.model_filename == custom_model
        assert custom_model in rcp.informer_model_path

    @pytest.mark.parametrize("file_exists, expected", [(True, True), (False, False)])
    @patch("os.path.exists")
    def test_informer_model_exists(self, mock_path_exists, file_exists, expected):
        """Test the informer_model_exists property with different file existence states"""
        mock_path_exists.return_value = file_exists
        rcp = RomanCatalogProcess(config_filename=default_roman_config)
        assert rcp.informer_model_exists is expected

    @patch("roman_photoz.roman_catalog_process.LephareInformer")
    def test_create_informer_stage_uses_correct_model(self, mock_informer):
        """Test that create_informer_stage uses the correct model path"""
        # Setup the mock
        mock_stage = MagicMock()
        mock_informer.make_stage.return_value = mock_stage

        # Create RCP with custom model
        custom_model = "special_model.pkl"
        rcp = RomanCatalogProcess(
            config_filename=default_roman_config, model_filename=custom_model
        )

        # Add required attributes for create_informer_stage
        rcp.flux_cols = ["flux_F158"]
        rcp.flux_err_cols = ["flux_err_F158"]
        rcp.data = {}

        # Call the method
        rcp.create_informer_stage()

        # Check that the correct model path was used
        call_args = mock_informer.make_stage.call_args[1]
        assert custom_model in call_args["model"]

        # Check that inform was called
        mock_stage.inform.assert_called_once()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("roman_photoz.roman_catalog_process.RomanCatalogProcess")
    def test_main_function_passes_correct_args(self, mock_rcp_class, mock_parse_args):
        """Test that the main() function in the roman_catalog_process.py module
        is initialized correctly and that it correctly passes command-line
        arguments to the RomanCatalogProcess class and its methods"""
        from roman_photoz.roman_catalog_process import main

        # Setup mock args
        mock_args = MagicMock()
        mock_args.config_filename = ""
        mock_args.model_filename = "test_model.pkl"
        mock_args.input_path = "test_path"
        mock_args.input_filename = "test_input.asdf"
        mock_args.output_path = "test_output_path"
        mock_args.output_filename = "test_output.asdf"
        mock_args.save_results = True
        mock_parse_args.return_value = mock_args

        # Setup mock rcp instance
        mock_rcp = MagicMock()
        mock_rcp_class.return_value = mock_rcp

        # Call main
        main([])

        # Check that RomanCatalogProcess was initialized with the correct model_filename
        mock_rcp_class.assert_called_once_with(
            config_filename=mock_args.config_filename,
            model_filename=mock_args.model_filename,
        )

        # Check that process was called with the correct arguments
        mock_rcp.process.assert_called_once_with(
            input_filename=mock_args.input_filename,
            input_path=mock_args.input_path,
            output_filename=mock_args.output_filename,
            output_path=mock_args.output_path,
            save_results=mock_args.save_results,
        )

    @pytest.mark.parametrize(
        "model_exists, should_create_informer",
        [
            (
                False,
                True,
            ),  # When model doesn't exist, create_informer_stage should be called
            (
                True,
                False,
            ),  # When model exists, create_informer_stage should NOT be called
        ],
    )
    @patch("os.path.exists")
    @patch(
        "roman_photoz.roman_catalog_process.RomanCatalogProcess.create_informer_stage"
    )
    @patch(
        "roman_photoz.roman_catalog_process.RomanCatalogProcess.create_estimator_stage"
    )
    def test_process_model_existence(
        self,
        mock_create_estimator,
        mock_create_informer,
        mock_exists,
        model_exists,
        should_create_informer,
    ):
        """Test that the process method handles model existence correctly"""
        # Setup mock to indicate model existence
        mock_exists.return_value = model_exists

        # Create RCP instance
        rcp = RomanCatalogProcess(config_filename=default_roman_config)

        # Mock get_data and format_data
        rcp.get_data = MagicMock(return_value=Table())
        rcp.format_data = MagicMock()

        # Call process method but do not save results
        rcp.process(save_results=False)

        # Verify create_informer_stage was called or not based on model existence
        if should_create_informer:
            mock_create_informer.assert_called_once()
        else:
            mock_create_informer.assert_not_called()

        # Verify create_estimator_stage was always called
        mock_create_estimator.assert_called_once()
