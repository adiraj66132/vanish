#!/usr/bin/env bash
# Start without direct virtual camera output; capture the Webcam Preview
# window from OBS (Window Capture) instead.
exec "$(dirname "$0")/run_local.sh" --no-virtual-camera "$@"
