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

from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector

from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager

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
	"""
	Shell representation of class for student implementation.
	
	"""
	
	def __init__(self):
		self.configUtil = ConfigUtil()
		
		self.enableSystemPerf   = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SYSTEM_PERF_KEY)
			
		self.enableSensing      = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SENSING_KEY)
		
		self.enableMqttClient = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_MQTT_CLIENT_KEY)
		self.enableCoapServer = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_SERVER_KEY)	
		self.enableCoapClient = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_CLIENT_KEY)
			
		# NOTE: this can also be retrieved from the configuration file
		self.enableActuation    = True
		
		self.sysPerfMgr         = None
		self.sensorAdapterMgr   = None
		#self.actuatorAdapterMgr = None
		
		# NOTE: The following aren't used until Part III but should be declared now
		self.mqttClient         = None
		self.coapClient         = None
		self.coapServer         = None

		self.sysPerfDataListener = None
		self.telemetryDataListener = None
		self.actuatorResponseCache = {}
		self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener=self)

		self.enableRedisStore = self.configUtil.getBoolean(
			section=ConfigConst.CONSTRAINED_DEVICE,
			key="enablePersistenceClient"
		)

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
			self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener = self)
			logging.info("Local actuation capabilities enabled")

		if self.enableMqttClient:
			self.mqttClient = MqttClientConnector()
			self.mqttClient.setDataMessageListener(self)			

		if self.enableCoapServer:
			logging.info("Creating CoapServerAdapter now")
			self.coapServer = CoapServerAdapter(dataMsgListener=self)
		else:
			logging.info("CoAP server disabled")

		if self.enableCoapClient:
			self.coapClient = CoapClientConnector(dataMsgListener = self)	

		self.deviceID = \
			self.configUtil.getProperty(
				section = ConfigConst.CONSTRAINED_DEVICE,
				key = ConfigConst.DEVICE_LOCATION_ID_KEY,
				defaultVal = ConfigConst.NOT_SET
			)

		self.handleTempChangeOnDevice = \
			self.configUtil.getBoolean( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY)
			
		self.triggerHvacTempFloor     = \
			self.configUtil.getFloat( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY);
				
		self.triggerHvacTempCeiling   = \
			self.configUtil.getFloat( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY);

		self.handleHumidityChangeOnDevice = \
			self.configUtil.getBoolean(
				section = ConfigConst.CONSTRAINED_DEVICE,
				key = "handleHumidityChangeOnDevice")

		self.triggerHumidifierHumidityFloor = \
			self.configUtil.getFloat(
				section = ConfigConst.CONSTRAINED_DEVICE,
				key = "triggerHumidifierHumidityFloor")

		self.triggerHumidifierHumidityCeiling = \
			self.configUtil.getFloat(
				section = ConfigConst.CONSTRAINED_DEVICE,
				key = "triggerHumidifierHumidityCeiling")

		logging.info("DeviceDataManager init start")
		logging.info("enableCoapServer = %s", str(self.enableCoapServer))
		logging.info("enableMqttClient = %s", str(self.enableMqttClient))
		logging.info("enableSensing = %s", str(self.enableSensing))

	def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
		"""
		Retrieves the named actuator data (response) item from the internal data cache.
		
		@param name
		@return ActuatorData
		"""
		pass
		
	def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
		"""
		Retrieves the named sensor data item from the internal data cache.
		
		@param name
		@return SensorData
		"""
		pass
	
	def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
		"""
		Retrieves the named system performance data from the internal data cache.
		
		@param name
		@return SystemPerformanceData
		"""
		pass
	
	def handleActuatorCommandResponse(self, data: ActuatorData) -> bool:
		if data:
			actuatorMsg = DataUtil().actuatorDataToJson(data)
			logging.info("Incoming actuator response received (from actuator manager): " + actuatorMsg)

			self.actuatorResponseCache[data.getName()] = data

			self._handleUpstreamTransmission(
				resource = ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE,
				msg = actuatorMsg
			)

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

				logging.info("Parsed incoming ActuatorData: %s", ad)
				return self.handleActuatorCommandMessage(ad)

			logging.warning("Unhandled incoming resource: %s", resourceEnum)
			return False

		except Exception as e:
			logging.warning("Failed to handle incoming message. Message: %s", e)
			return False
	
	def handleSensorMessage(self, data: SensorData) -> bool:
		if data:
			logging.debug(
				"Incoming sensor data received (from sensor manager): %s value=%s",
				str(data),
				str(data.getValue())
			)

			if self.enableRedisStore and self.redisClient:
				try:
					self.redisClient.storeData(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, data)
				except Exception as e:
					logging.warning(f"Failed to store SensorData to Redis: {e}")

			self._handleSensorDataAnalysis(data = data)

			sensorMsg = DataUtil().sensorDataToJson(data = data)
			self._handleUpstreamTransmission(
				resource = ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
				msg = sensorMsg
			)

			return True
		else:
			logging.warning("Incoming sensor data is invalid (null). Ignoring.")
			return False

	def handleSystemPerformanceMessage(self, data: SystemPerformanceData) -> bool:

		if data:
			logging.debug("Incoming system performance message received (from sys perf manager): " + str(data))

			sysPerfMsg = DataUtil().systemPerformanceDataToJson(data = data)
			self._handleUpstreamTransmission(
				resource = ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
				msg = sysPerfMsg
			)

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

		if self.redisClient and self.enableRedisStore:
			self.redisClient.connectClient()

		if self.mqttClient:
			self.mqttClient.connectClient()
			self.mqttClient.subscribeToTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, callback = self.handleIncomingMessage, qos = ConfigConst.DEFAULT_QOS)
		
		if self.coapServer:
			self.coapServer.startServer()

		logging.info("Started DeviceDataManager.")
		
	def stopManager(self):
		logging.info("Stopping DeviceDataManager...")
		
		if self.sysPerfMgr:
			self.sysPerfMgr.stopManager()
		
		if self.sensorAdapterMgr:	
			self.sensorAdapterMgr.stopManager()

		if self.redisClient and self.enableRedisStore:
			self.redisClient.disconnectClient()

		if self.mqttClient:
			self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
			self.mqttClient.disconnectClient()

		if self.coapServer:
			self.coapServer.stopServer()

		logging.info("Stopped DeviceDataManager.")
		
	def _handleIncomingDataAnalysis(self, msg: str):
		"""
		Call this from handleIncomeMessage() to determine if there's
		any action to take on the message. Steps to take:
		1) Validate msg: Most will be ActuatorData, but you may pass other info as well.
		2) Convert msg: Use DataUtil to convert if appropriate.
		3) Act on msg: Determine what - if any - action is required, and execute.
		"""
		pass
		
	def _handleSensorDataAnalysis(self, data: SensorData):
		if self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.info("Handle temp change: %s - type ID: %s", str(self.handleTempChangeOnDevice), str(data.getTypeID()))
			
			ad = ActuatorData(typeID = ConfigConst.HVAC_ACTUATOR_TYPE)
			ad.setLocationID(self.configUtil.getProperty(
				section = ConfigConst.CONSTRAINED_DEVICE,
				key = ConfigConst.DEVICE_LOCATION_ID_KEY,
				defaultVal = ConfigConst.NOT_SET
			))
			
			if data.getValue() > self.triggerHvacTempCeiling:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempCeiling)
				ad.setStateData("HVAC ON")
			elif data.getValue() < self.triggerHvacTempFloor:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempFloor)
				ad.setStateData("HVAC ON")
			else:
				ad.setCommand(ConfigConst.COMMAND_OFF)
				ad.setStateData("HVAC OFF")
				
			self.handleActuatorCommandMessage(ad)

		if self.handleHumidityChangeOnDevice and data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE:
			ad = ActuatorData(typeID = ConfigConst.HUMIDIFIER_ACTUATOR_TYPE)
			ad.setLocationID(self.deviceID)

			if data.getValue() < self.triggerHumidifierHumidityFloor:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setStateData("HUMIDIFIER ON")

			elif data.getValue() > self.triggerHumidifierHumidityCeiling:
				ad.setCommand(ConfigConst.COMMAND_OFF)
				ad.setStateData("HUMIDIFIER OFF")

			else:
				return

			self.handleActuatorCommandMessage(ad)	

	def _handleUpstreamTransmission(self, resource = None, msg: str = None):
		logging.info("Upstream transmission invoked. Checking comm's integration.")
		
		if self.mqttClient:
			if self.mqttClient.publishMessage(resource = resource, msg = msg):
				logging.debug("Published incoming data to resource (MQTT): %s", str(resource))
			else:
				logging.warning("Failed to publish incoming data to resource (MQTT): %s", str(resource))


	def handleActuatorCommandMessage(self, data: ActuatorData) -> ActuatorData:
		if data:
			logging.info("Processing actuator command message.")
			
			# TODO: add further validation before sending the command
			return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Received invalid ActuatorData command message. Ignoring.")
			return None	