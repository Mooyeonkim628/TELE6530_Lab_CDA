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
import paho.mqtt.client as mqttClient
import ssl

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

class MqttClientConnector(IPubSubClient):
	"""
	Shell representation of class for student implementation.
	
	"""

	def __init__(self, clientID: str = None):
		"""
		Default constructor. This will set remote broker information and client connection
		information based on the default configuration file contents.
		
		@param clientID Defaults to None. Can be set by caller. If this is used, it's
		critically important that a unique, non-conflicting name be used so to avoid
		causing the MQTT broker to disconnect any client using the same name. With
		auto-reconnect enabled, this can cause a race condition where each client with
		the same clientID continuously attempts to re-connect, causing the broker to
		disconnect the previous instance.
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = None
			
		self.host = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)

		self.port = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_MQTT_PORT)

		self.securePort = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.SECURE_PORT_KEY, 8883)

		self.keepAlive = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.KEEP_ALIVE_KEY, ConfigConst.DEFAULT_KEEP_ALIVE)

		self.defaultQos = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.DEFAULT_QOS_KEY, ConfigConst.DEFAULT_QOS)

		self.enableCrypt = \
			self.config.getBoolean( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.ENABLE_CRYPT_KEY, False)

		self.certFile = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.CERT_FILE_KEY, None)

		self.enableEncryption = \
			self.config.getBoolean( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.ENABLE_CRYPT_KEY)

		self.pemFileName = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.CERT_FILE_KEY)

		self.mqttClient = None
				
		if not clientID:
			self.clientID = \
				self.config.getProperty( \
					ConfigConst.CONSTRAINED_DEVICE, ConfigConst.DEVICE_LOCATION_ID_KEY, 'CDA_Mooyeon_Kim')
		else:
			self.clientID = clientID
				
		logging.info('\tMQTT Client ID:   ' + self.clientID)
		logging.info('\tMQTT Broker Host: ' + self.host)
		logging.info('\tMQTT Broker Port: ' + str(self.port))
		logging.info('\tMQTT Keep Alive:  ' + str(self.keepAlive))

	def connectClient(self) -> bool:
		if not self.mqttClient:
			self.mqttClient = mqttClient.Client(client_id = self.clientID, clean_session = True)
			
			try:
				if self.enableCrypt:
					logging.info("Enabling TLS encryption...")

					self.mqttClient.tls_set(
						ca_certs=self.certFile,
						tls_version=ssl.PROTOCOL_TLS_CLIENT
					)

			except Exception as e:
				logging.warning("Failed to enable TLS encryption. Using unencrypted connection. Error: %s", e)

			self.mqttClient.on_connect = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message = self.onMessage
			self.mqttClient.on_publish = self.onPublish
			self.mqttClient.on_subscribe = self.onSubscribe

		if not self.mqttClient.is_connected():
			connPort = self.securePort if self.enableCrypt else self.port

			logging.info(
				'MQTT client connecting to broker at host: ' + self.host +
				', port: ' + str(connPort) +
				', tls: ' + str(self.enableCrypt)
			)

			self.mqttClient.connect(self.host, connPort, self.keepAlive)
			self.mqttClient.loop_start()
			
			import time
			for _ in range(20):   
				if self.mqttClient.is_connected():
					return True
				time.sleep(0.1)

			return True
		else:
			logging.warning('MQTT client is already connected. Ignoring connect request.')
			
			return False
		
	def disconnectClient(self) -> bool:
		if self.mqttClient.is_connected():
			logging.info('Disconnecting MQTT client from broker: ' + self.host)
			self.mqttClient.loop_stop()
			self.mqttClient.disconnect()
			
			logging.warning("MQTT client connect timeout.")
			return False
		else:
			logging.warning('MQTT client already disconnected. Ignoring.')
			
			return False
		
	def onConnect(self, client, userdata, flags, rc):
		logging.info('[Callback] Connected to MQTT broker. Result code: ' + str(rc))
		
		# NOTE: Be sure to set `self.defaultQos` during instantiation!
		self.mqttClient.subscribe( \
			topic = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value, qos = self.defaultQos)
		
		self.mqttClient.message_callback_add( \
			sub = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value, \
			callback = self.onActuatorCommandMessage)
		
	def onDisconnect(self, client, userdata, rc):
		logging.info('MQTT client disconnected from broker: ' + str(client))
		
	def onMessage(self, client, userdata, msg):
		payload = msg.payload
		
		if payload:
			logging.info('MQTT message received with payload: ' + str(payload.decode("utf-8")))
		else:
			logging.info('MQTT message received with no payload: ' + str(msg))
			
	def onPublish(self, client, userdata, mid):
		#logging.info('MQTT message published: ' + str(client))
		pass
	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info('MQTT client subscribed: ' + str(client))	
	
	def onActuatorCommandMessage(self, client, userdata, msg):
		logging.info('[Callback] Actuator command message received. Topic: %s.', msg.topic)
		if self.dataMsgListener:
			try:
				self.dataMsgListener.handleIncomingMessage(
					ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
					msg.payload.decode('utf-8'))
			except:
				logging.exception("Failed to convert incoming actuation command payload to ActuatorData: ")

	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		"""
		"""
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot publish message.')
			return False
		
		# check validity of message
		if not msg:
			logging.warning('No message specified. Cannot publish message to topic: ' + resource.value)
			return False
					
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
		
		# publish message, and wait for publish to complete before returning
		msgInfo = self.mqttClient.publish(topic = resource.value, payload = msg, qos = qos)
		
		# The next SLOC is commented out now - recall it was added in Lab Module 06
		#msgInfo.wait_for_publish()
		
		# NOTE: The 'True' return no longer guarantees successful publish,
		# as it will return before the publish may successfully complete
		return True
	
	def subscribeToTopic(self, resource: ResourceNameEnum = None, callback = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		if not resource:
			logging.warning('No topic specified. Cannot subscribe.')
			return False
		
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
		
		logging.info('Subscribing to topic %s', resource.value)
		self.mqttClient.subscribe(resource.value, qos)
		
		return True
	
	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None):
		if not resource:
			logging.warning('No topic specified. Cannot unsubscribe.')
			return False
		
		logging.info('Unsubscribing to topic %s', resource.value)
		self.mqttClient.unsubscribe(resource.value)
		
		return True

	def setDataMessageListener(self, listener: IDataMessageListener = None):
		if listener:
			self.dataMsgListener = listener