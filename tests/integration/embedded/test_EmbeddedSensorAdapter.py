import logging
import unittest
from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.embedded.IrReceiverTask import IrReceiverTask
from programmingtheiot.cda.embedded.IrTransmitterTask import IrTransmitterTask
from programmingtheiot.cda.embedded.HumidifierKasaActuatorTask import HumidifierKasaActuatorTask
from programmingtheiot.data.ActuatorData import ActuatorData

class EmbeddedActuatorAdapterTest(unittest.TestCase):

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
            import pigpio
            pi = pigpio.pi()
            if not pi.connected:
                raise unittest.SkipTest("pigpio daemon not running. Run: sudo pigpiod")
            pi.stop()
        except ImportError:
            raise unittest.SkipTest("pigpio not available.")

        try:
            from tplinkcloud import TPLinkDeviceManager
        except ImportError:
            raise unittest.SkipTest("tplink-cloud-api not available. Run: pip3 install tplink-cloud-api")

        email = cfg.getProperty(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key='kasaEmail',
            defaultVal=None
        )
        if not email:
            raise unittest.SkipTest("kasaEmail not set in PiotConfig.props.")

        logging.info("Testing EmbeddedActuatorAdapter [IR + Kasa + LED]...")

        cls.locationID   = cfg.getProperty(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.DEVICE_LOCATION_ID_KEY,
            defaultVal=ConfigConst.NOT_SET
        )
        cls.actuatorMgr  = ActuatorAdapterManager()
        cls.receiver     = IrReceiverTask()
        cls.transmitter  = IrTransmitterTask()
        cls.kasaTask     = HumidifierKasaActuatorTask()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _makeActuatorData(self, typeID: int, command: int, stateData: str = None) -> ActuatorData:
        ad = ActuatorData(typeID=typeID)
        ad.setCommand(command)
        ad.setLocationID(self.locationID)
        if stateData:
            ad.setStateData(stateData)
        return ad

    def testRecordHvacOn(self):
        logging.info("Point the remote at the IR receiver and press ON within 5 seconds.")
        result = self.receiver.record('hvac_on')
        self.assertTrue(result, "Should successfully record hvac_on IR signal.")
        self.assertIn('hvac_on', self.receiver.getCodes())

    def testRecordHvacOff(self):
        logging.info("Point the remote at the IR receiver and press OFF within 5 seconds.")
        result = self.receiver.record('hvac_off')
        self.assertTrue(result, "Should successfully record hvac_off IR signal.")
        self.assertIn('hvac_off', self.receiver.getCodes())

    def testTransmitHvacOn(self):
        if 'hvac_on' not in self.transmitter.codes:
            self.skipTest("hvac_on not recorded yet. Run testRecordHvacOn first.")
        result = self.transmitter.send('hvac_on')
        self.assertTrue(result, "Should successfully send hvac_on IR signal.")
        sleep(2)

    def testTransmitHvacOff(self):
        if 'hvac_off' not in self.transmitter.codes:
            self.skipTest("hvac_off not recorded yet. Run testRecordHvacOff first.")
        result = self.transmitter.send('hvac_off')
        self.assertTrue(result, "Should successfully send hvac_off IR signal.")
        sleep(2)

    def testTransmitUnknownCode(self):
        result = self.transmitter.send('nonexistent_code')
        self.assertFalse(result, "Should return False for unknown IR code.")

    def testHumidifierOn(self):
        ad = self._makeActuatorData(ConfigConst.HUMIDIFIER_ACTUATOR_TYPE, ConfigConst.COMMAND_ON, "HUMIDIFIER ON")
        response = self.actuatorMgr.sendActuatorCommand(ad)
        self.assertIsNotNone(response, "Humidifier ON should return a response.")
        logging.info("Humidifier ON. Check if plug is powered.")
        sleep(3)

    def testHumidifierOff(self):
        ad = self._makeActuatorData(ConfigConst.HUMIDIFIER_ACTUATOR_TYPE, ConfigConst.COMMAND_OFF, "HUMIDIFIER OFF")
        response = self.actuatorMgr.sendActuatorCommand(ad)
        self.assertIsNotNone(response, "Humidifier OFF should return a response.")
        logging.info("Humidifier OFF.")
        sleep(3)

    def testLedDisplayOn(self):
        ad = self._makeActuatorData(ConfigConst.LED_DISPLAY_ACTUATOR_TYPE, ConfigConst.COMMAND_ON, "HELLO PIOT")
        response = self.actuatorMgr.sendActuatorCommand(ad)
        self.assertIsNotNone(response, "LED ON should return a response.")
        logging.info("LED display ON. Check Sense HAT.")
        sleep(3)

    def testLedDisplayOff(self):
        ad = self._makeActuatorData(ConfigConst.LED_DISPLAY_ACTUATOR_TYPE, ConfigConst.COMMAND_OFF)
        self.actuatorMgr.sendActuatorCommand(ad)
        logging.info("LED display OFF.")
        sleep(2)

    def testFullSequence(self):
        logging.info("=== Full actuator sequence test ===")
        self.testTransmitHvacOn()
        self.testHumidifierOn()
        self.testLedDisplayOn()
        self.testLedDisplayOff()
        self.testHumidifierOff()
        self.testTransmitHvacOff()
        logging.info("=== Full actuator sequence complete ===")

if __name__ == "__main__":
    unittest.main()