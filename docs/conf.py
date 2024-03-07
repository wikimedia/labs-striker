# -*- coding: utf-8 -*-

from datetime import date

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "Striker"
copyright = "%s, Wikimedia Foundation & contributors" % date.today().year
version = "0.1"
release = version
exclude_patterns = ["_build"]
pygments_style = "sphinx"

html_theme = "nature"
htmlhelp_basename = "Strikerdoc"

autodoc_default_flags = ["members", "private-members", "special-members"]
autodoc_memeber_order = "groupwise"
