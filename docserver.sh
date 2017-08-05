#!/bin/bash
# Starts a web server serving the documentation. Automatically rebuilds
# whenever the source files change. You need to run ./apidocs.sh when you add
# new modules, however.

./apidocs.sh

sphinx-autobuild -p 8080 -H 0.0.0.0 docs docs/_build/html \
    -z configmaster -z utils -z configmaster_project -n "$@"