#!/bin/bash

export PRIVATE_KEY=$(cat $ENV_DIR/PRIVATE_KEY)
python3 test/decrypt.py
