#!/bin/bash
codespell -w --ignore-words-list="" --quiet-level=2
pyupgrade --py36-plus *py
isort --profile black *.py
black -l 160 *.py
flake8 *.py
