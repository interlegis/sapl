#!/bin/bash

# QA checks: run this before every commit

py.test
./qa_check.sh
