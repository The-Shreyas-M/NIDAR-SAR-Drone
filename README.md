# NIDAR-SAR-Drone

Edge-powered search-and-rescue drone. Compute: **Raspberry Pi 5** running
Ubuntu Server 26.04 (`rpi`) with ROS 2 and custom Pi AI Camera drivers
(compiled manually on the Pi — not in this repo).

## Field Wi-Fi: hotspot + setup portal

The Pi manages its own Wi-Fi. You never need a monitor or keyboard.

| Situation | What happens |
|---|---|
| Boot, no known network around | `NIDAR-AP` hotspot comes up within seconds |
| Boot, known network in range | Joins it as a client (hotspot stays down) |
| Connected Wi-Fi drops mid-run | Hotspot comes back in ~4–9s |
| Hotspot up, known network appears | Flips back to it automatically (~15s) |

**Connect to the drone:** join SSID **`NIDAR-AP`** (password `nidar1234`),
then open **`http://192.168.50.1/`** — a setup page where you can scan for
Wi-Fi networks, join one with its password, and see/forget saved networks.
Joining a network switches the Pi to it (the hotspot drops — the page warns
you first). If the password is wrong, the hotspot is restored automatically.

## On-Pi commands (SSH as `user@rpi`)

```bash
sudo nidar-ap on        # force hotspot up (pins it, pauses auto-switching)
sudo nidar-ap off       # hotspot down + rescan for known networks
sudo nidar-ap status    # show branch: active conns, wlan0 state, AP + mode
sudo nidar-ap toggle    # flip current hotspot state
sudo nidar-ap auto      # resume automatic STA <-> AP switching
```

The manual pin expires after 15 min (and clears on reboot); `auto` clears it
immediately. Saved STA networks live in `/etc/netplan/50-cloud-init.yaml`
(`sudo netplan apply` after edits).

## How it's built (all live on the Pi, reboot-tested)

- **Hotspot profile** `NIDAR-AP` (native NetworkManager, `autoconnect no`):
  band bg/ch 6, `ipv4.method shared`, `192.168.50.1/24` (DHCP+DNS via NM's
  dnsmasq). STA profiles stay netplan-managed — the two don't clobber each other.
- **Boot fallback** — `/usr/local/bin/nidar-wifi-fallback` +
  `nidar-wifi-fallback.service`: waits only for NetworkManager to settle
  (`STA_GRACE=5`, `STA_SETTLE=15`), then raises the AP iff `wlan0` has no STA
  connection (~7s after service start, measured).
- **Runtime watcher** — `/usr/local/bin/nidar-wifi-watch` (stdlib Python) +
  `nidar-wifi-watch.service`: 5s ticks; STA down → AP up next tick; AP up →
  scans every ~15s and switches to the highest-priority visible saved network.
- **Disconnect dispatcher** — `/etc/NetworkManager/dispatcher.d/90-nidar-ap`:
  STA `down` event → AP up in ~4s (3s flap-grace + foreground `nmcli -w 20`;
  must stay foreground — backgrounded children get SIGHUP-killed).
- **Setup portal** — `/usr/local/bin/nidar-portal` (stdlib Python, port 80) +
  `nidar-portal.service`: single self-contained page (no CDN — the AP has no
  internet). API: `GET /api/status|/api/scan|/api/saved`,
  `POST /api/connect {ssid,password}`, `POST /api/forget {uuid}`.
  Scanning works while the AP is up on this radio; the portal filters its own
  beacon. No captive-portal DNS hijack — navigate to the fixed URL manually.

## Recording camera data (ROS 2)

The Pi runs **ROS 2 Lyrical** (`/opt/ros/lyrical`) with an IMX500 AI camera.

```bash
# 120s of camera FRAMES -> bag (640x480 @ 20fps, JPEG)
./ros/record_video_bag.sh 120 /home/user/rosbags/video_$(date +%s)

# 120s of DETECTIONS only -> bag (bounding boxes, no pixels)
./ros/record_bag.sh 120 /home/user/rosbags/detections
```

| Script | Purpose |
|---|---|
| `ros/imx500_video_publisher.py` | Publishes frames on `/imx500/image_raw/compressed` |
| `ros/record_video_bag.sh` | Starts publisher, waits for topic, records frames |
| `ros/bag_to_video.py` | Bag -> `.mp4` (deterministic) |
| `ros/record_bag.sh` | Records `/imx500/detections` (boxes only) |
| `ros/bag_to_csv.py` | Bag -> CSV of detections |

**Reproducing frames** (teammates, any machine with ROS 2):

```bash
ros2 bag play bags/sar_2min_video                 # replay live
python3 ros/bag_to_video.py bags/sar_2min_video out.mp4   # bag -> mp4
ros2 bag info bags/sar_2min_video                 # verify topic/counts
```

Sample data in the repo: `bags/sar_2min_video/` (single frame + README) and
`bags/sar_2min/` (detections CSV + README). The large `.mcap`/`.mp4` files are
git-ignored — regenerate them with the scripts above.

**Pi gotchas that cost real time:**
- The camera is **exclusive** — `imx500_detector` and the frame publisher (or
  `rpicam-vid`) cannot run together. Stop one first.
- `ros2 run imx500_detector ...` **fails** (broken ament index). Use
  `python3 -m imx500_detector.detector_node` with the workspace `PYTHONPATH`.
- `ros2 bag record` on this version **rejects positional topic args** — use
  `--topics /imx500/...`.
- **Never `set -u`** in scripts that source ROS `setup.bash`.
- picamera2 `RGB888` is already BGR-ordered here — swapping channels turns
  faces blue.
- IMX500 firmware upload takes 5–20s; wait for the topic, don't `sleep` blindly.

## Repo state

No app code yet — this repo currently holds docs only (`README.md`,
`AGENTS.md` has the agent-facing verified details). Pi is the source of
truth for all of the above; dev machine is Windows (use `python` +
`paramiko` for non-interactive SSH — no `sshpass`).
