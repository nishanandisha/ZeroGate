#!/bin/bash
source "$(dirname "$0")/../../lib.sh"
token dave | grep -q access_token
