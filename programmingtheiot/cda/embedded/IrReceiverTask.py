import logging
import json
import os
import pigpio

class IrReceiverTask:
    IR_RECEIVER_GPIO = 18
    IR_CODES_FILE    = './config/ir_codes.json'

    def __init__(self):
        self.pi       = pigpio.pi()
        self.codes    = {}
        self.pulses   = []
        self.lastTick = 0
        self.inCode   = False

        if not self.pi.connected:
            logging.warning("pigpio daemon not connected. Run: sudo pigpiod")
            return

        if os.path.exists(self.IR_CODES_FILE):
            with open(self.IR_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
            logging.info("Loaded IR codes from %s", self.IR_CODES_FILE)

        self.pi.set_mode(self.IR_RECEIVER_GPIO, pigpio.INPUT)
        logging.info("IrReceiverTask initialized on GPIO %d", self.IR_RECEIVER_GPIO)

    def _pulseCallback(self, gpio, level, tick):
        if level != pigpio.TIMEOUT:
            pulse = tick - self.lastTick
            self.lastTick = tick

            if self.inCode:
                self.pulses.append(pulse)
                self.pi.set_watchdog(self.IR_RECEIVER_GPIO, 200)
        else:
            self.pi.set_watchdog(self.IR_RECEIVER_GPIO, 0)
            self.inCode = False
            logging.info("IR signal received: %d pulses", len(self.pulses))

    def record(self, codeName: str):
        if not self.pi.connected:
            logging.warning("pigpio not connected.")
            return False

        logging.info("Recording IR code '%s' - press remote button now...", codeName)

        self.pulses   = []
        self.inCode   = True
        self.lastTick = self.pi.get_current_tick()

        cb = self.pi.callback(self.IR_RECEIVER_GPIO, pigpio.EITHER_EDGE, self._pulseCallback)

        import time
        timeout = 5.0
        start   = time.time()
        while self.inCode and (time.time() - start) < timeout:
            time.sleep(0.1)

        cb.cancel()

        if self.pulses:
            self.codes[codeName] = self.pulses
            self._saveCodes()
            logging.info("Saved IR code '%s' (%d pulses)", codeName, len(self.pulses))
            return True
        else:
            logging.warning("No IR signal detected for '%s'", codeName)
            return False

    def _saveCodes(self):
        os.makedirs(os.path.dirname(self.IR_CODES_FILE), exist_ok=True)
        with open(self.IR_CODES_FILE, 'w') as f:
            json.dump(self.codes, f, indent=2)
        logging.info("IR codes saved to %s", self.IR_CODES_FILE)

    def getCodes(self) -> dict:
        return self.codes

    def cleanup(self):
        if self.pi.connected:
            self.pi.stop()