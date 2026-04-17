import logging
from collections import deque
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class TemperatureI2cSensorAdapterTask(BaseSensorSimTask):
    def __init__(self):
        super(TemperatureI2cSensorAdapterTask, self).__init__(
            typeID=ConfigConst.TEMP_SENSOR_TYPE,
            minVal=SensorDataGenerator.LOW_NORMAL_INDOOR_TEMP,
            maxVal=SensorDataGenerator.HI_NORMAL_INDOOR_TEMP
        )
        self.sensorType = ConfigConst.TEMP_SENSOR_TYPE
        self.sh = None
        self.cpuHistory = deque(maxlen=10)

        try:
            from sense_hat import SenseHat
            self.sh = SenseHat()
            logging.info("SenseHat initialized for temperature sensor.")
        except Exception as e:
            logging.warning("Failed to init SenseHat for temperature: %s", e)

    def _getCpuTemp(self) -> float:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu = float(f.read()) / 1000.0
                self.cpuHistory.append(cpu)
                return sum(self.cpuHistory) / len(self.cpuHistory)
        except:
            return 0.0

    def _getCorrectedTemp(self) -> float:
        raw = self.sh.get_temperature_from_humidity()
        cpu = self._getCpuTemp()
        corrected = raw - ((cpu - 25.0) / 1.83)
        logging.debug("Temp raw=%.2f, cpu=%.2f, corrected=%.2f", raw, cpu, corrected)
        return corrected

    def generateTelemetry(self) -> SensorData:
        if not self.sh:
            logging.warning("SenseHat not initialized; returning existing sensorData.")
            return self.sensorData

        try:
            sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
            sensorVal = self._getCorrectedTemp()
            sensorData.setValue(sensorVal)
            self.latestSensorData = sensorData
            return sensorData
        except Exception as e:
            logging.warning("Error reading temperature from SenseHat: %s", e)
            return self.sensorData

    def getTelemetryValue(self) -> float:
        if self.sh:
            return self._getCorrectedTemp()
        return 0.0