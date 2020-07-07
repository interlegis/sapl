#!/usr/bin/env bash

# QA checks: run this before every commit

git_project_root=$(git rev-parse --show-toplevel)
cd ${git_project_root}

py.test
py.test --ds=sapl.crud.tests.settings sapl/crud/tests
./scripts/django/check_qa.sh
