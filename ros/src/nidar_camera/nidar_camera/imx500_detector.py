#!/usr/bin/env python3

import time

import numpy as np
import rclpy
from rclpy.node import Node

from vision_msgs.msg import Detection2D
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import ObjectHypothesisWithPose

from picamera2 import Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics


MODEL_PATH = "/usr/share/imx500-models/imx500_network_yolo11n_pp.rpk"

COCO_LABELS = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


class IMX500Detector(Node):

    def __init__(self):
        super().__init__("imx500_detector")

        self.declare_parameter(
            "model",
            MODEL_PATH
        )

        self.declare_parameter(
            "threshold",
            0.50
        )

        self.declare_parameter(
            "max_detections",
            10
        )

        model = self.get_parameter(
            "model"
        ).value

        self.threshold = float(
            self.get_parameter("threshold").value
        )

        self.max_detections = int(
            self.get_parameter("max_detections").value
        )

        self.get_logger().info(
            "========================================"
        )
        self.get_logger().info(
            "IMX500 YOLO11n ROS 2 detector"
        )
        self.get_logger().info(
            "========================================"
        )

        self.get_logger().info(
            f"Model: {model}"
        )

        self.get_logger().info(
            f"Detection threshold: {self.threshold:.2f}"
        )

        # ---------------------------------------------------------
        # IMPORTANT:
        #
        # IMX500 MUST be created before Picamera2.
        #
        # This loads/configures the network on the IMX500.
        # ---------------------------------------------------------

        self.imx500 = IMX500(model)

        self.intrinsics = self.imx500.network_intrinsics

        if self.intrinsics is None:
            self.intrinsics = NetworkIntrinsics()
            self.intrinsics.task = "object detection"

        if self.intrinsics.task != "object detection":
            raise RuntimeError(
                f"Model task is "
                f"'{self.intrinsics.task}', "
                f"not object detection"
            )

        # ---------------------------------------------------------
        # These match the official Raspberry Pi YOLO11n model-zoo
        # invocation:
        #
        # --bbox-normalization
        # --bbox-order xy
        # ---------------------------------------------------------

        self.intrinsics.bbox_normalization = True
        self.intrinsics.bbox_order = "xy"

        # ---------------------------------------------------------
        # Now create Picamera2.
        # ---------------------------------------------------------

        self.picam2 = Picamera2(
            self.imx500.camera_num
        )

        inference_rate = self.intrinsics.inference_rate

        self.get_logger().info(
            f"IMX500 inference rate: "
            f"{inference_rate} FPS"
        )

        config = self.picam2.create_preview_configuration(
            main={
		"size": (640, 480),
		"format": "RGB888"
	    },
            buffer_count=4
        )

        self.picam2.configure(config)

        self.get_logger().info(
            "Starting IMX500 network firmware..."
        )

        #self.imx500.show_network_fw_progress_bar()

        self.picam2.start()

        time.sleep(1.0)

        # ---------------------------------------------------------
        # ROS publisher
        # ---------------------------------------------------------

        self.publisher = self.create_publisher(
            Detection2DArray,
            "/imx500/detections",
            10
        )

        self.frame_count = 0
        self.detection_count = 0

        self.get_logger().info(
            "Camera started."
        )

        self.get_logger().info(
            "YOLO11n inference is running ON THE IMX500."
        )

        self.get_logger().info(
            "Publishing: /imx500/detections"
        )

    def process_frame(self):

        # ---------------------------------------------------------
        # Capture metadata.
        #
        # The actual neural-network output is embedded in this
        # metadata by the IMX500.
        # ---------------------------------------------------------

        metadata = self.picam2.capture_metadata()

        outputs = self.imx500.get_outputs(
            metadata,
            add_batch=True
        )

        if outputs is None:
            return

        self.frame_count += 1

        # ---------------------------------------------------------
        # YOLO11n PP output format:
        #
        # outputs[0] = boxes
        # outputs[1] = scores
        # outputs[2] = classes
        #
        # The PP network has already performed the post-processing
        # on the IMX500.
        # ---------------------------------------------------------

        boxes = outputs[0][0]
        scores = outputs[1][0]
        classes = outputs[2][0]

        input_w, input_h = self.imx500.get_input_size()

        # ---------------------------------------------------------
        # Official Picamera2 IMX500 processing:
        #
        # YOLO11n model-zoo uses bbox normalization.
        #
        # The tensor coordinates are divided by the inference
        # input height (640 for this model).
        # ---------------------------------------------------------

        if self.intrinsics.bbox_normalization:
            boxes = boxes / input_h

        # ---------------------------------------------------------
        # Official YOLO11n model-zoo setting is bbox-order=xy.
        #
        # The 	raw representation is transformed from:
        #
        #   y0, x0, y1, x1
        #
        # to:
        #
        #   x0, y0, x1, y1
        # ---------------------------------------------------------

        if self.intrinsics.bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]

        msg = Detection2DArray()

        msg.header.stamp = self.get_clock().now().to_msg()

        frame_detections = 0

        # ---------------------------------------------------------
        # Process detections
        # ---------------------------------------------------------

        for box, score, category in zip(
            boxes,
            scores,
            classes
        ):

            score = float(score)
            category = int(category)

            if score < self.threshold:
                continue

            if frame_detections >= self.max_detections:
                break

            # Normalized:
            #
            # x0, y0, x1, y1
            #
            x0 = float(box[0])
            y0 = float(box[1])
            x1 = float(box[2])
            y1 = float(box[3])

            width = x1 - x0
            height = y1 - y0

            # -----------------------------------------------------
            # Raspberry Pi's official IMX500 coordinate conversion.
            #
            # This handles:
            #
            # sensor crop
            # scaling
            # ISP output
            # translation
            #
            # and is much safer than manually scaling coordinates.
            # -----------------------------------------------------

            converted = self.imx500.convert_inference_coords(
                [
                    x0,
                    y0,
                    width,
                    height
                ],
                metadata,
                self.picam2
            )

            x, y, w, h = [int(v) for v in converted]

            # -----------------------------------------------------
            # ROS Detection2D
            # -----------------------------------------------------

            detection = Detection2D()

            detection.bbox.center.position.x = x + w / 2.0
            detection.bbox.center.position.y = y + h / 2.0
            detection.bbox.center.theta = 0.0

            detection.bbox.center.theta = 0.0

            detection.bbox.size_x = float(w)
            detection.bbox.size_y = float(h)

            hypothesis = ObjectHypothesisWithPose()

            hypothesis.hypothesis.class_id = str(category)
            hypothesis.hypothesis.score = score

            detection.results.append(
                hypothesis
            )

            msg.detections.append(
                detection
            )

            # -----------------------------------------------------
            # Human-readable ROS log
            # -----------------------------------------------------

            if (
                0 <= category < len(COCO_LABELS)
            ):
                label = COCO_LABELS[category]
            else:
                label = f"class_{category}"

            self.get_logger().info(
                f"[DETECTION] "
                f"{label} | "
                f"confidence={score:.3f} | "
                f"bbox=("
                f"x={x}, "
                f"y={y}, "
                f"w={w}, "
                f"h={h}"
                f")"
            )

            frame_detections += 1
            self.detection_count += 1

        # ---------------------------------------------------------
        # Publish
        # ---------------------------------------------------------

        self.publisher.publish(msg)

    def shutdown(self):

        self.get_logger().info(
            "Stopping camera..."
        )

        try:
            self.picam2.stop()
        except Exception:
            pass


def main(args=None):

    rclpy.init(args=args)

    node = None

    try:

        node = IMX500Detector()

        while rclpy.ok():

            node.process_frame()

            # Process ROS callbacks.
            rclpy.spin_once(
                node,
                timeout_sec=0.0
            )

    except KeyboardInterrupt:
        pass

    finally:

        if node is not None:
            node.shutdown()
            node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":
    main()
