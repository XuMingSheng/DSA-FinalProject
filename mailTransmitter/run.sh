#! /usr/bin/env bash

export LC_ALL='en_US.utf8'

./communicate.sh &
python3 mailManager.py
