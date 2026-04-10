import logging
import time

from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector

from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager
from programmingtheiot.cda.embedded.CameraTask import CameraTask

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData
from programmingtheiot.cda.connection.RedisPersistenceAdapter import RedisPersistenceAdapter
from programmingtheiot.cda.connection.CoapServerAdapter import CoapServerAdapter

class DeviceDataManager(IDataMessageListener):

	def __init__(self):
		self.configUtil = ConfigUtil()

		self.enableSystemPerf = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_SYSTEM_PERF_KEY)

		self.enableSensing = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_SENSING_KEY)

		self.enableMqttClient = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_MQTT_CLIENT_KEY)

		self.enableCoapServer = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_COAP_SERVER_KEY)

		self.enableCoapClient = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_COAP_CLIENT_KEY)

		self.enableCamera = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key=ConfigConst.ENABLE_CAMERA_KEY)

		self.enableActuation = True

		self.sysPerfMgr       = None
		self.sensorAdapterMgr = None
		self.mqttClient       = None
		self.coapClient       = None
		self.coapServer       = None
		self.cameraTask       = None

		self.sysPerfDataListener   = None
		self.telemetryDataListener = None
		self.actuatorResponseCache = {}
		self.actuatorAdapterMgr    = ActuatorAdapterManager(dataMsgListener=self)

		self.enableRedisStore = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE, key="enablePersistenceClient")

		self.redisClient = RedisPersistenceAdapter() if self.enableRedisStore else None

		if self.enableSystemPerf:
			self.sysPerfMgr = SystemPerformanceManager()
			self.sysPerfMgr.setDataMessageListener(self)
			logging.info("Local system performance tracking enabled")

		if self.enableSensing:
			self.sensorAdapterMgr = SensorAdapterManager()
			self.sensorAdapterMgr.setDataMessageListener(self)
			logging.info("Local sensor tracking enabled")

		if self.enableActuation:
			self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener=self)
			logging.info("Local actuation capabilities enabled")

		if self.enableCamera:
			self.cameraTask = CameraTask(dataMsgListener=self)
			logging.info("CameraTask initialized.")

		if self.enableMqttClient:
			self.mqttClient = MqttClientConnector()
			self.mqttClient.setDataMessageListener(self)

		if self.enableCoapServer:
			logging.info("Creating CoapServerAdapter now")
			self.coapServer = CoapServerAdapter(dataMsgListener=self)
		else:
			logging.info("CoAP server disabled")

		if self.enableCoapClient:
			self.coapClient = CoapClientConnector(dataMsgListener=self)

		self.deviceID = \
			self.configUtil.getProperty(
				section=ConfigConst.CONSTRAINED_DEVICE,
				key=ConfigConst.DEVICE_LOCATION_ID_KEY,
				defaultVal=ConfigConst.NOT_SET)

		self.handleTempChangeOnDevice = \
			self.configUtil.getBoolean(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY)

		self.triggerHvacTempFloor = \
			self.configUtil.getFloat(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY)

		self.triggerHvacTempCeiling = \
			self.configUtil.getFloat(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY)

		self.handleHumidityChangeOnDevice = \
			self.configUtil.getBoolean(
				section=ConfigConst.CONSTRAINED_DEVICE, key="handleHumidityChangeOnDevice")

		self.triggerHumidifierHumidityFloor = \
			self.configUtil.getFloat(
				section=ConfigConst.CONSTRAINED_DEVICE, key="triggerHumidifierHumidityFloor")

		self.triggerHumidifierHumidityCeiling = \
			self.configUtil.getFloat(
				section=ConfigConst.CONSTRAINED_DEVICE, key="triggerHumidifierHumidityCeiling")

		self.cloudOverrideDurationSecs = \
			self.configUtil.getFloat(
				section=ConfigConst.CONSTRAINED_DEVICE,
				key="cloudOverrideDurationSecs",
				defaultVal=600.0)

		self.seasonMode = self.configUtil.getProperty(
			section=ConfigConst.CONSTRAINED_DEVICE,
			key='seasonMode',
			defaultVal='summer'
		).lower()

		self.cloudHvacOverrideTime       = None
		self.cloudHumidifierOverrideTime = None

		logging.info("DeviceDataManager init start")
		logging.info("enableCoapServer = %s", str(self.enableCoapServer))
		logging.info("enableMqttClient = %s", str(self.enableMqttClient))
		logging.info("enableSensing = %s", str(self.enableSensing))
		logging.info("enableCamera = %s", str(self.enableCamera))
		logging.info("seasonMode = %s", self.seasonMode)
		logging.info("cloudOverrideDurationSecs = %s", str(self.cloudOverrideDurationSecs))

	def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
		pass

	def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
		pass

	def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
		pass

	def handleActuatorCommandResponse(self, data: ActuatorData) -> bool:
		if data:
			actuatorMsg = DataUtil().actuatorDataToJson(data)
			logging.info("Incoming actuator response received (from actuator manager): " + actuatorMsg)

			self.actuatorResponseCache[data.getName()] = data

			self._handleUpstreamTransmission(
				resource=ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE,
				msg=actuatorMsg)

			return True
		else:
			logging.warning("Incoming actuator response is invalid (null). Ignoring.")
			return False

	def handleIncomingMessage(self, resourceEnum: ResourceNameEnum, msg: str) -> bool:
		if not msg:
			logging.warning("Incoming message is empty.")
			return False

		try:
			logging.info("Handling incoming message on resource: %s", resourceEnum)

			if resourceEnum == ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE:
				ad = DataUtil().jsonToActuatorData(msg)

				if ad is None:
					logging.warning("Failed to parse ActuatorData from incoming message.")
					return False

				if ad.getTypeID() == ConfigConst.HVAC_ACTUATOR_TYPE:
					self.cloudHvacOverrideTime = time.time()
					logging.info("Cloud override set for HVAC. Local threshold logic disabled for %.0f secs.",
						self.cloudOverrideDurationSecs)
				elif ad.getTypeID() == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE:
					self.cloudHumidifierOverrideTime = time.time()
					logging.info("Cloud override set for Humidifier. Local threshold logic disabled for %.0f secs.",
						self.cloudOverrideDurationSecs)

				logging.info("Parsed incoming ActuatorData: %s", ad)
				return self.handleActuatorCommandMessage(ad, isCloudCommand=True)

			logging.warning("Unhandled incoming resource: %s", resourceEnum)
			return False

		except Exception as e:
			logging.warning("Failed to handle incoming message. Message: %s", e)
			return False

	def handleSensorMessage(self, data: SensorData) -> bool:
		if data:
			logging.debug(
				"Incoming sensor data received (from sensor manager): %s value=%s",
				str(data), str(data.getValue()))

			if self.enableRedisStore and self.redisClient:
				try:
					self.redisClient.storeData(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, data)
				except Exception as e:
					logging.warning(f"Failed to store SensorData to Redis: {e}")

			self._handleSensorDataAnalysis(data=data)

			sensorMsg = DataUtil().sensorDataToJson(data=data)
			self._handleUpstreamTransmission(
				resource=ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
				msg=sensorMsg)

			return True
		else:
			logging.warning("Incoming sensor data is invalid (null). Ignoring.")
			return False

	def handleSystemPerformanceMessage(self, data: SystemPerformanceData) -> bool:
		if data:
			logging.debug("Incoming system performance message received (from sys perf manager): " + str(data))

			sysPerfMsg = DataUtil().systemPerformanceDataToJson(data=data)
			self._handleUpstreamTransmission(
				resource=ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
				msg=sysPerfMsg)

			return True
		else:
			logging.warning("Incoming system performance data is invalid (null). Ignoring.")
			return False

	def setSystemPerformanceDataListener(self, listener: ISystemPerformanceDataListener = None):
		if listener:
			self.sysPerfDataListener = listener
			return True
		return False

	def setTelemetryDataListener(self, name: str = None, listener: ITelemetryDataListener = None):
		if listener:
			self.telemetryDataListener = listener
			return True
		if name and isinstance(name, ITelemetryDataListener):
			self.telemetryDataListener = name
			return True
		return False

	def startManager(self):
		logging.info("Starting DeviceDataManager...")

		if self.sysPerfMgr:
			self.sysPerfMgr.startManager()

		if self.sensorAdapterMgr:
			self.sensorAdapterMgr.startManager()

		if self.cameraTask:
			self.cameraTask.start()
			logging.info("CameraTask started.")

		if self.redisClient and self.enableRedisStore:
			self.redisClient.connectClient()

		if self.mqttClient:
			self.mqttClient.connectClient()
			self.mqttClient.subscribeToTopic(
				ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				callback=self.handleIncomingMessage,
				qos=ConfigConst.DEFAULT_QOS)

		if self.coapServer:
			self.coapServer.startServer()

		logging.info("Started DeviceDataManager.")

	def stopManager(self):
		logging.info("Stopping DeviceDataManager...")

		if self.sysPerfMgr:
			self.sysPerfMgr.stopManager()

		if self.sensorAdapterMgr:
			self.sensorAdapterMgr.stopManager()

		if self.cameraTask:
			self.cameraTask.stop()
			logging.info("CameraTask stopped.")

		if self.redisClient and self.enableRedisStore:
			self.redisClient.disconnectClient()

		if self.mqttClient:
			self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
			self.mqttClient.disconnectClient()

		if self.coapServer:
			self.coapServer.stopServer()

		logging.info("Stopped DeviceDataManager.")

	def _isCloudOverrideActive(self, overrideTime) -> bool:
		if overrideTime is None:
			return False
		elapsed = time.time() - overrideTime
		return elapsed < self.cloudOverrideDurationSecs

	def _handleIncomingDataAnalysis(self, msg: str):
		pass

	def _handleSensorDataAnalysis(self, data: SensorData):
		if self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.info("Handle temp change: seasonMode=%s, temp=%.1f", self.seasonMode, data.getValue())

			if self._isCloudOverrideActive(self.cloudHvacOverrideTime):
				logging.info("Cloud override active for HVAC. Skipping local threshold command.")
			else:
				ad = ActuatorData(typeID=ConfigConst.HVAC_ACTUATOR_TYPE)
				ad.setLocationID(self.configUtil.getProperty(
					section=ConfigConst.CONSTRAINED_DEVICE,
					key=ConfigConst.DEVICE_LOCATION_ID_KEY,
					defaultVal=ConfigConst.NOT_SET))

				temp = data.getValue()

				if self.seasonMode == 'summer':
					# 여름: 23도 이상 → AC ON, 20도 이하 → AC OFF
					if temp >= self.triggerHvacTempCeiling:
						ad.setCommand(ConfigConst.COMMAND_ON)
						ad.setStateData("HVAC ON (cooling)")
						logging.info("Summer: %.1f >= %.1f → AC ON", temp, self.triggerHvacTempCeiling)
					elif temp <= self.triggerHvacTempFloor:
						ad.setCommand(ConfigConst.COMMAND_OFF)
						ad.setStateData("HVAC OFF")
						logging.info("Summer: %.1f <= %.1f → AC OFF", temp, self.triggerHvacTempFloor)
					else:
						return

				elif self.seasonMode == 'winter':
					# 겨울: 24도 이하 → 히터 ON, 27도 이상 → 히터 OFF
					if temp <= self.triggerHvacTempFloor:
						ad.setCommand(ConfigConst.COMMAND_ON)
						ad.setStateData("HVAC ON (heating)")
						logging.info("Winter: %.1f <= %.1f → Heater ON", temp, self.triggerHvacTempFloor)
					elif temp >= self.triggerHvacTempCeiling:
						ad.setCommand(ConfigConst.COMMAND_OFF)
						ad.setStateData("HVAC OFF")
						logging.info("Winter: %.1f >= %.1f → Heater OFF", temp, self.triggerHvacTempCeiling)
					else:
						return

				self.handleActuatorCommandMessage(ad)

		if self.handleHumidityChangeOnDevice and data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE:
			if self._isCloudOverrideActive(self.cloudHumidifierOverrideTime):
				logging.info("Cloud override active for Humidifier. Skipping local threshold command.")
				return

			ad = ActuatorData(typeID=ConfigConst.HUMIDIFIER_ACTUATOR_TYPE)
			ad.setLocationID(self.deviceID)

			humidity = data.getValue()

			if humidity < self.triggerHumidifierHumidityFloor:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setStateData("HUMIDIFIER ON")
			elif humidity > self.triggerHumidifierHumidityCeiling:
				ad.setCommand(ConfigConst.COMMAND_OFF)
				ad.setStateData("HUMIDIFIER OFF")
			else:
				return

			self.handleActuatorCommandMessage(ad)

	def _handleUpstreamTransmission(self, resource=None, msg: str = None):
		logging.info("Upstream transmission invoked. Checking comm's integration.")

		if self.mqttClient:
			if self.mqttClient.publishMessage(resource=resource, msg=msg):
				logging.debug("Published incoming data to resource (MQTT): %s", str(resource))
			else:
				logging.warning("Failed to publish incoming data to resource (MQTT): %s", str(resource))

	def handleActuatorCommandMessage(self, data: ActuatorData, isCloudCommand: bool = False) -> ActuatorData:
		if data:
			logging.info("Processing actuator command message.")

			if not isCloudCommand:
				if data.getTypeID() == ConfigConst.HVAC_ACTUATOR_TYPE:
					if self._isCloudOverrideActive(self.cloudHvacOverrideTime):
						logging.info("Cloud override active for HVAC. Skipping local command.")
						return None
				elif data.getTypeID() == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE:
					if self._isCloudOverrideActive(self.cloudHumidifierOverrideTime):
						logging.info("Cloud override active for Humidifier. Skipping local command.")
						return None

			return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Received invalid ActuatorData command message. Ignoring.")
			return None