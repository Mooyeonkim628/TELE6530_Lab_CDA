import logging
from sense_hat import SenseHat
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.common.ConfigConst import ConfigConst
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class TemperatureI2cSensorAdapterTask(BaseSensorSimTask):
    def __init__(self):
        super(TemperatureI2cSensorAdapterTask, self).__init__(
            typeID=SensorData.TEMPERATURE_SENSOR_TYPE,
            minVal=SensorDataGenerator.LOW_NORMAL_ENV_TEMPERATURE,
            maxVal=SensorDataGenerator.HI_NORMAL_ENV_TEMPERATURE
        )
        self.sensorType = SensorData.TEMPERATURE_SENSOR_TYPE
        self.sh = None

        try:
            self.sh = SenseHat()
            logging.info("SenseHat initialized for temperature sensor.")
        except Exception as e:
            logging.warning("Failed to init SenseHat for temperature: %s", e)

    def generateTelemetry(self) -> SensorData:
        if not self.sh:
            logging.warning("SenseHat not initialized; returning existing sensorData.")
            return self.sensorData

        try:
            sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
            sensorVal = self.sh.get_temperature()
            sensorData.setValue(sensorVal)
            self.latestSensorData = sensorData
            logging.debug("Temperature reading: %.2f", sensorVal)
            return sensorData
        except Exception as e:
            logging.warning("Error reading temperature from SenseHat: %s", e)
            return self.sensorData

    def getTelemetryValue(self) -> float:
        if self.sh:
            return self.sh.get_temperature()
        return 0.0