#!/bin/bash
source venv/bin/activate
export DEV=1
export PYTHONPATH=$PYTHONPATH:yandex_school
gunicorn -c gunicorn.py.ini app:app