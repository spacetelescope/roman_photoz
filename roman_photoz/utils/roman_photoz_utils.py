from pathlib import Path

from roman_photoz.logger import logger


def read_output_keys(output_keys_filename: str) -> list[str]:
    """
    Read the Roman output keys from the provided file.

    Parameters
    ----------
    output_keys_filename : str
        The filename of the file containing the output keys.

    Returns
    -------
    output_keys : list of str
        List of output key names read from the file.

    Raises
    ------
    FileNotFoundError
        If the output keys file is not found.
    """

    default_output_file = Path(output_keys_filename)

    if not default_output_file.exists():
        logger.error("Output keys file not found.")
        raise FileNotFoundError

    with open(default_output_file) as f:
        output_keys = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    return output_keys
