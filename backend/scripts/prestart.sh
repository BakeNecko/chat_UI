#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

alembic upgrade head

# alembic revision --autogenerate -m "Init DB"

# Create initial data in DB
python app/initial_data.py
