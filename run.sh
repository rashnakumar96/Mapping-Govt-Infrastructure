#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "usage: ./run.sh [ccTLD] [country_name] [nordvpn_name]"
    exit 1
fi


yaml="docker-compose-$1.yaml"
touch "$yaml"

token="e9f2abb9fd8de1adc4b8cbfad69c51ca31ab1728c6560a66c193aa8aacdb340b"

echo "version: '3'
services:
  vpn_$1:
    image: ghcr.io/bubuntux/nordvpn
    cap_add:
      - NET_ADMIN               # Required
      - NET_RAW                 # Required
    environment:                # Review https://github.com/bubuntux/nordvpn#environment-variables
      - TOKEN=$token     # Required
      - CONNECT=$3
      - TECHNOLOGY=NordLynx
      - NETWORK=192.168.1.0/24  # So it can be accessed within the local network
    ports:
      - :8888
    sysctls:
      - net.ipv6.conf.all.disable_ipv6=1  # Recomended if using ipv4 only
  downloader_$1:
    container_name: downloader_$1
    image: downloader:latest
    entrypoint: python3 /scripts/collectResourcestoDepthN.py $1 $2
    volumes:
    - ./results:/results
    - ./data:/data
    network_mode: service:vpn_$1
    environment:
    - PYTHONUNBUFFERED=1
    depends_on:
      - vpn_$1" > "$yaml"

docker compose -f $yaml up -d --build
docker compose -f $yaml logs -f