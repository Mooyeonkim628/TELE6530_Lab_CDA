import logging
import unittest
import time

from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil

from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.cda.connection.RedisPersistenceAdapter import RedisPersistenceAdapter


class RedisClientAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            format="%(asctime)s:%(module)s:%(levelname)s:%(message)s",
            level=logging.INFO
        )
        logging.info("Testing RedisPersistenceAdapter class...")

        cfg = ConfigUtil()
        cls.redisHost = cfg.getProperty("Data.GatewayService", "host", "localhost")
        cls.redisPort = int(cfg.getProperty("Data.GatewayService", "port", "6379"))

        logging.info(f"Redis config: host={cls.redisHost}, port={cls.redisPort}")

        cls.redisAdapter = RedisPersistenceAdapter()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.redisAdapter.disconnectClient()
        except Exception:
            pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testConnectClient(self):
        ok1 = self.redisAdapter.connectClient()
        self.assertTrue(ok1, "connectClient() should return True")
        ok2 = self.redisAdapter.connectClient()
        self.assertTrue(ok2, "connectClient() should be idempotent")

    def testDisconnectClient(self):
        self.assertTrue(self.redisAdapter.connectClient(), "connectClient() should succeed before disconnect")

        ok1 = self.redisAdapter.disconnectClient()
        self.assertTrue(ok1, "disconnectClient() should return True")
        ok2 = self.redisAdapter.disconnectClient()
        self.assertTrue(ok2, "disconnectClient() should be idempotent")

    def testStoreSensorData(self):
        self.assertTrue(self.redisAdapter.connectClient(), "connectClient() should succeed before storeData")

        d = SensorData()
        if hasattr(d, "setName"):
            d.setName("RedisClientAdapterTest")
        if hasattr(d, "setValue"):
            d.setValue(25.5)
        elif hasattr(d, "value"):
            d.value = 25.5

        if hasattr(d, "timeStamp"):
            try:
                d.timeStamp = time.time()
            except Exception:
                pass

        ok = self.redisAdapter.storeData(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, d)
        self.assertTrue(ok, "storeData() should return True when publish succeeds")

        self.assertTrue(self.redisAdapter.disconnectClient(), "disconnectClient() should succeed after storeData")


if __name__ == "__main__":
    unittest.main()
