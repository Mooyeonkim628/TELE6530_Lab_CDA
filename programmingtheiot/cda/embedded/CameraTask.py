import logging
import threading
import time
import os
from datetime import datetime

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.data.SensorData import SensorData

try:
    from picamera2 import Picamera2
    from picamera2.outputs import FfmpegOutput
    from picamera2.encoders import H264Encoder
    import numpy as np
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logging.warning("picamera2 or numpy not available.")

class CameraTask:
    RECORD_DIR      = "/home/trido21c/recordings"
    RECORD_DURATION = 60  # seconds

    def __init__(self, dataMsgListener=None):
        self.dataMsgListener = dataMsgListener
        self.configUtil      = ConfigUtil()
        self.host            = self.configUtil.getProperty(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_HOST_ADDR_KEY, '127.0.0.1')
        self.port            = self.configUtil.getInteger(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_PORT_KEY, 8554)
        self.path            = self.configUtil.getProperty(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_PATH_KEY, 'stream')
        self.width           = self.configUtil.getInteger(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FRAME_WIDTH_KEY, 1440)
        self.height          = self.configUtil.getInteger(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FRAME_HEIGHT_KEY, 1080)
        self.fps             = self.configUtil.getInteger(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FPS_KEY, 30)
        self.minPixelsDiff   = self.configUtil.getInteger(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.MIN_MOTION_PIXELS_DIFF_KEY, 10000)
        self.rtspUrl         = f"rtsp://{self.host}:{self.port}/{self.path}"
        self.picam           = None
        self.encoder         = None
        self.running         = False
        self.motionThread    = None
        self.prevFrame       = None
        self.isRecording     = False
        self.recordLock      = threading.Lock()
        os.makedirs(self.RECORD_DIR, exist_ok=True)
        logging.info("CameraTask initialized. RTSP: %s", self.rtspUrl)

    def start(self) -> bool:
        if not PICAMERA_AVAILABLE:
            logging.warning("picamera2 not available.")
            return False
        if self.running:
            logging.warning("CameraTask already running.")
            return False
        try:
            self.picam  = Picamera2()
            videoConfig = self.picam.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.fps}
            )
            self.picam.configure(videoConfig)
            self.encoder = H264Encoder(bitrate=4000000)
            output       = FfmpegOutput(f"-f rtsp -rtsp_transport tcp {self.rtspUrl}")
            self.picam.start_recording(self.encoder, output)
            self.running      = True
            self.motionThread = threading.Thread(target=self._detectMotion, daemon=True)
            self.motionThread.start()
            logging.info("CameraTask started.")
            return True
        except Exception as e:
            logging.warning("Failed to start CameraTask: %s", e)
            return False

    def stop(self) -> bool:
        if not self.running:
            return False
        self.running = False
        try:
            if self.picam:
                self.picam.stop_recording()
                self.picam.close()
                self.picam = None
            logging.info("CameraTask stopped.")
            return True
        except Exception as e:
            logging.warning("Failed to stop CameraTask: %s", e)
            return False

    def _startRecording(self):
        with self.recordLock:
            if self.isRecording:
                return
            self.isRecording = True

        def record():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath  = os.path.join(self.RECORD_DIR, f"motion_{timestamp}.mp4")
            try:
                logging.info("Recording started: %s", filepath)
                recEncoder = H264Encoder(bitrate=2000000)
                recOutput  = FfmpegOutput(filepath)
                self.picam.start_encoder(recEncoder, recOutput)
                time.sleep(self.RECORD_DURATION)
                self.picam.stop_encoder(recEncoder)
                logging.info("Recording saved: %s", filepath)
            except Exception as e:
                logging.warning("Recording error: %s", e)
            finally:
                with self.recordLock:
                    self.isRecording = False

        threading.Thread(target=record, daemon=True).start()

    def _detectMotion(self):
        while self.running:
            try:
                frame = self.picam.capture_array()
                if self.prevFrame is not None:
                    diff       = np.abs(frame.astype(int) - self.prevFrame.astype(int))
                    diffPixels = np.sum(diff > 30)
                    if diffPixels > self.minPixelsDiff:
                        logging.info("Motion detected! diffPixels=%d", diffPixels)
                        self._notifyMotion(diffPixels)
                        self._startRecording()
                        time.sleep(2)
                self.prevFrame = frame
                time.sleep(0.1)
            except Exception as e:
                logging.warning("Motion detection error: %s", e)
                time.sleep(1)

    def _notifyMotion(self, diffPixels: int):
        if self.dataMsgListener:
            sensorData = SensorData(name=ConfigConst.MOTION_SENSOR_NAME, typeID=ConfigConst.MOTION_SENSOR_TYPE)
            sensorData.setValue(1.0)
            self.dataMsgListener.handleSensorMessage(sensorData)

    def isRunning(self) -> bool:
        return self.running