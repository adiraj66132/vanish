#!/usr/bin/env bash
# Require virtual camera output. On Linux, load the v4l2loopback kernel
# module first (e.g. "sudo modprobe v4l2loopback"). macOS has no virtual
# camera backend; use run_obs.sh with OBS Window Capture instead.
exec "$(dirname "$0")/run_local.sh" --virtual-camera "$@"
