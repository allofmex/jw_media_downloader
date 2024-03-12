#!/bin/bash
SCRIPT_DIR=dirname "$0"
source ~/jw_media_tool_venv/bin/activate
python $SCRIPT_DIR/src/start.py "$@"
