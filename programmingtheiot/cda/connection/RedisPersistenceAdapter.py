import redis
import json
import logging

from programmingtheiot.common.ConfigUtil import ConfigUtil
import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum


class RedisPersistenceAdapter:
    _Logger = logging.getLogger(__name__)
    DATA_GATEWAY_SERVICE = "Data.GatewayService"

    def __init__(self):
        self.host = None
        self.port = None
        self.redisClient = None
        self.connected = False

        self._configUtil = ConfigUtil()
        self._initConfig()
        self._initClient()

    def _initConfig(self):
        try:
            hostKey = getattr(ConfigConst, "HOST_KEY", "host")
            portKey = getattr(ConfigConst, "PORT_KEY", "port")
            defaultHost = getattr(ConfigConst, "DEFAULT_HOST", "localhost")
            defaultPort = getattr(ConfigConst, "DEFAULT_PORT", 6379)

            self.host = self._configUtil.getProperty(self.DATA_GATEWAY_SERVICE, hostKey, defaultHost)
            portStr = self._configUtil.getProperty(self.DATA_GATEWAY_SERVICE, portKey, str(defaultPort))
            self.port = int(portStr)

            self._Logger.info(f"Redis config loaded. host={self.host}, port={self.port}")

        except Exception as e:
            self._Logger.error(f"Failed to load Redis config: {e}")
            self.host = "localhost"
            self.port = 6379

    def _initClient(self):
        try:
            self.redisClient = redis.Redis(host=self.host, port=self.port, decode_responses=True)
            self._Logger.info("Redis client initialized.")
        except Exception as e:
            self._Logger.error(f"Failed to initialize Redis client: {e}")

    def connectClient(self) -> bool:
        if self.connected:
            self._Logger.warning("Redis client is already connected.")
            return True
        try:
            if self.redisClient and self.redisClient.ping():
                self.connected = True
                self._Logger.info("Connected to Redis.")
                return True
            self._Logger.error("Redis ping failed.")
            return False
        except Exception as e:
            self._Logger.error(f"Failed to connect to Redis: {e}")
            return False

    def disconnectClient(self) -> bool:
        if not self.connected:
            self._Logger.warning("Redis client is already disconnected.")
            return True

        try:
            if self.redisClient:
                self.redisClient.close()
            self.connected = False
            self._Logger.info("Disconnected from Redis.")
            return True
        except Exception as e:
            self._Logger.error(f"Failed to disconnect from Redis: {e}")
            return False

    def storeData(self, resource: ResourceNameEnum, data) -> bool:
        if not self.connected:
            self._Logger.warning("Redis client not connected. Call connectClient() first.")
            return False

        if not resource or data is None:
            self._Logger.warning("Invalid resource or data.")
            return False

        try:
            topic = resource.value if hasattr(resource, "value") else str(resource)

            if hasattr(data, "__dict__"):
                payload = json.dumps(data.__dict__, default=str)
            else:
                payload = json.dumps({"data": str(data)})

            subs = self.redisClient.publish(topic, payload)
            if subs == 0:
                self._Logger.debug("Publish succeeded but no subscribers were listening.")

            return True

        except Exception as e:
            self._Logger.error(f"Failed to store data in Redis: {e}")
            return False
