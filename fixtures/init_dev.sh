#!/bin/bash
# Load development fixtures

python manage.py loaddata fixtures/auth.yaml
python manage.py loaddata fixtures/configmaster-core.yaml

fixtures/init_repos.sh
