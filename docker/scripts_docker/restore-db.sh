#!/bin/bash
sudo pg_restore --disable-triggers --data-only sapl_30-03-16.tar | docker exec -i sapl_localhost_1 psql -U sapl
