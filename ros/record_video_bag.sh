#!/bin/bash
# record_video_bag.sh - record camera FRAMES (not just detections) into a bag.
#
# Usage: ./record_video_bag.sh [DURATION] [OUTPUT_DIR] [WIDTH] [HEIGHT] [FPS]
#   default: 120s -> /home/user/rosbags/video_<ts>, 640x480 @ 20fps
#
# Produces a bag with /imx500/image_raw/compressed (sensor_msgs/CompressedImage,
# JPEG). Convert back with ros/bag_to_video.py.
#
# NOTE: no `set -u` - ROS setup.bash reads unset vars and aborts under nounset.
set -o pipefail

DURATION="${1:-120}"
OUT="${2:-/home/user/rosbags/video_$(date +%Y%m%d_%H%M%S)}"
WIDTH="${3:-640}"
HEIGHT="${4:-480}"
FPS="${5:-20}"
TOPIC=/imx500/image_raw/compressed
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/imx500_video_publisher.py"

source /opt/ros/lyrical/setup.bash

cleanup() {
  [ -n "${PUB_PID:-}" ] && kill -INT "$PUB_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

# The camera is exclusive - make sure the detector is not holding it.
if pgrep -f imx500_detector >/dev/null 2>&1; then
  echo "==> stopping running imx500_detector (camera is exclusive)"
  pkill -f imx500_detector
  sleep 2
fi

mkdir -p "$(dirname "$OUT")"

echo "==> starting frame publisher (${WIDTH}x${HEIGHT}@${FPS})"
nohup python3 "$PY" --width "$WIDTH" --height "$HEIGHT" --fps "$FPS" \
  --topic "$TOPIC" > /tmp/imx500_video_publisher.log 2>&1 &
PUB_PID=$!

echo "==> waiting for $TOPIC ..."
for i in $(seq 1 40); do
  if ros2 topic list 2>/dev/null | grep -qx "$TOPIC"; then
    break
  fi
  if ! kill -0 "$PUB_PID" 2>/dev/null; then
    echo "!! publisher died:" >&2
    tail -20 /tmp/imx500_video_publisher.log >&2
    exit 1
  fi
  sleep 1
done
if ! ros2 topic list 2>/dev/null | grep -qx "$TOPIC"; then
  echo "!! $TOPIC never appeared" >&2
  tail -20 /tmp/imx500_video_publisher.log >&2
  exit 1
fi

echo "==> topic up, warming up 3s"
sleep 3

echo "==> recording ${DURATION}s -> $OUT"
# This ROS 2 (Lyrical) rejects positional topic args; use --topics.
timeout -s INT "$DURATION" ros2 bag record -o "$OUT" --topics "$TOPIC"
echo "==> recording stopped"

cleanup
trap - EXIT
echo "==> bag info"
ros2 bag info "$OUT" 2>&1 | head -30
echo "==> publisher log tail"
tail -3 /tmp/imx500_video_publisher.log
