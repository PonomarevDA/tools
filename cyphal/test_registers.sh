#!/bin/bash
# set -e
MAX=1000
for i in {1..1000}; do
    echo "$i/$MAX"
    res=$(y rl -T 1.0 50, | y rb -T 1.0 | jq)
done
