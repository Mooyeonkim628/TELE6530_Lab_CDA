import logging
from sense_hat import SenseHat
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.common.ConfigConst import ConfigConst
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class PressureI2cSensorAdapterTask(BaseSensorSimTask):
    def __init__(self):
        super(PressureI2cSensorAdapterTask, self).__init__(
            typeID=SensorData.PRESSURE_SENSOR_TYPE,
            minVal=SensorDataGenerator.LOW_NORMAL_ENV_PRESSURE,
            maxVal=SensorDataGenerator.HI_NORMAL_ENV_PRESSURE
        )
        self.sensorType = SensorData.PRESSURE_SENSOR_TYPE
        self.sh = None

        try:
            self.sh = SenseHat()
            logging.info("SenseHat initialized for pressure sensor.")
        except Exception as e:
            logging.warning("Failed to init SenseHat for pressure: %s", e)

    def generateTelemetry(self) -> SensorData:
        if not self.sh:
            logging.warning("SenseHat not initialized; returning existing sensorData.")
            return self.sensorData

        try:
            sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
            sensorVal = self.sh.get_pressure()
            sensorData.setValue(sensorVal)
            self.latestSensorData = sensorData
            logging.debug("Pressure reading: %.2f", sensorVal)
            return sensorData
        except Exception as e:
            logging.warning("Error reading pressure from SenseHat: %s", e)
            return self.sensorData

    def getTelemetryValue(self) -> float:
        if self.sh:
            return self.sh.get_pressure()
        return 0.0