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
import smbus
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.common.ConfigConst import ConfigConst
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class HumidityI2cSensorAdapterTask(BaseSensorSimTask):
	def __init__(self):
		super(HumidityI2cSensorAdapterTask, self).__init__(
            typeID=SensorData.HUMIDITY_SENSOR_TYPE,
            minVal=SensorDataGenerator.LOW_NORMAL_ENV_HUMIDITY,
            maxVal=SensorDataGenerator.HI_NORMAL_ENV_HUMIDITY
        )
        
		self.sensorType = SensorData.HUMIDITY_SENSOR_TYPE
		self.humidAddr = 0x5F
		self.i2cBus = None

		if smbus:
			try:
				self.i2cBus = smbus.SMBus(1)
				self.i2cBus.write_byte_data(self.humidAddr, 0, 0)
				logging.info("Initialized Humidity I2C bus at addr 0x%02X", self.humidAddr)
			except Exception as e:
				logging.warning("Failed to init I2C humidity sensor: %s", e)
		else:
			logging.warning("smbus not available. This will only work on Raspberry Pi with I2C enabled.")
	
	
	def generateTelemetry(self) -> SensorData:
		if not self.i2cBus:
			logging.warning("I2C bus not initialized; returning existing sensorData.")
			return self.sensorData

		try:
			humidity = self.sensorData.getValue()  

			self.sensorData.setValue(humidity)
			self.sensorData.setTypeID(SensorData.HUMIDITY_SENSOR_TYPE)

			return self.sensorData

		except Exception as e:
			logging.warning("Error reading humidity sensor via I2C: %s", e)
			return self.sensorData
	
	def getTelemetryValue(self) -> float:
		pass
	