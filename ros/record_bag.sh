#!/bin/bash
# record_bag.sh - record a ROS 2 bag of IMX500 detections for N seconds.
#
# Usage: ./record_bag.sh [DURATION_SECONDS] [OUTPUT_DIR]
#   defaults: 120s -> /home/user/rosbags/sar_<timestamp>
#
# Why the PYTHONPATH hack: the colcon install of imx500_detector has a broken
# ament index (egg-link points at build/, so `ros2 run imx500_detector ...`
# reports "Package not found"). Running the module directly works, so this
# script starts the node that way. Fix the ament index and `ros2 run` works too.
# NOTE: no `set -u` — ROS setup.bash reads unset vars (AMENT_TRACE_SETUP_FILES)
# and aborts the whole script under nounset.
set -o pipefail
DURATION="${1:-120}"
OUT="${2:-/home/user/rosbags/sar_$(date +%Y%m%d_%H%M%S)}"
WS=/home/user/imx500_ros_ws
LOG=/tmp/imx500_detector.log

source /opt/ros/lyrical/setup.bash
source "$WS/install/setup.bash" 2>/dev/null || true
export PYTHONPATH="$WS/install/imx500_detector/lib/python3.14/site-packages:${PYTHONPATH:-}"

cleanup() {
  [ -n "${DET_PID:-}" ] && kill "$DET_PID" 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

mkdir -p "$(dirname "$OUT")"

echo "==> starting detector (log: $LOG)"
cd "$WS" || exit 1
nohup python3 -m imx500_detector.detector_node > "$LOG" 2>&1 &
DET_PID=$!

# IMX500 firmware upload takes a while; wait for the topic to actually appear.
echo "==> waiting for /imx500/detections ..."
for i in $(seq 1 60); do
  if ros2 topic list 2>/dev/null | grep -qx "/imx500/detections"; then
    break
  fi
  if ! kill -0 "$DET_PID" 2>/dev/null; then
    echo "!! detector died, last log lines:" >&2
    tail -20 "$LOG" >&2
    exit 1
  fi
  sleep 1
done
if ! ros2 topic list 2>/dev/null | grep -qx "/imx500/detections"; then
  echo "!! /imx500/detections never appeared" >&2
  tail -20 "$LOG" >&2
  exit 1
fi
echo "==> topic up, waiting 5s for first frames"
sleep 5

echo "==> recording ${DURATION}s -> $OUT"
# This ROS 2 (Lyrical) rejects positional topic args; topics go via --topics.
timeout -s INT "$DURATION" ros2 bag record -o "$OUT" --topics /imx500/detections
echo "==> recording stopped"

echo "==> bag info"
ros2 bag info "$OUT" 2>&1 | head -40

echo "==> detector log tail"
tail -3 "$LOG"
