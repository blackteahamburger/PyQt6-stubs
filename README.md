# Stubs for the PyQt6 framework and its extensions.

This repository holds the stubs of the PyQt6 framework and its extensions. The stubs are based on the stubs
which are delivered with the PyQt6 packages.

# Generation of stubs

Stubs are generated by running `generate_upstream.py`. It will download the latest PyQt6 release, extract the stubs, do some fixes to them and run `ruff` to do the final fix and formatting.
