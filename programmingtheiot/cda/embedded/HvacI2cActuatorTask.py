import logging
import threading
import time

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask
from programmingtheiot.cda.embedded.IrTransmitterTask import IrTransmitterTask

class HvacI2cActuatorTask(BaseActuatorSimTask):

    def __init__(self, cameraTask=None):
        super(HvacI2cActuatorTask, self).__init__(
            name      = ConfigConst.HVAC_ACTUATOR_NAME,
            typeID    = ConfigConst.HVAC_ACTUATOR_TYPE,
            simpleName = "HVAC"
        )
        self.irTransmitter = IrTransmitterTask()
        self.cameraTask    = cameraTask
        logging.info("HvacI2cActuatorTask initialized with IR transmitter.")

    def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        logging.info("HVAC ON command received - sending IR signal.")
        if self.cameraTask:
            self.cameraTask.pause()
        success = self.irTransmitter.send('hvac_on')
        if self.cameraTask:
            self.cameraTask.resume()
        return 0 if success else -1

    def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        logging.info("HVAC OFF command received - sending IR signal.")
        if self.cameraTask:
            self.cameraTask.pause()
        success = self.irTransmitter.send('hvac_off')
        if self.cameraTask:
            self.cameraTask.resume()
        return 0 if success else -1