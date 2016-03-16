#!/bin/bash

# QA checks: run this before every commit

py.test
py.test --ds=crud.tests.settings crud/tests
./check_qa.sh
