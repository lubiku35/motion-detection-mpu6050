"""
SensorReader Module for Raspberry Pi Pico W

This module interfaces with the MPU6050 sensor over I2C to read accelerometer
and gyroscope data. It performs enriched behavior analysis to classify motion
states like stable, tilting, shaking, and walking. The logic includes dynamic
thresholds and tilt/orientation classification.
"""

from machine import I2C, Pin
from mpu6050 import MPU6050
import time
import ujson

class SensorReader:
    """
    SensorReader handles initialization and periodic reading of MPU6050 sensor data.
    It processes motion detection, behavior classification, tilt orientation,
    and logs the enriched results to a JSON file.
    """

    def __init__(self, sda=0, scl=1, log_file="logs.json"):
        print(f"[SENSOR] Initializing I2C on SDA=GP{sda}, SCL=GP{scl}...")
        self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda))
        self.sensor = MPU6050(self.i2c)
        self.last_accel = None
        self.last_motion = "Initializing"
        self.log_file = log_file
        self.accel_window = []
        self.max_window_size = 20  # ~2 seconds at 10Hz
        print("[SENSOR] MPU6050 initialized and ready.")

    def read(self):
        """
        Reads a single sensor sample, classifies the behavior, and logs the result.
        Returns enriched JSON data including motion type, tilt, and behavior.
        """
        try:
            accel = self.sensor.read_accel()
            gyro = self.sensor.read_gyro()
            motion = self._detect_motion(accel)
            summary = self._analyze_behavior(accel)

            enriched = {
                "timestamp": time.time(),
                "motion": motion,
                "accel": accel,
                "gyro": gyro,
                "summary": summary
            }

            self._log_to_file(enriched)

            print(f"[READ] Motion: {motion} | Behavior: {summary['behavior']} | "
                  f"Walking: {summary['walking']} | Accel: {accel} | Gyro: {gyro}")
            return enriched

        except Exception as e:
            print("[ERROR] Sensor read failed:", e)
            return {
                "timestamp": time.time(),
                "motion": "Error",
                "accel": {"x": 0, "y": 0, "z": 0},
                "gyro": {"x": 0, "y": 0, "z": 0},
                "summary": {
                    "behavior": "error",
                    "intensity": "unknown",
                    "tilt": "unknown",
                    "walking": False,
                    "variance_z": 0.0
                }
            }

    def _detect_motion(self, accel):
        """Detect axis-based movement using dynamic threshold based on recent variance."""
        if not self.last_accel:
            self.last_accel = accel
            return "Initializing"

        dx = accel['x'] - self.last_accel['x']
        dy = accel['y'] - self.last_accel['y']
        dz = accel['z'] - self.last_accel['z']
        self.last_accel = accel

        var_z = self._variance(self.accel_window)  # <- FIXED LINE

        dynamic_threshold = max(0.2, min(1.0, var_z * 20))

        if abs(dx) > dynamic_threshold: return "X-axis movement"
        if abs(dy) > dynamic_threshold: return "Y-axis movement"
        if abs(dz) > dynamic_threshold: return "Z-axis movement"
        return "Stable"

    def _analyze_behavior(self, accel):
        """
        Enhanced behavior analysis including walking detection.
        Combines Z-axis variance, oscillation pattern, and gyroscope stability.
        """
        abs_x = abs(accel['x'])
        abs_y = abs(accel['y'])
        abs_z = abs(accel['z'])
        total = abs_x + abs_y + abs_z

        # Tilt orientation based on dominant axis
        dominant = max((abs_x, 'x'), (abs_y, 'y'), (abs_z, 'z'))[1]
        tilt = {"x": "side", "y": "upright", "z": "flat"}[dominant]

        # Update window for Z values (used for walking detection)
        self.accel_window.append(accel['z'])
        if len(self.accel_window) > self.max_window_size:
            self.accel_window.pop(0)

        var_z = self._variance(self.accel_window)

        # Compute basic oscillation pattern (zero-crossings per time unit)
        zero_crossings = 0
        for i in range(1, len(self.accel_window)):
            if (self.accel_window[i-1] - 1.0) * (self.accel_window[i] - 1.0) < 0:
                zero_crossings += 1

        # Walking: moderate variance, oscillation, and no chaotic rotation
        walking = False
        if (
            len(self.accel_window) == self.max_window_size and
            0.01 < var_z < 0.12 and
            3 <= zero_crossings <= 12 and
            abs(accel['x']) < 2.5 and
            abs(accel['y']) < 2.5
        ):
            walking = True

        # Classify general behavior
        if walking:
            behavior = "walking"
            intensity = "moderate"
        elif abs_y > 3.5 or total > 4.5:
            behavior = "shaking"
            intensity = "high"
        elif total > 3.0:
            behavior = "moving"
            intensity = "medium"
        elif total > 1.5:
            behavior = "tilting"
            intensity = "low"
        else:
            behavior = "stable"
            intensity = "low"

        return {
            "behavior": behavior,
            "intensity": intensity,
            "tilt": tilt,
            "walking": walking,
            "variance_z": round(var_z, 4)
        }


    def _variance(self, values):
        """Computes variance for a list of numeric values."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _log_to_file(self, data):
        """Appends a new line of JSON data to the log file."""
        try:
            with open(self.log_file, "a") as f:
                f.write(ujson.dumps(data) + "\n")
        except Exception as e:
            print("[LOG ERROR] Could not write to file:", e)
