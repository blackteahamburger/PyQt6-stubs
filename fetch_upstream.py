"""Fetch the upstream stubs."""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from version import PYQT_VERSIONS

SRC_DIR = Path(__file__).parent.joinpath("PyQt6-stubs-collection")


def download_stubs(download_folder: Path) -> None:
    """Download the stubs and copy them to PyQt6-stubs-collection/{lib} folder."""
    for lib, version in PYQT_VERSIONS.items():
        print(f"Downloading stubs for {lib}")
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "download",
            "-d",
            str(download_folder),
            lib + f"=={version}",
        ])

    # Extract the upstream pyi files
    with tempfile.TemporaryDirectory() as temp_folder_str:
        temp_folder = Path(temp_folder_str)
        print(f"Created temporary directory {temp_folder}")
        for download in download_folder.glob("*.whl"):
            print(f"Extracting file {download}")
            with zipfile.ZipFile(download, "r") as zip_ref:
                zip_ref.extractall(temp_folder)

        # Take every pyi file from all folders and move it to "PyQt6-stubs"
        for folder in temp_folder.glob("*"):
            print(f"Scanning folder for pyi files {folder}")
            for extracted_file in folder.glob("*.pyi"):
                copy_file = SRC_DIR / extracted_file.name
                shutil.copyfile(extracted_file, copy_file)
                subprocess.check_call(["git", "add", str(copy_file)])


if __name__ == "__main__":
    shutil.rmtree(SRC_DIR, ignore_errors=True)
    SRC_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dwld_folder:
        download_stubs(Path(temp_dwld_folder))
