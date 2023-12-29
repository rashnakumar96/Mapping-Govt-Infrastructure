#!/bin/bash

if [ -z "$1" ]; then
    echo "usage: ./stop.sh [ccTLD]"
    exit 1
fi

docker compose -f docker-compose-$1.yaml stop -t 10
docker compose -f docker-compose-$1.yaml down
rm docker-compose-$1.yaml