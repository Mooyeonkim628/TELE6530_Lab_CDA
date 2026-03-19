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
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData

class UpdateActuatorResourceHandler(Resource):
	def __init__(
		self,
		name: str = ConfigConst.ACTUATOR_CMD,
		coap_server=None,
		dataMsgListener: IDataMessageListener = None
	):
		super(UpdateActuatorResourceHandler, self).__init__(
			name,
			coap_server,
			visible=True,
			observable=True,
			allow_children=True
		)

		self.dataMsgListener = dataMsgListener
		self.dataUtil = DataUtil()
		self.actuatorData = ActuatorData()

		self.payload = "UpdateActuatorData"

	def render_GET_advanced(self, request, response):
		if request:
			jsonData = self.dataUtil.actuatorDataToJson(self.actuatorData)
			logging.info("Latest ActuatorData JSON: " + jsonData)

			response.code = defines.Codes.CONTENT.number
			response.payload = (defines.Content_types["application/json"], jsonData)

		return self, response

	def render_PUT_advanced(self, request, response):
		if request:
			try:
				jsonData = request.payload
				if isinstance(jsonData, bytes):
					jsonData = jsonData.decode()

				self.actuatorData = self.dataUtil.jsonToActuatorData(jsonData)

				if self.dataMsgListener:
					self.dataMsgListener.handleActuatorCommandMessage(self.actuatorData)

				response.code = defines.Codes.CHANGED.number
			except Exception as e:
				logging.warning("Failed to process actuator PUT: %s", str(e))
				response.code = defines.Codes.BAD_REQUEST.number

		return self, response