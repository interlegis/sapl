#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
import requests
import json
import time
import re

# TODO: inserir timestamp no logging do python-indexer.py

USE_SOLR = os.getenv('USE_SOLR', True)  # TODO: trocar por False em produção
SOLR_BASE_URL = os.getenv('SOLR_URL', 'http://localhost:8983') + '/solr'

SOLR_UPDATE_URL = f'{SOLR_BASE_URL}/sapl-logs/update?commitWithin=1000'

SOLR_COLLECTION_STATUS = (
    f'{SOLR_BASE_URL}/sapl-logs/admin/ping?distrib=true&wt=json'
)

BATCH_SIZE = 10  # https://lucidworks.com/post/really-batch-updates-solr-2/

previous = None

buffer = []
payload = []

num_docs = 0
total_docs = 0

# logging setup
logfilename = 'python-indexer.log'

logging.basicConfig(
    filename=logfilename,
    filemode='w+',
    level=logging.INFO
)

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger = logging.getLogger('python-indexer')
logger.setLevel(logging.DEBUG)

print(f"The logging of this program is done at {logfilename}")


def push_to_solr():
    logger.debug(f"Sending {len(payload)} documents to Solr")

    r = requests.post(
        SOLR_UPDATE_URL,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )
    logger.debug(r.content)


def parse_fields(groups):
    from datetime import datetime as dt

    iso8601 = "{} {}".format(groups[1], groups[2].replace(",", "."))
    d = dt.fromisoformat(iso8601)
    datetime = d.strftime('%Y-%m-%dT%H:%M:%SZ')

    # datetime = groups[1] + "T" + groups[2].split(',')[0] + "Z"

    fields = {
        'level': groups[0],
        'datetime': datetime
    }

    parts = groups[3].split()
    fields['server'] = parts[0]
    fields['path'] = parts[1]

    # format: sapl.painel.views:get_votos:497
    function = parts[2].split(':')
    fields['app_file'] = function[0]
    fields['method'] = function[1]
    fields['line_number'] = function[2]
    fields['function'] = parts[2]

    fields['message'] = ' '.join(parts[3:])

    return fields


def parse_logs(line):
    global previous

    # discard empty lines
    if not line.strip():
        return

    pattern = (
        "^(ERROR|INFO|DEBUG|WARNING)" +
        r'\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2},\d+)\s+(.*)'
    )
    match = re.match(pattern, line)

    if match:
        groups = match.groups()
        fields = parse_fields(groups)
        fields['line'] = line

        # if match but buffer is full then there was a stack trace before
        if buffer and previous:
            previous['stacktrace'] = ''.join(buffer)
            buffer.clear()
        elif not previous:
            buffer.clear()  # un-garbaged trash

        # append the previous one
        if previous:
            payload.append(previous)

        # delay append of current (it may have stacktrace)
        previous = fields
    else:
        # while not match again collect into buffer
        buffer.append(line)

    logger.debug(len(payload))


def follow(fd):
    """ generator function that yields new lines in a file """

    # seek the end of the file
    fd.seek(0, os.SEEK_END)

    # start infinite loop
    while True:
        # read last line of file
        line = fd.readline()
        # sleep if file hasn't been updated
        if not line:
            time.sleep(0.1)
            continue

        yield line


def check_solr():
    try:
        r = requests.get(SOLR_BASE_URL)
        if r.status_code == 200:
            print(f"Solr server at {SOLR_BASE_URL} is up and running...")

        print("Checking collection health...")

        r = requests.get(SOLR_COLLECTION_STATUS)
        data = r.json()
        if data['status'] == 'OK':
            print("Collection sapl-logs is healthy")

    except Exception as e:
        logger.error(
            "Exception: " + str(e) +
            f"\nError connecting to Solr at {SOLR_COLLECTION_STATUS}"
        )
        sys.exit(1)


if __name__ == '__main__':

    if not USE_SOLR:
        print(f"USE_SOLR={USE_SOLR}")
        sys.exit(0)

    check_solr()

    filename = sys.argv[1]
    print(f"Opening log file {filename}...")
    logfile = open(filename, 'r')
    loglines = follow(logfile)

    # iterate over the generator
    for line in loglines:
        logger.debug(f"Current payload size: {len(payload)}")
        parse_logs(line)

        num_docs = (num_docs + 1) % BATCH_SIZE
        if num_docs == 0 and payload:
            push_to_solr()
            total_docs += len(payload)
            payload.clear()

    push_to_solr()
