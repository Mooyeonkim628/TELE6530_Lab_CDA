import logging
import unittest
from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.common.DefaultDataMessageListener import DefaultDataMessageListener

class EmbeddedSensorAdapterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            format='%(asctime)s:%(module)s:%(levelname)s:%(message)s',
            level=logging.DEBUG
        )

        cfg = ConfigUtil()
        useSenseHat = cfg.getBoolean(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.ENABLE_SENSE_HAT_KEY
        )
        useEmulator = cfg.getBoolean(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.ENABLE_EMULATOR_KEY
        )

        if not useSenseHat:
            raise unittest.SkipTest("ENABLE_SENSE_HAT_KEY is False. Set enableSenseHAT=True in PiotConfig.props.")
        if useEmulator:
            raise unittest.SkipTest("ENABLE_EMULATOR_KEY is True. For embedded test, set enableEmulator=False.")

        try:
            from sense_hat import SenseHat
            sh = SenseHat()
            _ = sh.get_temperature()
        except Exception as e:
            raise unittest.SkipTest(f"SenseHat not available: {e}")

        logging.info("Testing SensorAdapterManager [Sense HAT embedded]...")
        cls.defaultMsgListener = DefaultDataMessageListener()
        cls.sensorAdapterMgr   = SensorAdapterManager()
        cls.sensorAdapterMgr.setDataMessageListener(cls.defaultMsgListener)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRunEmbeddedSensors(self):
        self.sensorAdapterMgr.startManager()
        sleep(20)
        self.sensorAdapterMgr.stopManager()

    def testSingleHumidityReading(self):
        from programmingtheiot.cda.embedded.HumidityI2cSensorAdapterTask import HumidityI2cSensorAdapterTask
        task = HumidityI2cSensorAdapterTask()
        data = task.generateTelemetry()
        self.assertIsNotNone(data, "Humidity data should not be None.")
        self.assertGreater(data.getValue(), 0.0, "Humidity should be greater than 0.")
        logging.info("Humidity reading: %.2f", data.getValue())

    def testSingleTemperatureReading(self):
        from programmingtheiot.cda.embedded.TemperatureI2cSensorAdapterTask import TemperatureI2cSensorAdapterTask
        task = TemperatureI2cSensorAdapterTask()
        data = task.generateTelemetry()
        self.assertIsNotNone(data, "Temperature data should not be None.")
        self.assertGreater(data.getValue(), 0.0, "Temperature should be greater than 0.")
        logging.info("Temperature reading: %.2f", data.getValue())

    def testSinglePressureReading(self):
        from programmingtheiot.cda.embedded.PressureI2cSensorAdapterTask import PressureI2cSensorAdapterTask
        task = PressureI2cSensorAdapterTask()
        data = task.generateTelemetry()
        self.assertIsNotNone(data, "Pressure data should not be None.")
        self.assertGreater(data.getValue(), 0.0, "Pressure should be greater than 0.")
        logging.info("Pressure reading: %.2f", data.getValue())

if __name__ == "__main__":
    unittest.main()