import logging

from importlib import import_module

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.ActuatorData import ActuatorData

from programmingtheiot.cda.sim.HvacActuatorSimTask import HvacActuatorSimTask
from programmingtheiot.cda.sim.HumidifierActuatorSimTask import HumidifierActuatorSimTask

class ActuatorAdapterManager(object):

	def __init__(self, dataMsgListener: IDataMessageListener = None, cameraTask=None):
		self.dataMsgListener = dataMsgListener
		self.cameraTask = cameraTask
		self.configUtil = ConfigUtil()
		
		self.useSimulator = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SIMULATOR_KEY)
		self.useEmulator = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_EMULATOR_KEY)
		self.useSenseHat = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SENSE_HAT_KEY)
		self.deviceID = \
			self.configUtil.getProperty( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.DEVICE_LOCATION_ID_KEY, defaultVal = ConfigConst.NOT_SET)
		self.locationID = \
			self.configUtil.getProperty( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.DEVICE_LOCATION_ID_KEY, defaultVal = ConfigConst.NOT_SET)
		
		self.humidifierActuator = None
		self.hvacActuator       = None
		self.ledDisplayActuator = None
		
		self._initEnvironmentalActuationTasks()

	def _initEnvironmentalActuationTasks(self):
		if self.useSenseHat:
			logging.info("Loading embedded actuator tasks (real hardware).")

			hueModule = import_module('programmingtheiot.cda.embedded.HumidifierKasaActuatorTask', 'HumidifierKasaActuatorTask')
			hueClazz  = getattr(hueModule, 'HumidifierKasaActuatorTask')
			self.humidifierActuator = hueClazz()

			hveModule = import_module('programmingtheiot.cda.embedded.HvacI2cActuatorTask', 'HvacI2cActuatorTask')
			hveClazz  = getattr(hveModule, 'HvacI2cActuatorTask')
			self.hvacActuator = hveClazz(cameraTask=self.cameraTask)

			leDisplayModule = import_module('programmingtheiot.cda.emulated.LedDisplayEmulatorTask', 'LedDisplayEmulatorTask')
			leClazz = getattr(leDisplayModule, 'LedDisplayEmulatorTask')
			self.ledDisplayActuator = leClazz()



		elif self.useEmulator:
			logging.info("Loading emulated actuator tasks (pisense emulator).")

			hueModule = import_module('programmingtheiot.cda.emulated.HumidifierEmulatorTask', 'HumidifierEmulatorTask')
			hueClazz  = getattr(hueModule, 'HumidifierEmulatorTask')
			self.humidifierActuator = hueClazz()

			hveModule = import_module('programmingtheiot.cda.emulated.HvacEmulatorTask', 'HvacEmulatorTask')
			hveClazz  = getattr(hveModule, 'HvacEmulatorTask')
			self.hvacActuator = hveClazz()

			leDisplayModule = import_module('programmingtheiot.cda.emulated.LedDisplayEmulatorTask', 'LedDisplayEmulatorTask')
			leClazz = getattr(leDisplayModule, 'LedDisplayEmulatorTask')
			self.ledDisplayActuator = leClazz()

		else:
			logging.info("Loading sim actuator tasks.")
			self.humidifierActuator = HumidifierActuatorSimTask()
			self.hvacActuator       = HvacActuatorSimTask()

	def sendActuatorCommand(self, data: ActuatorData) -> ActuatorData:
		if data and not data.isResponseFlagEnabled():
			if data.getLocationID() == self.locationID:
				logging.info("Actuator command received for location ID %s. Processing...", str(data.getLocationID()))
				
				aType = data.getTypeID()
				responseData = None
				
				if aType == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE and self.humidifierActuator:
					responseData = self.humidifierActuator.updateActuator(data)
					if self.ledDisplayActuator:
						ledData = ActuatorData(typeID=ConfigConst.LED_DISPLAY_ACTUATOR_TYPE, name=ConfigConst.LED_ACTUATOR_NAME)
						ledData.setCommand(data.getCommand())
						ledData.setStateData("HUM ON" if data.getCommand() == 1 else "HUM OFF")
						self.ledDisplayActuator.updateActuator(ledData)
				elif aType == ConfigConst.HVAC_ACTUATOR_TYPE and self.hvacActuator:
					responseData = self.hvacActuator.updateActuator(data)
					if self.ledDisplayActuator:
						ledData = ActuatorData(typeID=ConfigConst.LED_DISPLAY_ACTUATOR_TYPE, name=ConfigConst.LED_ACTUATOR_NAME)
						ledData.setCommand(data.getCommand())
						ledData.setStateData("HVAC ON" if data.getCommand() == 1 else "HVAC OFF")
						self.ledDisplayActuator.updateActuator(ledData)
				elif aType == ConfigConst.LED_DISPLAY_ACTUATOR_TYPE and self.ledDisplayActuator:
					responseData = self.ledDisplayActuator.updateActuator(data)
				else:
					logging.warning("No valid actuator type. Ignoring actuation for type: %s", data.getTypeID())

				if responseData and self.dataMsgListener:
					self.dataMsgListener.handleActuatorCommandResponse(responseData)

				return responseData
			else:
				logging.warning("Location ID doesn't match. Ignoring actuation: (me) %s != (you) %s", str(self.locationID), str(data.getLocationID()))
		else:
			logging.warning("Actuator request received. Message is empty or response. Ignoring.")
		
		return None
	
	def setDataMessageListener(self, listener: IDataMessageListener) -> bool:
		if listener:
			self.dataMsgListener = listener