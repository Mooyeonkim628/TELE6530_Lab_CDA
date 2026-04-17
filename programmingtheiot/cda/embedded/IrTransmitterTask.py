import logging
import json
import os
import time
import pigpio

class IrTransmitterTask:
    IR_TRANSMITTER_GPIO = 12
    IR_CODES_FILE       = './config/ir_codes.json'
    IR_FREQUENCY        = 38000

    def __init__(self):
        self.pi    = pigpio.pi()
        self.codes = {}
        if not self.pi.connected:
            logging.warning("pigpio daemon not connected.")
            return
        if os.path.exists(self.IR_CODES_FILE):
            with open(self.IR_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
            logging.info("Loaded IR codes: %s", list(self.codes.keys()))
        else:
            logging.warning("No IR codes file found at %s", self.IR_CODES_FILE)
        logging.info("IrTransmitterTask initialized on GPIO %d", self.IR_TRANSMITTER_GPIO)

    def send(self, codeName: str) -> bool:
        if not self.pi.connected:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                logging.warning("pigpio not connected.")
                return False
        if codeName not in self.codes:
            logging.warning("IR code '%s' not found.", codeName)
            return False

        pulses = self.codes[codeName]
        on = True
        for duration in pulses:
            if on:
                self.pi.hardware_PWM(12, 38000, 400000)
                time.sleep(duration / 1000000.0)
                self.pi.hardware_PWM(12, 0, 0)
            else:
                time.sleep(duration / 1000000.0)
            on = not on
        self.pi.hardware_PWM(12, 0, 0)
        logging.info("IR code '%s' sent successfully.", codeName)
        return True

    def cleanup(self):
        if self.pi.connected:
            self.pi.hardware_PWM(self.IR_TRANSMITTER_GPIO, 0, 0)
            self.pi.stop()