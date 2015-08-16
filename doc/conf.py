# Sphinx build configuratuion
# ===========================
#
# Copying
# -------
#
# Copyright (c) 2015 propanelib authors and contributors.
#
# This file is part of the *propanelib* project.
#
# propanelib is a free software project. You can redistribute it and/or
# modify if under the terms of the MIT License.
#
# This software project is distributed *as is*, WITHOUT WARRANTY OF ANY
# KIND; including but not limited to the WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE and NONINFRINGEMENT.
#
# You should have received a copy of the MIT License along with
# propanelib. If not, see <http://opensource.org/licenses/MIT>.
#
"""propanelib documentation build configuration file."""
import sys
import os


# General configuration
# ---------------------

# Sphinx extension modules
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinxcontrib.cf3domain',
]

# Templates paths.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'propanelib'
copyright = '2015, propanelib authors'

# The version info for the project. Acts as replacement for
# |version| and |release|.
#
# The short X.Y version.
version = '0.1'
# The full version, including alpha/beta/rc tags.
release = '0.1a'

add_function_parentheses = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The theme to use for HTML and HTML Help pages.
html_theme = 'alabaster'

# Paths that contain custom static files.
html_static_path = ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'propanelibdoc'

