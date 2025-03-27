====================
Create Roman Filters
====================

This module provides functionality to process Roman Space Telescope filter data, create individual filter files, and generate a configuration file for use with `rail+lephare`.

Functions
---------

.. function:: download_file(url: str, dest: str)

    Download a file from the specified URL and save it to the destination path.

    :param url: The URL of the file to download.
    :type url: str
    :param dest: The destination path where the file will be saved.
    :type dest: str

.. function:: read_effarea_file(filename: str = "", **kwargs) -> pandas.DataFrame

    Read the efficiency area file into a pandas DataFrame. If the file does not exist, it will be downloaded from the specified URL.

    :param filename: The path to the efficiency area file. If not provided, the default filename will be used.
    :type filename: str, optional
    :param kwargs: Additional keyword arguments to pass to `pandas.read_excel`.
    :return: The data from the efficiency area file.
    :rtype: pandas.DataFrame

.. function:: create_files(data: pandas.DataFrame, filepath: str = "")

    Create filter files from the provided DataFrame. Each filter file contains wavelength and filter data, with a comment line at the top.

    :param data: The DataFrame containing the filter data.
    :type data: pandas.DataFrame
    :param filepath: The path where the filter files will be saved. If not provided, the current directory will be used.
    :type filepath: str, optional

.. function:: create_roman_phot_par_file(filter_list: list, filter_rep: pathlib.Path)

    Create the `roman_phot.par` file to be used with the filter command.

    :param filter_list: List of filter filenames.
    :type filter_list: list
    :param filter_rep: Path to the directory where the filters are stored.
    :type filter_rep: pathlib.Path

.. function:: create_path(filepath: str = "") -> pathlib.Path

    Create the directory structure for saving filter files.

    :param filepath: The path where the filter files will be saved. If not provided, the current directory will be used.
    :type filepath: str, optional
    :return: The path where the filter files will be saved.
    :rtype: pathlib.Path

.. function:: run_filter_command(config_file_path: str = "")

    Run the filter command to create the filter file needed by `rail+lephare`.

    :param config_file_path: The path to the configuration file that contains the information about the filters.
    :type config_file_path: str, optional

.. function:: run(input_filename: str = "", input_path: str = "")

    Run the process to create filter files and execute the filter command.

    :param input_filename: The filename containing the monochromatic effective area of each filter per column.
    :type input_filename: str
    :param input_path: The path where the results will be saved.
    :type input_path: str

Usage Example
-------------

To use this module, run it as a script with the following command:

.. code-block:: bash

    python create_roman_filters.py <output_path> <input_filename>

- `<output_path>`: The directory where the results will be saved.
- `<input_filename>`: The filename containing the monochromatic effective area of each filter per column.

The script will generate individual filter files and a configuration file (`roman_phot.par`) for use with `rail+lephare`.

