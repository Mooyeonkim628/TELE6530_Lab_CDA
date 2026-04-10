import logging
import unittest
from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.embedded.CameraTask import CameraTask
from programmingtheiot.common.DefaultDataMessageListener import DefaultDataMessageListener

class CameraTaskIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            format='%(asctime)s:%(module)s:%(levelname)s:%(message)s',
            level=logging.DEBUG
        )

        cfg = ConfigUtil()
        enableCamera = cfg.getBoolean(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.ENABLE_CAMERA_KEY
        )

        if not enableCamera:
            raise unittest.SkipTest("ENABLE_CAMERA_KEY is False. Set enableCamera=True in PiotConfig.props.")

        try:
            from picamera2 import Picamera2
            import numpy as np
        except ImportError:
            raise unittest.SkipTest("picamera2 or numpy not available. Run: sudo apt install -y python3-picamera2")

        logging.info("Testing CameraTask [integration: RTSP + motion detection]...")
        cls.msgListener = DefaultDataMessageListener()
        cls.cameraTask  = CameraTask(dataMsgListener=cls.msgListener)

    def setUp(self):
        pass

    def tearDown(self):
        if self.cameraTask.isRunning():
            self.cameraTask.stop()

    def testStartStop(self):
        result = self.cameraTask.start()
        self.assertTrue(result, "CameraTask should start successfully.")
        self.assertTrue(self.cameraTask.isRunning())
        sleep(5)
        result = self.cameraTask.stop()
        self.assertTrue(result, "CameraTask should stop successfully.")
        self.assertFalse(self.cameraTask.isRunning())

    def testStreamingAndMotionDetection(self):
        result = self.cameraTask.start()
        self.assertTrue(result, "CameraTask should start successfully.")
        self.assertTrue(self.cameraTask.isRunning())

        logging.info("Running for 30 seconds.")
        logging.info("Connect VLC to rtsp://<RPi-IP>:8554/stream to verify streaming.")
        logging.info("Move in front of the camera to trigger motion detection.")

        sleep(30)

        self.assertTrue(self.cameraTask.isRunning(), "CameraTask should still be running after 30 seconds.")
        self.cameraTask.stop()

    def testRestartCamera(self):
        self.cameraTask.start()
        sleep(3)
        self.cameraTask.stop()
        sleep(1)

        result = self.cameraTask.start()
        self.assertTrue(result, "CameraTask should restart successfully.")
        sleep(3)
        self.cameraTask.stop()

if __name__ == "__main__":
    unittest.main()