#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# You may find it more helpful to your design to adjust the
# functionality, constants and interfaces (if there are any)
# provided within in order to meet the needs of your specific
# Programming the Internet of Things project.
# 

import logging

from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask

from pisense import SenseHAT

class HvacEmulatorTask(BaseActuatorSimTask):
	"""
	Shell representation of class for student implementation.
	
	"""

	def __init__(self):
		super( \
			HvacEmulatorTask, self).__init__( \
				name = ConfigConst.HVAC_ACTUATOR_NAME, \
				typeID = ConfigConst.HVAC_ACTUATOR_TYPE, \
				simpleName = "HVAC")
		enableEmulation = \
			ConfigUtil().getBoolean( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.ENABLE_EMULATOR_KEY)
		
		self.sh = SenseHAT(emulate = enableEmulation)		

	def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		if self.sh and self.sh.screen:
			msg = stateData if stateData else "HVAC ON"
			self.sh.screen.scroll_text(msg)
			return 0
		return -1

	def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		if self.sh and self.sh.screen:
			msg = stateData if stateData else "HVAC OFF"
			self.sh.screen.scroll_text(msg)
			sleep(1)
			self.sh.screen.clear()
			return 0
		return -1