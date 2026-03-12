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
import traceback

from threading import Thread
from time import sleep

from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.cda.connection.handlers.GetTelemetryResourceHandler import GetTelemetryResourceHandler
from programmingtheiot.cda.connection.handlers.UpdateActuatorResourceHandler import UpdateActuatorResourceHandler
from programmingtheiot.cda.connection.handlers.GetSystemPerformanceResourceHandler import GetSystemPerformanceResourceHandler

class CoapServerAdapter():
	"""
	Definition for a CoAP communications server, with embedded test functions.
	
	"""
	
	def __init__(self, dataMsgListener = None):
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		
		self.host = self.config.getProperty(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		self.port = self.config.getInteger(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_COAP_PORT)
		self.serverUri = f"coap://{self.host}:{self.port}"

		self.coapServer     = None
		self.coapServerTask = None
		
		self.listenTimeout = 30
		
		logging.info("CoapServerAdapter init start")
		self._initServer()
		
		logging.info(f"CoAP server configured for host and port: {self.serverUri}")
		
	def addResource(self, resourcePath: ResourceNameEnum = None, endName: str = None, resource=None):
		if not resourcePath or not resource:
			if resourcePath:
				logging.warning("No resource provided for path: " + str(resourcePath.value))
			else:
				logging.warning("No resource path provided.")
			return None

		uriPath = resourcePath.value

		if endName:
			uriPath = uriPath + "/" + endName

		try:
			self.coapServer.add_resource(uriPath, resource)
			logging.info(f"Added CoAP resource: {uriPath}, resource.name={resource.name}")
			return resource
		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning("Failed to add CoAP resource for path: " + uriPath)
			return None

	def _initServer(self):
		try:
			self.coapServer = CoAP(server_address=(self.host, self.port))

			# System performance resource
			sysPerfHandler = GetSystemPerformanceResourceHandler(
				dataMsgListener=self.dataMsgListener
			)
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
				resource=sysPerfHandler
			)

			# Telemetry resource
			telemetryHandler = GetTelemetryResourceHandler(
				dataMsgListener=self.dataMsgListener
			)
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
				resource=telemetryHandler
			)

			# Actuator resources
			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.HUMIDIFIER_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.HUMIDIFIER_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener
				)
			)

			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.HVAC_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.HVAC_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener
				)
			)

			self.addResource(
				resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				endName=ConfigConst.LED_ACTUATOR_NAME,
				resource=UpdateActuatorResourceHandler(
					name=ConfigConst.LED_ACTUATOR_NAME,
					dataMsgListener=self.dataMsgListener
				)
			)

			logging.info("Created CoAP server with default resources.")

		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning("Failed to create CoAP server.")

	def startServer(self):
		if self.coapServer:
			logging.info("Starting CoAP server...")
			
			if self.coapServerTask and self.coapServerTask.isAlive():
				self.stopServer()
				self.coapServerTask= None
				
			self.coapServerTask = Thread(target = self._runServer)
			self.coapServerTask.setDaemon(True)
			self.coapServerTask.start()
			
			logging.info("\n\n***** CoAP server started. *****\n\n")
		else:
			logging.warning("CoAP server not yet initialized (shouldn't happen).")

	def stopServer(self):
		if self.coapServer:
			logging.info("Stopping CoAP server...")
			
			self.coapServer.close()
			self.coapServerTask.join(5)
		else:
			logging.warning("CoAP server not yet initialized (shouldn't happen).")

	def _runServer(self):
		try:
			self.coapServer.listen(self.listenTimeout)

		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning("Failed to run server.")
	
	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		
		return False
