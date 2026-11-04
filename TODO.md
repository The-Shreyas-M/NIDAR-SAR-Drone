# NIDAR-SAR-Drone — TODO

## Done
- [x] Pi Wi-Fi: AP (NIDAR-AP) + setup portal (http://192.168.50.1/) + boot fallback + runtime watcher + dispatcher
- [x] Pi scripts mirrored in repo `pi/` with INSTALL.md
- [x] ROS 2 workspace skeleton (9 packages) built on Pi
- [x] Custom messages (PersonDetection, PersonDetectionArray, MissionCommand, LaunchpadPose)
- [x] Onboard launch (MAVROS apm, RPLidar C1, IMX500, EKF, SLAM, ArUco, mission mgr)
- [x] ROS 2 bags recorded (detections + 2-min video) and pushed sample to repo
- [x] GitHub repo created (public): https://github.com/The-Shreyas-M/NIDAR-SAR-Drone

## Phase 2 — Drivers (needs hardware)
- [ ] Connect RPLidar C1 to /dev/ttyUSB0, verify /scan
- [ ] Wire Pixhawk TELEM2 → Pi UART (/dev/ttyAMA0, 921600), verify /mavros/state
- [ ] Implement nidar_lidar wrapper node
- [ ] Verify EKF fuses IMU + odometry → /odom, /tf

## Phase 3 — Perception
- [ ] Implement aruco_detector (launchpad pose → /aruco/launchpad_pose)
- [ ] Implement person_fusion (IMX500 boxes + LiDAR distance → PersonDetectionArray)
- [ ] Test detection accuracy in maze

## Phase 4 — SLAM
- [ ] Run slam_toolbox in maze, tune resolution/max_laser_range
- [ ] Verify /map quality, loop closure
- [ ] Save map for reuse

## Phase 5 — Navigation & landing
- [ ] ArUco-guided takeoff from launchpad
- [ ] Person approach (position drone in front of person)
- [ ] Auto-land on ArUco marker
- [ ] Mission state machine (operator triggers takeoff, auto-land on complete/low battery)
- [ ] Implement offboard_control (velocity setpoints to MAVROS)

## Phase 6 — GCS
- [ ] Set up WSL + ROS 2 Lyrical on GCS laptop (needs admin)
- [ ] Map receiver + visualization (RViz2 or web)
- [ ] Shortest path planner (entry/exit → each person on occupancy grid)
- [ ] Display people on map with distances
- [ ] Mission command UI (takeoff trigger, abort, etc.)

## Phase 7 — Comms hardening
- [ ] DDS discovery over Wi-Fi (Pi as AP)
- [ ] QoS profiles for map/telemetry (reliable vs best-effort)
- [ ] Bandwidth caps (map at 1-2 Hz, not full rate)
- [ ] Reconnect handling

## Open questions
- [ ] ArUco marker size (cm) and ID for launchpad
- [ ] Pixhawk firmware: ArduPilot (confirmed) — which frame type?
- [ ] GCS: web app (rosbridge) or desktop (RViz2)?
- [ ] SLAM: 2D slam_toolbox (confirmed) — async or sync mode?
