# bags/sar_2min

Recorded on the Pi 2026-10-22 with `ros/record_bag.sh 120`.

- **Topic:** `/imx500/detections` (`vision_msgs/msg/Detection2DArray`)
- **Duration:** 118.6 s, **493 messages** (~4 Hz)
- **Storage:** MCAP, 57 KB
- `detections.csv` — exported with `ros/bag_to_csv.py`, one row per detection
  (16 rows; most frames had no detection, so the array was empty)

This bag holds **detection metadata only — not video frames**. The
`imx500_detector` node has no image publisher; it only publishes bounding
boxes. Video is recorded separately with `rpicam-vid --post-process-file ...`
(the two cannot run at the same time — the camera is exclusive).

Replay / inspect:

```bash
ros2 bag info bags/sar_2min
ros2 bag play bags/sar_2min --loop
```
