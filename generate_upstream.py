#!/usr/bin/env python3
#
# Copyright (c) 2025 Blackteahamburger <blackteahamburger@outlook.com>
#
# Modified from https://github.com/python-qt-tools/PyQt6-stubs/blob/main/generate_upstream.py
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.
#
"""Generate the upstream stubs."""

import logging
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import fix
from version import PYQT_VERSIONS

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

SRC_DIR = Path(__file__).parent.joinpath("PyQt6-stubs")


def download_stubs(download_folder: Path) -> None:
    """Download the stubs and copy them to PyQt6-stubs/{lib} folder."""
    for lib, version in PYQT_VERSIONS.items():
        logger.info("Downloading stubs for %s version %s", lib, version)
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
        logger.info("Created temporary directory %s", temp_folder)
        for download in download_folder.glob("*.whl"):
            logger.info("Extracting file %s", download)
            with zipfile.ZipFile(download, "r") as zip_ref:
                zip_ref.extractall(temp_folder)

        # Take every pyi file from all folders and move it to "PyQt6-stubs"
        for folder in temp_folder.glob("*"):
            logger.info("Scanning folder for pyi files %s", folder)
            for extracted_file in folder.glob("*.pyi"):
                copy_file = SRC_DIR / extracted_file.name
                shutil.copyfile(extracted_file, copy_file)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    shutil.rmtree(SRC_DIR, ignore_errors=True)
    SRC_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dwld_folder:
        download_stubs(Path(temp_dwld_folder))

    # Call the fix script to process the downloaded files
    logger.info("Running fix.py to process the downloaded files")
    fix.fix_all()
