import logging
import threading
import time

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
    logging.warning("picamera2 or numpy not available. Run: sudo apt install -y python3-picamera2")

class CameraTask:
    """
    단일 카메라 인스턴스로 RTSP 스트리밍 + 모션 감지를 동시에 처리
    """

    def __init__(self, dataMsgListener=None):
        self.dataMsgListener = dataMsgListener
        self.configUtil      = ConfigUtil()

        # 스트리밍 config
        self.host            = self.configUtil.getProperty(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_HOST_ADDR_KEY,        '127.0.0.1')
        self.port            = self.configUtil.getInteger(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_PORT_KEY,             8554)
        self.path            = self.configUtil.getProperty(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_PATH_KEY,             'stream')
        self.width           = self.configUtil.getInteger(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FRAME_WIDTH_KEY,      1440)
        self.height          = self.configUtil.getInteger(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FRAME_HEIGHT_KEY,     1080)
        self.fps             = self.configUtil.getInteger(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.STREAM_FPS_KEY,              30)

        # 모션 감지 config
        self.minPixelsDiff   = self.configUtil.getInteger(
            ConfigConst.CONSTRAINED_DEVICE, ConfigConst.MIN_MOTION_PIXELS_DIFF_KEY,  10000)

        self.rtspUrl         = f"rtsp://{self.host}:{self.port}/{self.path}"

        self.picam           = None
        self.encoder         = None
        self.running         = False
        self.motionThread    = None
        self.prevFrame       = None

        logging.info("CameraTask initialized. RTSP: %s", self.rtspUrl)

    def start(self) -> bool:
        if not PICAMERA_AVAILABLE:
            logging.warning("picamera2 not available.")
            return False

        if self.running:
            logging.warning("CameraTask already running.")
            return False

        try:
            self.picam   = Picamera2()

            # 비디오 설정 (스트리밍용)
            videoConfig  = self.picam.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.fps}
            )
            self.picam.configure(videoConfig)

            # RTSP 스트리밍 시작
            self.encoder = H264Encoder(bitrate=4000000)
            output       = FfmpegOutput(f"-f rtsp -rtsp_transport tcp {self.rtspUrl}")
            self.picam.start_recording(self.encoder, output)

            self.running     = True

            # 모션 감지 스레드 시작 (같은 카메라 인스턴스 공유)
            self.motionThread = threading.Thread(target=self._detectMotion, daemon=True)
            self.motionThread.start()

            logging.info("CameraTask started. Streaming + motion detection active.")
            return True

        except Exception as e:
            logging.warning("Failed to start CameraTask: %s", e)
            return False

    def stop(self) -> bool:
        if not self.running:
            logging.warning("CameraTask not running.")
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

    def _detectMotion(self):
        while self.running:
            try:
                # 스트리밍 중인 카메라에서 프레임 캡처
                frame = self.picam.capture_array()

                if self.prevFrame is not None:
                    diff       = np.abs(frame.astype(int) - self.prevFrame.astype(int))
                    diffPixels = np.sum(diff > 30)

                    if diffPixels > self.minPixelsDiff:
                        logging.info("Motion detected! diffPixels=%d", diffPixels)
                        self._notifyMotion(diffPixels)
                        time.sleep(2)  # 2초 debounce

                self.prevFrame = frame
                time.sleep(0.1)  # 10fps로 체크

            except Exception as e:
                logging.warning("Motion detection error: %s", e)
                time.sleep(1)

    def _notifyMotion(self, diffPixels: int):
        if self.dataMsgListener:
            sensorData = SensorData(
                name   = ConfigConst.MOTION_SENSOR_NAME,
                typeID = ConfigConst.MOTION_SENSOR_TYPE
            )
            sensorData.setValue(float(diffPixels))
            self.dataMsgListener.handleSensorMessage(sensorData)

    def isRunning(self) -> bool:
        return self.running