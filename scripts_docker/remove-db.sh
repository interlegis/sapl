#!/bin/bash
sudo docker stop sapl_localhost_1
sudo docker rm sapl_localhost_1
sudo docker rmi -f postgres
