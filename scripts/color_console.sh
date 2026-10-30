#!/bin/bash

ESC=$'\033'
RESET="${ESC}[0m"
DIM="${ESC}[2m"
BOLD="${ESC}[1m"
GREEN="${ESC}[32m"
YELLOW="${ESC}[33m"
RED="${ESC}[1;31m"
CYAN="${ESC}[36m"
MAGENTA="${ESC}[35m"

sed -u \
  -e "s/\(\[[0-9:]* INFO\]\)/${GREEN}\1${RESET}/g" \
  -e "s/\(\[[0-9:]* WARN.*\]\)/${YELLOW}\1${RESET}/g" \
  -e "s/\(\[[0-9:]* ERROR.*\]\)/${RED}\1${RESET}/g" \
  -e "s/\(joined the game\|left the game\)/${CYAN}${BOLD}\1${RESET}/g" \
  -e "s/\(<[^>]*>\)/${MAGENTA}${BOLD}\1${RESET}/g"
