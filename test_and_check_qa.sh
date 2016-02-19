#!/bin/bash

# QA checks: run this before every commit

py.test
py.test --ds=crud_tests.settings crud_tests
./check_qa.sh
