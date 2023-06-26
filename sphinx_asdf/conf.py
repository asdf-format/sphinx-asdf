import datetime
import os
import sys
from pathlib import Path

import numpy
import toml

# Ensure documentation examples are determinstically random.
try:
    numpy.random.seed(int(os.environ["SOURCE_DATE_EPOCH"]))
except KeyError:
    pass

try:
    from sphinx_astropy.conf.v1 import *
except ImportError:
    print("ERROR: the documentation requires the sphinx-astropy package to be installed")
    sys.exit(1)

# -- General configuration ----------------------------------------------------
intersphinx_mapping["pypa-packaging"] = ("https://packaging.python.org/en/latest/", None)
intersphinx_mapping["asdf-standard"] = ("https://asdf-standard.readthedocs.io/en/latest/", None)
intersphinx_mapping["pytest"] = ("https://docs.pytest.org/en/latest/", None)

# This is added to the end of RST files - a good place to put substitutions to
# be used globally.
rst_epilog += """
"""

# -- Options for HTML output ---------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_theme_options = {}

static_dir = os.path.join(os.path.dirname(__file__), "static")
html_logo = f"{static_dir}/logo.png"
html_favicon = f"{static_dir}/logo.ico"
latex_logo = f"{static_dir}/logo.pdf"

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname("__file__")), "sphinxext"))
extensions += ["sphinx_asdf"]
