#!/bin/bash
# Load development fixtures

python manage.py loaddata fixtures/auth.yaml
python manage.py loaddata fixtures/configmaster-core.yaml
python manage.py loaddata fixtures/configmaster-devices.yaml

fixtures/init_data.sh
