#!/usr/bin/env python
'''
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
'''
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
