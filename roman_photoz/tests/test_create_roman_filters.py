from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from roman_photoz.create_roman_filters import (
    BASE_URL,
    create_files,
    create_path,
    create_roman_phot_par_file,
    download_file,
    read_effarea_file,
    run,
    run_filter_command,
)


@pytest.fixture
def mock_response():
    """Create a mock requests response object."""
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.content = b"Test content"
    return mock


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing filter creation."""
    # Create a basic dataframe with wavelength and filter data
    data = {
        "wavelength": [0.1, 0.2, 0.3],
        "F087": [0.8, 0.9, 0.7],
        "F106": [0.7, 0.8, 0.6],
    }
    return pd.DataFrame(data)


def test_download_file(mock_response):
    """Test the download_file function correctly downloads and saves a file."""
    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("requests.get", return_value=mock_response) as mock_get,
    ):
        url = "http://test.url/file.xlsx"
        dest = "test_file.xlsx"
        download_file(url, dest)

        # Verify the function called the correct URL with timeout
        mock_get.assert_called_once_with(url, timeout=30)
        # Verify response was checked for errors
        mock_response.raise_for_status.assert_called_once()
        # Verify file was opened and written with correct content
        mock_open.assert_called_once_with(dest, "wb")
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(
            mock_response.content
        )


@pytest.mark.parametrize(
    "file_exists, test_file, expected_kwargs, expected_download",
    [
        # Case 1: File exists, no download needed
        (
            True,
            "test_file.xlsx",
            {"header": 1},
            None,
        ),
        # Case 2: File doesn't exist, download needed
        (
            False,
            "test_Roman_effarea_20220101.xlsx",
            {},
            {
                "url": BASE_URL.format("20220101"),
                "dest": Path("test_Roman_effarea_20220101.xlsx").resolve().as_posix(),
            },
        ),
    ],
    ids=["file_exists", "file_download_needed"],
)
def test_read_effarea_file(file_exists, test_file, expected_kwargs, expected_download):
    """Test reading an efficiency area file, with or without downloading it first."""
    mock_df = pd.DataFrame({"wavelength": [1, 2, 3]})

    with patch("pathlib.Path.exists", return_value=file_exists):
        # Set up additional mocks based on whether download is expected
        if file_exists:
            # Simple case: file exists, just mock pandas.read_excel
            with patch("pandas.read_excel", return_value=mock_df) as mock_read_excel:
                result = read_effarea_file(test_file, **expected_kwargs)

                # Verify the function returns the expected DataFrame
                assert result is mock_df
                # Verify read_excel was called with expected parameters
                file_path = Path(test_file).resolve()
                mock_read_excel.assert_called_once_with(file_path, **expected_kwargs)
        else:
            # Complex case: file doesn't exist, mock download_file and pandas.read_excel
            with (
                patch(
                    "roman_photoz.create_roman_filters.download_file"
                ) as mock_download,
                patch("pandas.read_excel", return_value=mock_df) as mock_read_excel,
            ):
                # Create a resolved path for testing
                test_path = Path(test_file).resolve()
                result = read_effarea_file(test_path.as_posix())

                # Verify download was called with correct URL and destination
                mock_download.assert_called_once_with(
                    expected_download["url"], expected_download["dest"]
                )
                # Verify read_excel was called and the function returns the expected DataFrame
                mock_read_excel.assert_called_once()
                assert result is mock_df


def test_create_files(sample_dataframe):
    """Test creating filter files from a DataFrame."""
    test_path = Path("test_path")

    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch(
            "roman_photoz.create_roman_filters.create_roman_phot_par_file"
        ) as mock_create_par,
        patch("roman_photoz.create_roman_filters.create_path", return_value=test_path),
    ):
        create_files(
            sample_dataframe,
        )

        # Verify files were created for each filter column
        assert (
            mock_open.call_count == 2
        )  # One for each filter column (excluding wavelength)

        # Verify create_roman_phot_par_file was called with correct filter list
        mock_create_par.assert_called_once_with(
            ["romanF087.pb", "romanF106.pb"], test_path
        )


def test_create_roman_phot_par_file():
    """Test creating the roman_phot.par file."""
    filter_list = ["filter1.pb", "filter2.pb"]
    filter_rep = Path("test_filter_path")

    with patch("builtins.open", MagicMock()) as mock_open:
        create_roman_phot_par_file(filter_list, filter_rep)

        # Verify file was opened at the correct path
        mock_open.assert_called_once_with(filter_rep / "roman_phot.par", "w")

        # Verify file content contains the filter list and repository path
        file_content = mock_open.return_value.__enter__.return_value.write.call_args[0][
            0
        ]
        assert "FILTER_LIST filter1.pb,filter2.pb" in file_content
        assert f"FILTER_REP {filter_rep.as_posix()}" in file_content
        assert "FILTER_CALIB 0,0" in file_content


def test_create_path_local(monkeypatch):
    """Test that roman-photoz uses local path when LEPHAREDIR is not set."""
    monkeypatch.delenv("LEPHAREDIR", raising=False)
    path = create_path()
    assert path == Path(".").resolve()
    assert path.exists()
    assert path.is_dir()


def test_create_path_lepharedir(monkeypatch, tmp_path):
    """Test that roman-photoz uses LEPHAREDIR environment variable if set."""
    monkeypatch.setenv("LEPHAREDIR", str(tmp_path))
    expected = tmp_path / "filt" / "roman"
    path = create_path()
    assert path == expected.resolve()
    assert path.exists()
    assert path.is_dir()


def test_run_filter_command():
    """Test running the filter command."""
    with (
        patch(
            "roman_photoz.create_roman_filters.create_path",
            return_value=Path("/test/path"),
        ) as mock_create_path,
        patch("roman_photoz.create_roman_filters.Filter") as mock_filter,
    ):
        # Configure the mock Filter instance
        mock_filter_instance = MagicMock()
        mock_filter.return_value = mock_filter_instance

        run_filter_command()

        # Verify create_path was called
        mock_create_path.assert_called_once_with()

        # Verify Filter was instantiated with the correct config file path
        mock_filter.assert_called_once_with(config_file="/test/path/roman_phot.par")

        # Verify run method was called on the Filter instance
        mock_filter_instance.run.assert_called_once()


def test_run():
    """Test the main run function."""
    with (
        patch("roman_photoz.create_roman_filters.read_effarea_file") as mock_read,
        patch("roman_photoz.create_roman_filters.get_auxiliary_data") as mock_get_data,
        patch("roman_photoz.create_roman_filters.create_files") as mock_create_files,
        patch(
            "roman_photoz.create_roman_filters.run_filter_command"
        ) as mock_run_filter,
    ):
        # Configure mock read_effarea_file to return a dataframe
        mock_df = pd.DataFrame({"wavelength": [1, 2, 3]})
        mock_read.return_value = mock_df

        run("test_input.xlsx")

        # Verify read_effarea_file was called with the correct parameters
        mock_read.assert_called_once_with(filename="test_input.xlsx", header=1)

        # Verify get_auxiliary_data was called
        mock_get_data.assert_called_once()

        # Verify create_files was called with the dataframe only
        mock_create_files.assert_called_once_with(data=mock_df)

        # Verify run_filter_command was called with no arguments
        mock_run_filter.assert_called_once_with()
