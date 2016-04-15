#!/bin/bash
set -eou pipefail

# Inserts license headers
# One-off script! Not fully idempotent.

# Generate list of relevant source code files

FILES=$(mktemp)
find . -name '*.py' -not -path '*/migrations*' -not -path '*/contrib/*' > $FILES
find . -name '*.html' >> $FILES

COPYRIGHT="Copyright (C) 2013-2016 Continum AG"
ENCODING="-*- coding: utf8 -*-"

# Remove existing headers

find $(cat $FILES) -exec sed -i '/#!.*python.*/d' '{}' \; 
find $(cat $FILES) -exec sed -i '/# -\*- coding.*/d' '{}' \; 
find $(cat $FILES) -exec sed -i "/$COPYRIGHT/d" '{}' \; 

# Add new headers

find $(cat $FILES | grep '\.py$') -exec sed -i '1s%^%\n%' '{}' \; 
find $(cat $FILES | grep '\.py$') -exec sed -i "1s%^%#\n#   $COPYRIGHT\n#\n%" '{}' \; 
find $(cat $FILES | grep '\.py$') -exec sed -i "1s%^%# $ENCODING\n%" '{}' \; 
find $(cat $FILES | grep '\.py$') -exec sed -i '1s%^%#!/usr/bin/env python2\n%' '{}' \; 

find $(cat $FILES | grep 'templates/.*\.html$') -exec sed -i "1s%^%{# $COPYRIGHT #}\n\n%" '{}' \; 

# Cleanup
rm $FILES
