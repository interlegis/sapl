#!/bin/bash

celery multi start 2 -A sapl -l info -Q:1 email_queue -c:1 1 -Q:2 celery -c:2 1 --pidfile=./celery/celery_log/%n.pid --logfile=./celery/celery_log/%n%I.log

echo "Celery started"

while true; do sleep 2; done

echo "Celery finished"
