#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decouple import config
from random import randint

import logging
import sys
import time
import requests
import json
import os
import re

USE_SOLR = config('USE_SOLR', default="False", cast=bool)

SOLR_BASE_URL = config('SOLR_URL', default="http://localhost:8983") + '/solr'
SOLR_UPDATE_URL = f'{SOLR_BASE_URL}/sapl-logs/update?commitWithin=1000'

SOLR_COLLECTION_STATUS = (
    f'{SOLR_BASE_URL}/sapl-logs/admin/ping?distrib=true&wt=json'
)

BATCH_SIZE = 5  # https://lucidworks.com/post/really-batch-updates-solr-2/

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
logger = logging.getLogger('python-indexer.py')
logger.setLevel(logging.INFO)

print(f"The logging of this program is done at {logfilename}")


def exp_backoff(func):
    def inner_func(*args, **kwargs):
        MAX_SLEEP_TIME = 180  # 3 min

        iter = 0

        while True:
            try:
                func(*args, **kwargs)
                break
            except Exception as e:
                logger.error(
                    "Exception: " + str(e)  # +
                    # f"\nError connecting to Solr at {SOLR_CONNECTION_STATUS}
                )

                jitter = randint(0, 10)
                sleep_time = min(2**iter + jitter, MAX_SLEEP_TIME)
                print(f"Retrying in {sleep_time} seconds... ")
                time.sleep(sleep_time)
                iter += 1

    return inner_func


@exp_backoff
def check_solr():
    r = requests.get(SOLR_BASE_URL)
    if r.ok and r.status_code == 200:
        print(f"Solr server at {SOLR_BASE_URL} is up and running...")

    print("Checking collection health...")

    r = requests.get(SOLR_COLLECTION_STATUS)
    data = r.json()
    if r.ok and data['status'] == "OK":
        print("Collection sapl-logs is healthy")


@exp_backoff
def push_to_solr():
    logger.debug(f"Sending {len(payload)} documents to Solr")

    requests.post(
        SOLR_UPDATE_URL,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )


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


if __name__ == '__main__':

    if not USE_SOLR:
        print("Solr não habilitado, saindo de python-indexer.py")
        logger.info(f"USE_SOLR={USE_SOLR}")
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
