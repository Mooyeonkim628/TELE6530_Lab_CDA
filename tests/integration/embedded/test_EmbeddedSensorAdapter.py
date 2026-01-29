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
            raise unittest.SkipTest("ENABLE_SENSE_HAT_KEY is False. Set enableSenseHat=True in PiotConfig.props.")
        if useEmulator:
            raise unittest.SkipTest("ENABLE_EMULATOR_KEY is True. For embedded test, set enableEmulator=False.")

        try:
            import smbus  
        except ImportError:
            raise unittest.SkipTest("smbus not available. This test requires Raspberry Pi + Sense HAT (I2C).")

        logging.info("Testing SensorAdapterManager class [using Sense HAT I2C / embedded]...")  

        cls.defaultMsgListener = DefaultDataMessageListener()
        cls.sensorAdapterMgr = SensorAdapterManager()
        cls.sensorAdapterMgr.setDataMessageListener(cls.defaultMsgListener)		
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testRunEmbeddedSensors(self):
        self.sensorAdapterMgr.startManager()
		
        sleep(20)
		
        self.sensorAdapterMgr.stopManager()

if __name__ == "__main__":
	unittest.main()
	
