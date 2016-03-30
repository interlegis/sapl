#!/bin/bash
sudo docker stop sapl_db_1
sudo docker rm sapl_db_1
sudo docker rmi -f postgres
