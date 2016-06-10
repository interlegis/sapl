#!/bin/bash

# QA checks: run this before every commit

py.test
py.test --ds=sapl.crud.tests.settings sapl/crud/tests
./check_qa.sh
