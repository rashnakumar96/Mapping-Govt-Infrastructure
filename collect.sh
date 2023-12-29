#!/bin/bash

if [ -z "$1" ]; then
    echo "usage: ./collect.sh [ccTLD]"
    exit 1
fi

zip -j "$1.zip" \
results/resources/hostnametoResourcesMap_$1.json \
results/resources/resources_0_$1.json \
results/resources/resources_1_$1.json \
results/resources/resources_2_$1.json \
results/resources/resources_3_$1.json \
results/resources/resources_4_$1.json \
results/resources/resources_5_$1.json \
results/resources/resources_6_$1.json \
results/resources/resources_6_$1.json \
results/urlSizeMap/urlSizeMap_$1.json
