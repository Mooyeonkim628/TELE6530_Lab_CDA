import logging
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask
from sense_hat import SenseHat

class LedDisplayEmulatorTask(BaseActuatorSimTask):

    def __init__(self):
        super(LedDisplayEmulatorTask, self).__init__(
            name       = ConfigConst.LED_ACTUATOR_NAME,
            typeID     = ConfigConst.LED_DISPLAY_ACTUATOR_TYPE,
            simpleName = "LED_Display"
        )
        self.sh = SenseHat()
        self.lastKnownCommand = -1

    def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if self.sh:
            self.sh.show_message(stateData if stateData else "ON", scroll_speed=0.05, text_colour=[0, 255, 0])
            return 0
        else:
            logging.warning("No SenseHat instance to write.")
            return -1

    def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        if self.sh:
            self.sh.show_message(stateData if stateData else "OFF", scroll_speed=0.05, text_colour=[255, 0, 0])
            self.sh.clear()
            return 0
        else:
            logging.warning("No SenseHat instance to clear.")
            return -1