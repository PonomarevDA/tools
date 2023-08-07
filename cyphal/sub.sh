#!/bin/bash
print_help () {
  echo "Usage: sub.sh <node_id> <subject>"
  if [ ! -z "$NODE_ID" ]; then
    $SCRIPT_DIR/get_subjects.sh $NODE_ID
  fi
  exit
}

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
NODE_ID=$1
SUBJECT=$2

if [ -z "$SUBJECT" ]; then
    print_help
fi

PORT_ID=$(y r $NODE_ID uavcan.pub.$SUBJECT.id)
DATA_TYPE=$(y r $NODE_ID uavcan.pub.$SUBJECT.type | tr -d '"')

echo "y sub $PORT_ID:$DATA_TYPE"
y sub $PORT_ID:$DATA_TYPE
