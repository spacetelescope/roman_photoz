"""Test data management for regression tests using data from artifactory."""

import filecmp
import hashlib
import json
import os
import pprint
import shutil
from datetime import datetime
from difflib import unified_diff
from pathlib import Path

from ci_watson.artifactory_helpers import BigdataError, get_bigdata, get_bigdata_root

# Define location of default Artifactory API key, for Jenkins use only
ARTIFACTORY_API_KEY_FILE = "/eng/ssb2/keys/svc_rodata.key"

# Define a request timeout in seconds
TIMEOUT = 30

# Define cache directory in user's home
CACHE_DIR = os.path.expanduser("~/.cache/roman_photoz/regtest")


class RegtestData:
    """Handles regression test data retrieved from artifactory."""

    def __init__(
        self,
        env="dev",
        inputs_root="roman-pipeline",
        results_root="roman-pipeline-results/regression-tests/runs/",
        docopy=True,
        input=None,
        input_remote=None,
        output=None,
        truth=None,
        truth_remote=None,
        remote_results_path=None,
        test_name=None,
        traceback=None,
        use_cache=True,
        **kwargs,
    ):
        self._env = env
        self._inputs_root = inputs_root
        self._results_root = results_root
        self._bigdata_root = get_bigdata_root()
        self._cache_enabled = use_cache
        self._cache_dir = Path(CACHE_DIR)

        self.docopy = docopy

        # Initialize @property attributes
        self.input = input
        self.input_remote = input_remote
        self.output = output
        self.truth = truth
        self.truth_remote = truth_remote

        # No @properties for the following attributes
        self.remote_results_path = remote_results_path
        self.test_name = test_name
        self.traceback = traceback

        # Initialize cache if enabled
        if self._cache_enabled:
            self._init_cache()

    def __repr__(self):
        return pprint.pformat(
            dict(
                input=self.input,
                output=self.output,
                truth=self.truth,
                input_remote=self.input_remote,
                truth_remote=self.truth_remote,
                remote_results_path=self.remote_results_path,
                test_name=self.test_name,
                traceback=self.traceback,
            ),
            indent=1,
        )

    @property
    def input_remote(self):
        if self._input_remote is not None:
            return os.path.join(*self._input_remote)
        else:
            return None

    @input_remote.setter
    def input_remote(self, value):
        if value:
            self._input_remote = value.split(os.sep)
        else:
            self._input_remote = value

    @property
    def truth_remote(self):
        if self._truth_remote is not None:
            return os.path.join(*self._truth_remote)
        else:
            return None

    @truth_remote.setter
    def truth_remote(self, value):
        if value:
            self._truth_remote = value.split(os.sep)
        else:
            self._truth_remote = value

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        if value:
            self._input = os.path.abspath(value)
        else:
            self._input = value

    @property
    def truth(self):
        return self._truth

    @truth.setter
    def truth(self, value):
        if value:
            self._truth = os.path.abspath(value)
        else:
            self._truth = value

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value):
        if value:
            self._output = os.path.abspath(value)
        else:
            self._output = value

    @property
    def bigdata_root(self):
        return self._bigdata_root

    @property
    def cache_enabled(self):
        """Get the current cache status."""
        return self._cache_enabled

    @cache_enabled.setter
    def cache_enabled(self, value):
        """Enable or disable the cache."""
        if value and not self._cache_enabled:
            self._cache_enabled = True
            self._init_cache()
        else:
            self._cache_enabled = value

    # Cache management methods
    def _init_cache(self):
        """Initialize the cache directory and metadata."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_index_file = self._cache_dir / "cache_index.json"

        # Load or create cache index
        if self._cache_index_file.exists():
            try:
                with open(self._cache_index_file) as f:
                    self._cache_index = json.load(f)
            except (json.JSONDecodeError, OSError):
                # If index is corrupted, create a new one
                self._cache_index = {}
        else:
            self._cache_index = {}

    def _get_file_hash(self, filepath):
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_cached_file(self, remote_path):
        """Get a file from cache if available and valid."""
        if not self._cache_enabled:
            return None

        cache_key = f"{self._inputs_root}/{self._env}/{remote_path}"
        cache_info = self._cache_index.get(cache_key)

        if cache_info:
            cached_file = self._cache_dir / cache_info["cache_path"]
            if cached_file.exists():
                return str(cached_file)

            # For backward compatibility with old cache format
            # that used hash prefixes instead of subdirectories
            if "_" in cache_info["cache_path"]:
                old_style_path = self._cache_dir / cache_info["cache_path"]
                if old_style_path.exists():
                    return str(old_style_path)

        return None

    def _cache_file(self, local_path, remote_path):
        """Add a file to the cache.

        File is stored in a structure that preserves original filename while
        ensuring uniqueness by using hash-based subdirectories.
        """
        if not self._cache_enabled:
            return

        cache_key = f"{self._inputs_root}/{self._env}/{remote_path}"

        # Create a hash of the full path to use as a subdirectory
        path_hash = hashlib.sha256(cache_key.encode()).hexdigest()[:8]
        cache_subdir = self._cache_dir / path_hash
        cache_subdir.mkdir(exist_ok=True)

        # Use original filename within the hash-based subdirectory
        filename = os.path.basename(local_path)
        cached_file = cache_subdir / filename

        # Copy file to cache
        shutil.copy2(local_path, cached_file)

        # Store relative path from cache_dir
        rel_path = os.path.join(path_hash, filename)

        # Update cache index
        self._cache_index[cache_key] = {
            "cache_path": rel_path,
            "hash": self._get_file_hash(local_path),
            "timestamp": str(datetime.now()),
        }

        # Save updated index
        with open(self._cache_index_file, "w") as f:
            json.dump(self._cache_index, f, indent=2)

    def clear_cache(self):
        """Clear the entire cache directory."""
        if self._cache_enabled and self._cache_dir.exists():
            for item in self._cache_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            # Recreate index
            self._cache_index = {}
            with open(self._cache_index_file, "w") as f:
                json.dump(self._cache_index, f, indent=2)

    def cache_info(self):
        """Return information about the cache."""
        if not self._cache_enabled:
            return {"enabled": False}

        # Count files and calculate size
        file_count = 0
        total_size = 0

        # Recursively walk through cache directory
        for root, dirs, files in os.walk(self._cache_dir):
            root_path = Path(root)
            for file in files:
                if file != "cache_index.json":
                    file_path = root_path / file
                    file_count += 1
                    total_size += file_path.stat().st_size

        return {
            "enabled": True,
            "location": str(self._cache_dir),
            "files": file_count,
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
        }

    # The methods
    def get_data(self, path=None, docopy=None, use_cache=None):
        """Copy data from Artifactory remote resource to the CWD

        Updates self.input and self.input_remote upon completion

        Parameters
        ----------
        path : str, optional
            Remote path to the data file
        docopy : bool, optional
            Whether to copy the file locally
        use_cache : bool, optional
            Whether to use cached data if available
        """
        if path is None:
            path = self.input_remote
        else:
            self.input_remote = path

        if docopy is None:
            docopy = self.docopy

        if use_cache is None:
            use_cache = self._cache_enabled

        # Get original filename from path
        original_filename = os.path.basename(path)

        # Try to get from cache first
        if use_cache:
            cached_file = self._get_cached_file(path)
            if cached_file:
                if docopy:
                    # Copy from cache to current directory with original filename
                    shutil.copy2(cached_file, original_filename)
                    self.input = os.path.abspath(original_filename)
                else:
                    self.input = cached_file
                self.input_remote = os.path.join(self._inputs_root, self._env, path)
                return self.input

        # If not in cache or cache disabled, get from Artifactory
        self.input = get_bigdata(self._inputs_root, self._env, path, docopy=docopy)
        self.input_remote = os.path.join(self._inputs_root, self._env, path)

        # Add to cache if enabled
        if use_cache and docopy:
            self._cache_file(self.input, path)

        return self.input

    def get_truth(self, path=None, docopy=None, use_cache=None):
        """Copy truth data from Artifactory remote resource to the CWD/truth

        Updates self.truth and self.truth_remote on completion

        Parameters
        ----------
        path : str, optional
            Remote path to the truth file
        docopy : bool, optional
            Whether to copy the file locally
        use_cache : bool, optional
            Whether to use cached data if available
        """
        if path is None:
            path = self.truth_remote
        else:
            self.truth_remote = path

        if docopy is None:
            docopy = self.docopy

        if use_cache is None:
            use_cache = self._cache_enabled

        # Get original filename from path
        original_filename = os.path.basename(path)

        os.makedirs("truth", exist_ok=True)
        os.chdir("truth")

        try:
            # Try cache first
            if use_cache:
                cached_file = self._get_cached_file(path)
                if cached_file:
                    if docopy:
                        # Copy from cache to current directory with original filename
                        shutil.copy2(cached_file, original_filename)
                        self.truth = os.path.abspath(original_filename)
                    else:
                        self.truth = cached_file
                    self.truth_remote = os.path.join(self._inputs_root, self._env, path)
                    os.chdir("..")
                    return self.truth

            # If not in cache or cache disabled, get from Artifactory
            self.truth = get_bigdata(self._inputs_root, self._env, path, docopy=docopy)
            self.truth_remote = os.path.join(self._inputs_root, self._env, path)

            # Add to cache if enabled
            if use_cache and docopy:
                self._cache_file(self.truth, path)

        except BigdataError:
            os.chdir("..")
            raise

        os.chdir("..")
        return self.truth

    def compare_files(self, output_file, truth_file):
        """Compare output file with truth file, providing detailed difference information.

        This implementation provides detailed differences between files for both text
        and binary files. For text files, it shows exact line differences using unified diff.
        For binary files, it provides size and basic difference information.

        Parameters
        ----------
        output_file : str
            Path to the output file generated by the test

        truth_file : str
            Path to the truth file to compare against

        Returns
        -------
        bool
            True if files match, False otherwise

        Raises
        ------
        FileNotFoundError
            If either file is missing
        AssertionError
            If files don't match, with detailed diff information
        """
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Output file not found: {output_file}")
        if not os.path.exists(truth_file):
            raise FileNotFoundError(f"Truth file not found: {truth_file}")

        # First try binary comparison
        if filecmp.cmp(output_file, truth_file, shallow=False):
            return True

        # If binary comparison fails, try to generate a readable diff
        try:
            with open(output_file) as f1, open(truth_file) as f2:
                output_lines = f1.readlines()
                truth_lines = f2.readlines()

            diff = list(
                unified_diff(
                    truth_lines,
                    output_lines,
                    fromfile=os.path.basename(truth_file),
                    tofile=os.path.basename(output_file),
                    lineterm="",
                )
            )

            if diff:
                # Get file sizes for additional context
                output_size = os.path.getsize(output_file)
                truth_size = os.path.getsize(truth_file)

                # Format a detailed error message
                diff_msg = "\n".join(
                    [
                        "Text files differ:",
                        f"Output file: {output_file} ({output_size:,} bytes)",
                        f"Truth file:  {truth_file} ({truth_size:,} bytes)",
                        "Line differences:",
                        *diff[:50],  # Show first 50 lines of diff
                    ]
                )

                # If there are more differences, indicate this
                if len(diff) > 50:
                    diff_msg += f"\n... and {len(diff) - 50} more differences"

                raise AssertionError(diff_msg)

            return True

        except UnicodeDecodeError:
            # For binary files, provide size and basic hash information
            output_size = os.path.getsize(output_file)
            truth_size = os.path.getsize(truth_file)

            # Get hashes for additional diagnostic info
            output_hash = self._get_file_hash(output_file)
            truth_hash = self._get_file_hash(truth_file)

            diff_msg = "\n".join(
                [
                    "Binary files differ:",
                    f"Output file: {output_file}",
                    f"  Size: {output_size:,} bytes",
                    f"  SHA256: {output_hash}",
                    f"Truth file: {truth_file}",
                    f"  Size: {truth_size:,} bytes",
                    f"  SHA256: {truth_hash}",
                    f"Size difference: {abs(output_size - truth_size):,} bytes",
                ]
            )
            raise AssertionError(diff_msg)
