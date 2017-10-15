#!/bin/bash
# Generate sphinx-apidocs scaffolding. You need to run this whenever new
# modules are added to the project.

set -euo pipefail

rm -rf docs/api/*

export SPHINX_APIDOC_OPTIONS='members,undoc-members,show-inheritance,private-members'

sphinx-apidoc -f -o docs/api . \
    configmaster_project \
    configmaster/migrations utils/contrib *.py docs \
    configmaster/admin.py \
    configmaster/models.py \
    configmaster/tests.py \
    configmaster/urls.py \
    configmaster/views.py \
    -H "Internal API docs" --private \
    --module-first \
    "$@"