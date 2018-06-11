#!/bin/bash

git_project_root=$(git rev-parse --show-toplevel)
cd ${git_project_root}

python -c "from sapl.settings import SAPL_APPS; print(*[s.split('.')[-1] for s in SAPL_APPS])" | xargs -t ./manage.py graph_models -d -g -o zzz.png -l fdp
