import logging
import asyncio

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask

try:
    from tplinkcloud import TPLinkDeviceManager
    TPLINK_AVAILABLE = True
except ImportError:
    TPLINK_AVAILABLE = False
    logging.warning("tplink-cloud-api not installed. Run: pip3 install tplink-cloud-api")

class HumidifierKasaActuatorTask(BaseActuatorSimTask):

    KASA_EMAIL_KEY    = 'kasaEmail'
    KASA_PASSWORD_KEY = 'kasaPassword'

    def __init__(self):
        super(HumidifierKasaActuatorTask, self).__init__(
            name       = ConfigConst.HUMIDIFIER_ACTUATOR_NAME,
            typeID     = ConfigConst.HUMIDIFIER_ACTUATOR_TYPE,
            simpleName = "HUMIDIFIER"
        )

        self.manager = None

        if not TPLINK_AVAILABLE:
            logging.warning("tplinkcloud not available.")
            return

        self.email    = ConfigUtil().getProperty(
            section    = ConfigConst.CONSTRAINED_DEVICE,
            key        = self.KASA_EMAIL_KEY,
            defaultVal = None
        )
        self.password = ConfigUtil().getProperty(
            section    = ConfigConst.CONSTRAINED_DEVICE,
            key        = self.KASA_PASSWORD_KEY,
            defaultVal = None
        )

        if not self.email or not self.password:
            logging.warning("Kasa credentials not set. Add 'kasaEmail' and 'kasaPassword' to PiotConfig.props")
            return

        self.manager = TPLinkDeviceManager(self.email, self.password)
        logging.info("HumidifierKasaActuatorTask initialized.")

    def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if not self.manager:
            logging.warning("Kasa manager not initialized.")
            return -1
        try:
            asyncio.run(self._powerOn())
            logging.info("Kasa plug ON: Humidifier activated.")
            return 0
        except Exception as e:
            logging.warning("Failed to turn ON Kasa plug: %s", e)
            return -1

    def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if not self.manager:
            logging.warning("Kasa manager not initialized.")
            return -1
        try:
            asyncio.run(self._powerOff())
            logging.info("Kasa plug OFF: Humidifier deactivated.")
            return 0
        except Exception as e:
            logging.warning("Failed to turn OFF Kasa plug: %s", e)
            return -1

    async def _powerOn(self):
        devices = await self.manager.get_devices()
        if devices:
            await devices[0].power_on()

    async def _powerOff(self):
        devices = await self.manager.get_devices()
        if devices:
            await devices[0].power_off()