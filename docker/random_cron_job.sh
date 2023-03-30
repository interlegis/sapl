#!/usr/bin/env bash

SOLR_URL=$1
# Define the interval of time to run the cronjob
RANDOM_MINUTE_MIN=0
RANDOM_MINUTE_MAX=60
RANDOM_HOUR_MIN=0
RANDOM_HOUR_MAX=3

# Generate a random minute within the interval
RANDOM_MINUTE=$((RANDOM % ($RANDOM_MINUTE_MAX-$RANDOM_MINUTE_MIN+1) + $RANDOM_MINUTE_MIN))
RANDOM_HOUR=$((RANDOM % ($RANDOM_HOUR_MAX-$RANDOM_HOUR_MIN+1) + $RANDOM_HOUR_MIN))

# Add the cronjob to the crontab
echo "$RANDOM_MINUTE $RANDOM_HOUR * * * /path/to/command" >> /etc/crontab

# Start the cron daemon
crond -f -L /dev/stdout
