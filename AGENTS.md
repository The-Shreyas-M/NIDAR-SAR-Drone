# AGENTS.md — NIDAR-SAR-Drone

> Repo state (2026-10-15): no app code yet, not a git repo. `pi/` mirrors
> the live Pi scripts/services — edit there, redeploy via `pi/INSTALL.md`.

## What this is
- Edge-powered SAR drone. Compute: Raspberry Pi 5 running Ubuntu Server 26.04
  (`rpi`, kernel `7.0.0-1020-raspi`, aarch64).
- ROS 2 + custom Pi AI Camera drivers, compiled and installed manually on the
  Pi (not in this repo). Never assume a rebuild from source here works.
- Dev machine is Windows; Pi is a remote target over SSH (`user@rpi`).
  Windows has no `python3`/`sshpass` — use `python` + `paramiko` (installed)
  for non-interactive SSH from scripts.

## Pi networking (verified live 2026-10-14, reboot-tested)
- Stack: NetworkManager active; systemd-networkd inactive; Netplan renderer
  is NetworkManager. STA profiles are netplan-managed (`/etc/netplan/`):
  `netplan-wlan0-Nord 5` (autoconnect-priority 100),
  `netplan-wlan0-Not_For_You__2G` (priority 50). `wlan0` powersave disabled.
- AP profile `NIDAR-AP` (native NM, survives `netplan apply`): SSID
  `NIDAR-AP`, WPA-PSK `nidar1234`, band bg/ch 6, `ipv4.method shared`,
  `192.168.50.1/24`, `autoconnect no`, priority -100. Change PSK with:
  `sudo nmcli con modify NIDAR-AP wifi-sec.psk '<new>'`
- Boot fallback: `/usr/local/bin/nidar-wifi-fallback` +
  `nidar-wifi-fallback.service` (enabled, `STA_GRACE=5` `STA_SETTLE=15`).
  Waits only for NM to settle, then brings up `NIDAR-AP` iff `wlan0` has no
  STA connection (~7s after service start, measured). No fixed 40s window.
- Runtime guard: `/usr/local/bin/nidar-wifi-watch` +
  `nidar-wifi-watch.service` (enabled, 5s ticks). STA down → AP up at next
  tick; AP up → scans every ~15s and flips to highest-priority visible saved
  STA network. Plus NM dispatcher `/etc/NetworkManager/dispatcher.d/90-nidar-ap`:
  STA `down` event → AP up in ~4s (3s flap-grace + activation, foreground
  `nmcli -w 20` — must NOT be backgrounded, SIGHUP kills it).
- Manual override: `nidar-ap on|off` writes `/run/nidar-ap-hold` (tmpfs, gone
  on reboot, 15min expiry) which pauses watcher+dispatcher; `nidar-ap auto`
  clears it. `off` also triggers an STA rescan.
- Manual toggle: `sudo nidar-ap on|off|status|toggle|auto`
  (`/usr/local/bin/nidar-ap`).
- `user` has sudo only with password; NMcli changes need `sudo`.
- Single radio: AP up blocks STA. To join a new network: `nidar-ap off`,
  then connect normally. To save a new network persistently, add it via
  netplan (`/etc/netplan/50-cloud-init.yaml` + `sudo netplan apply`).

## Wi-Fi setup portal (verified live 2026-10-14, reboot-tested)
- Join `NIDAR-AP`, open `http://192.168.50.1/` (kept `.50.1`, not `192.168.1.1`:
  already live and `192.168.1.x` collides with common home-router subnets).
- Backend `/usr/local/bin/nidar-portal` (Python stdlib only, port 80) +
  `nidar-portal.service` (enabled). API: `GET /api/status|/api/scan|/api/saved`,
  `POST /api/connect {ssid,password}`, `POST /api/forget {uuid}`.
- `connect` creates an NM profile (autoconnect, survives reboot) and the AP
  drops as `wlan0` switches to STA — the page warns before firing. On failure
  the portal re-ups `NIDAR-AP` so the operator is never stranded.
- Portal clears `/run/nidar-ap-hold` on connect success (resume auto mode),
  sets it on failure (pins AP so the watcher doesn't flap at a bad password).
- Scanning works while the AP is up on this hardware (no AP-down dance needed);
  own `NIDAR-AP` beacon is filtered from results. No DNS-hijack/captive auto-
  popup — user navigates to the fixed URL manually.

## ROS 2 on the Pi (verified live 2026-10-22)
- Distro: **ROS 2 Lyrical**, `/opt/ros/lyrical` (Python 3.14). Nothing is
  sourced by default — always `source /opt/ros/lyrical/setup.bash` first.
- Camera workspace: `/home/user/imx500_ros_ws`, package `imx500_detector`.
- **`ros2 run imx500_detector ...` does NOT work**: the colcon install has a
  broken ament index (egg-link points into `build/`), so the package is
  invisible to `ros2 pkg`. Run the node directly instead:
  `PYTHONPATH=$WS/install/imx500_detector/lib/python3.14/site-packages:$PYTHONPATH
  python3 -m imx500_detector.detector_node`
- **`ros2 bag record` needs `--topics`** — positional topic args are rejected
  (`unrecognized arguments: /topic`). Use
  `ros2 bag record -o OUT --topics /imx500/detections`.
- **Never `set -u`** in scripts that source ROS `setup.bash` — it reads unset
  vars (`AMENT_TRACE_SETUP_FILES`) and the script dies immediately.
- The detector publishes **only** `/imx500/detections`
  (`vision_msgs/msg/Detection2DArray`) at ~4 Hz. There is **no image topic**,
  so a bag contains detection metadata, not video frames.
- IMX500 firmware upload takes ~5–20s: wait for the topic to appear before
  recording, don't sleep a fixed amount.
- Camera is exclusive: `imx500_detector` and `rpicam-vid` cannot run at the
  same time. Annotation video is a separate `rpicam-vid --post-process-file`
  run, not something the bag captures.
- Scripts: `ros/record_bag.sh [seconds] [outdir]` (start node → wait for topic
  → record → `ros2 bag info`), `ros/bag_to_csv.py` for CSV export.
  Bags land in `bags/` in the repo.

### Camera frames (video) in a bag
- The detector has no image publisher, so frames need
  `ros/imx500_video_publisher.py` → `sensor_msgs/msg/CompressedImage` (JPEG) on
  `/imx500/image_raw/compressed`. Drive it with `ros/record_video_bag.sh
  [secs] [outdir] [w] [h] [fps]`; convert back with `ros/bag_to_video.py`.
- **picamera2 "RGB888" is already BGR here** — do NOT swap channels before
  `cv2.imencode`, or everything turns blue (verified the hard way).
- 640x480 @ 20fps → ~74 MB per 2 min. Bump resolution/fps only deliberately.
- Sample: `bags/sar_2min_video/` (bag + mp4 + one raw frame).

## ROS 2 workspace on the Pi (verified build 2026-11-04)
- Workspace: `~/nidar_ws` (src in repo at `ros/src/`). Build: `cd ~/nidar_ws && source /opt/ros/lyrical/setup.bash && colcon build --symlink-install`.
- 9 packages: nidar_msgs, nidar_bringup, nidar_camera, nidar_lidar, nidar_flight, nidar_gcs, nidar_navigation, nidar_perception, nidar_slam.
- Launch: `ros2 launch nidar_bringup onboard.launch.py fcu_url:=/dev/ttyAMA0:921600` (MAVROS apm, RPLidar C1, IMX500, EKF, SLAM, ArUco, mission manager).
- MAVROS uses `apm.launch` (ArduPilot). FC via UART on `/dev/ttyAMA0` (override with fcu_url arg).
- LiDAR package: `lgdx_rplidar_c1`, executable `rplidar_c1_node`.
- Custom messages in `nidar_msgs`: PersonDetection, PersonDetectionArray, MissionCommand, LaunchpadPose.
- Entry points: imx500_detector, imx500_video_publisher, aruco_detector, person_fusion, offboard_control, mission_manager, gcs_node.
- Node stubs only - real logic TBD per phase. SLAM config in nidar_slam/config/slam_toolbox.yaml.
- FC permission: user in dialout group (needed for UART). LiDAR not yet connected (/dev/ttyUSB0 absent).

## Rules for future sessions
- Pi is the executable source of truth. Before writing Netplan /
  NetworkManager / `hostapd` / `dnsmasq` config, SSH in and check what the Pi
  actually uses (`nmcli general status`, `netplan status`, `systemctl status
  NetworkManager systemd-networkd`). Docs lose to device state.
- Do not commit the SSH password or STA Wi-Fi PSKs (they live in
  `/etc/netplan`, root-only). The field AP PSK above is the documented
  exception — operators need it to connect.
- Keep Pi scripts idempotent and reboot-safe; verify with
  `sudo reboot` + reconnect test, not just "service started".
- Repo mirrors the Pi scripts under `pi/` (`bin/`, `systemd/`,
  `networkmanager/`, `INSTALL.md`). `pi/` is source of truth: edit there,
  redeploy via `pi/INSTALL.md`, never hand-edit Pi copies.
- Prefer `nmcli` (if NetworkManager is active) over hand-rolled
  `hostapd`+`dnsmasq` unless the device proves otherwise — fewer moving parts.
- Repo has no build/test/lint yet. When adding the first script, add its exact
  run/verify command next to it in this file.
