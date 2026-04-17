import logging
from time import sleep
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask
from sense_hat import SenseHat

class HvacEmulatorTask(BaseActuatorSimTask):

    def __init__(self):
        super(HvacEmulatorTask, self).__init__(
            name       = ConfigConst.HVAC_ACTUATOR_NAME,
            typeID     = ConfigConst.HVAC_ACTUATOR_TYPE,
            simpleName = "HVAC"
        )
        self.sh = SenseHat()

    def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if self.sh:
            msg = stateData if stateData else "HVAC ON"
            self.sh.show_message(msg)
            return 0
        else:
            logging.warning("No SenseHat instance to write.")
            return -1

    def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if self.sh:
            msg = stateData if stateData else "HVAC OFF"
            self.sh.show_message(msg)
            sleep(1)
            self.sh.clear()
            return 0
        else:
            logging.warning("No SenseHat instance to clear.")
            return -1