#!/bin/bash
sudo docker stop $(docker ps -a -q) # Parar containers
sudo docker rm $(sudo docker ps -a -q) # Remover containers
sudo docker rmi -f $( sudo docker images -q ) # Remover imagens
