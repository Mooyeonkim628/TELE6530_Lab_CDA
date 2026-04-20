import logging
import json
import os
import subprocess

class IrTransmitterTask:
    IR_TRANSMITTER_GPIO = 13
    IR_CODES_FILE       = './config/ir_codes.json'
    IR_FREQUENCY        = 38000

    def __init__(self):
        self.codes = {}
        if os.path.exists(self.IR_CODES_FILE):
            with open(self.IR_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
            logging.info("Loaded IR codes: %s", list(self.codes.keys()))
        else:
            logging.warning("No IR codes file found at %s", self.IR_CODES_FILE)
        logging.info("IrTransmitterTask initialized on GPIO %d", self.IR_TRANSMITTER_GPIO)

    def send(self, codeName: str) -> bool:
        if codeName not in self.codes:
            logging.warning("IR code '%s' not found.", codeName)
            return False
        script = f"""
import pigpio, time
pi = pigpio.pi()
pulses = {json.dumps(self.codes[codeName])}
for _ in range(10):
    on = True
    for duration in pulses:
        if on:
            pi.hardware_PWM(13, 38000, 400000)
            time.sleep(duration / 1000000.0)
            pi.hardware_PWM(13, 0, 0)
        else:
            time.sleep(duration / 1000000.0)
        on = not on
    pi.hardware_PWM(13, 0, 0)
    time.sleep(0.1)
pi.stop()
"""
        subprocess.run(['sudo', 'chrt', '-f', '99', 'python3', '-c', script])
        logging.info("IR code '%s' sent successfully.", codeName)
        return True

    def cleanup(self):
        pass