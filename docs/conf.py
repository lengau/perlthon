import datetime
import os

# Project information

project = "Perlthon"
author = "Alex M. Lowe"
copyright = f"{datetime.date.today().year}, {author}"
release = "0.1.0"

# Sidebar documentation title
html_title = project + " documentation"

# Documentation website URL
ogp_site_url = "https://lengau.github.io/perlthon/"
ogp_site_name = project

html_context = {
    "product_page": "github.com/lengau/perlthon",
    "github_url": "https://github.com/lengau/perlthon",
    "repo_default_branch": "master",
    "repo_folder": "/docs/",
    "discourse": "",
    "author": author,
}

extensions = [
    "canonical_sphinx",
]

exclude_patterns = [
    "_build",
    ".venv",
]

rst_epilog = """
.. include:: /reuse/links.txt
"""

