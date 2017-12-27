#!/bin/bash

if [ "$#" -ne 1 ]
then
  echo "please provide a browser name to start the script [chrome,firefox,opera]"
  exit 1
fi

browser=$1

cd /selenium
git pull

python /selenium/start_node.py --config  /selenium/config_node_${browser}.json