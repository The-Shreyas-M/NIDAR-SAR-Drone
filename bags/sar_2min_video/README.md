# bags/sar_2min_video

Recorded on the Pi 2026-10-22 with `ros/record_video_bag.sh 120`.

- **Topic:** `/imx500/image_raw/compressed`
  (`sensor_msgs/msg/CompressedImage`, `format: jpeg`)
- **Duration:** 119.25 s, **2382 messages** (19.97 fps), 640x480
- **Storage:** MCAP, 74 MB
- `video.mp4` — decoded from the bag with `ros/bag_to_video.py` (38 MB)
- `sample_frame_60s.jpg` — single raw frame pulled straight out of the bag

These are real camera pixels. Reproduce them yourself:

```bash
# 1. replay the bag live (requires ROS 2 + any image viewer node)
ros2 bag play bags/sar_2min_video --loop

# 2. bag -> mp4 (deterministic, frame-for-frame)
python3 ros/bag_to_video.py bags/sar_2min_video out.mp4

# 3. pull a single frame's JPEG bytes (no decoding needed - already JPEG)
python3 - <<'PY'
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
r = rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri='bags/sar_2min_video', storage_id='mcap'),
       rosbag2_py.ConverterOptions(input_serialization_format='cdr',
                                  output_serialization_format='cdr'))
t, data, stamp = r.read_next()
msg = deserialize_message(data, get_message('sensor_msgs/msg/CompressedImage'))
open('frame0.jpg', 'wb').write(bytes(msg.data))
PY
```
