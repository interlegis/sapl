#!/usr/bin/env bash
sudo docker stop $(docker ps -a -q) # Para containers
sudo docker rm $(sudo docker ps -a -q) # Remove containers
sudo docker rmi -f $( sudo docker images -q ) # Remove imagens
sudo docker volume rm $(sudo docker volume ls -q -f dangling=true) # Remove volumes
