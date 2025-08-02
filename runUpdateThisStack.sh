#!/bin/bash

# MySQL data directory
mkdir -p mysql/data

# Prefect data directory
mkdir -p prefect/data

# Raw data directories
mkdir -p DATA/INPUT
mkdir -p DATA/GENERATED



# Run the stack
echo "TZ=$(timedatectl show --value --property=Timezone)" > .env
sudo docker-compose down
sudo docker-compose up -d --build
