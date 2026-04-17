import logging
from sense_hat import SenseHat
from programmingtheiot.data.SensorData import SensorData
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class HumidityI2cSensorAdapterTask(BaseSensorSimTask):
    def __init__(self):
        super(HumidityI2cSensorAdapterTask, self).__init__(
            typeID=ConfigConst.HUMIDITY_SENSOR_TYPE,
            minVal=SensorDataGenerator.LOW_NORMAL_ENV_HUMIDITY,
            maxVal=SensorDataGenerator.HI_NORMAL_ENV_HUMIDITY
        )
        self.sensorType = ConfigConst.HUMIDITY_SENSOR_TYPE
        self.sh = None

        try:
            self.sh = SenseHat()
            logging.info("SenseHat initialized for humidity sensor.")
        except Exception as e:
            logging.warning("Failed to init SenseHat for humidity: %s", e)

    def generateTelemetry(self) -> SensorData:
        if not self.sh:
            logging.warning("SenseHat not initialized; returning existing sensorData.")
            return self.sensorData

        try:
            sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
            sensorVal = self.sh.get_humidity()
            sensorData.setValue(sensorVal)
            self.latestSensorData = sensorData
            logging.debug("Humidity reading: %.2f", sensorVal)
            return sensorData
        except Exception as e:
            logging.warning("Error reading humidity from SenseHat: %s", e)
            return self.sensorData

    def getTelemetryValue(self) -> float:
        if self.sh:
            return self.sh.get_humidity()
        return 0.0