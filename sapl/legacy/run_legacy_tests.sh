#!/bin/bash

# All tests under this directory are excluded in default pytest.ini
# To run them use this script in this directory

py.test --ds=sapl.legacy_migration_settings
