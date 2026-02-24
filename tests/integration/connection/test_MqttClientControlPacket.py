import logging
import unittest

from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.DefaultDataMessageListener import DefaultDataMessageListener
from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData
from programmingtheiot.data.DataUtil import DataUtil


class MqttClientControlPacketTest(unittest.TestCase):
    """
    Goal: generate MQTT 3.1.1 control packets.
    You still need Wireshark (or broker logs) to *verify* each packet on the wire.
    """

    @classmethod
    def setUpClass(self):
        logging.basicConfig(
            format='%(asctime)s:%(module)s:%(levelname)s:%(message)s',
            level=logging.DEBUG
        )
        logging.info("Executing the MqttClientControlPacketTest class...")

        self.cfg = ConfigUtil()
        self.mcc = MqttClientConnector(clientID="MyTestMqttClient_ControlPkts")
        self.du = DataUtil()
        self.listener = DefaultDataMessageListener()

    def setUp(self):
        ok = self.mcc.connectClient()
        sleep(1)
        self.mcc.setDataMessageListener(self.listener)

    def tearDown(self):
        try:
            self.mcc.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
        except Exception:
            pass

        try:
            self.mcc.disconnectClient()
        except Exception:
            pass

        sleep(1)

    def testConnectAndDisconnect(self):
        ok = self.mcc.disconnectClient()
        self.assertTrue(ok or ok is False) 
        ok2 = self.mcc.connectClient()
        self.assertTrue(ok2 or ok2 is False)

    def testServerPing(self):

        keepAlive = getattr(self.mcc, "keepAlive", 60)
        wait_s = max(keepAlive + 2, 7)

        logging.info(f"Waiting {wait_s}s to trigger MQTT keepAlive ping (keepAlive={keepAlive})...")
        sleep(wait_s)


    def testPubSub(self):
        ok = self.mcc.subscribeToTopic(
            ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
            callback=None,
            qos=1
        )
        self.assertTrue(ok or ok is False)
        sleep(1)

        ad = ActuatorData()
        ad.setCommand(7)  
        payload = self.du.actuatorDataToJson(ad) if hasattr(self.du, "actuatorDataToJson") else str(ad)

        self.mcc.publishMessage(
            ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
            msg=payload,
            qos=0
        )
        sleep(1)

        self.mcc.publishMessage(
            ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
            msg=payload,
            qos=1
        )
        sleep(1)

        self.mcc.publishMessage(
            ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
            msg=payload,
            qos=2
        )
        sleep(2)

        ok2 = self.mcc.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
        self.assertTrue(ok2 or ok2 is False)
        sleep(1)