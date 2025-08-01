#!/bin/bash

# MySQL data directory
mkdir -p mysql/data

# Raw data directories
mkdir -p DATA/INPUT
mkdir -p DATA/GENERATED



# Run the stack
sudo docker-compose down
sudo docker-compose up -d --build
