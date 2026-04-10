import logging
import json
import os
import pigpio

class IrTransmitterTask:
    IR_TRANSMITTER_GPIO = 17         # IR LED 연결 핀 (필요시 변경)
    IR_CODES_FILE       = './config/ir_codes.json'
    IR_FREQUENCY        = 38000      # 다이킨 표준 38kHz 캐리어

    def __init__(self):
        self.pi    = pigpio.pi()
        self.codes = {}

        if not self.pi.connected:
            logging.warning("pigpio daemon not connected. Run: sudo systemctl start pigpiod")
            return

        # 저장된 IR 코드 로드
        if os.path.exists(self.IR_CODES_FILE):
            with open(self.IR_CODES_FILE, 'r') as f:
                self.codes = json.load(f)
            logging.info("Loaded IR codes: %s", list(self.codes.keys()))
        else:
            logging.warning("No IR codes file found at %s. Record codes first.", self.IR_CODES_FILE)

        self.pi.set_mode(self.IR_TRANSMITTER_GPIO, pigpio.OUTPUT)
        logging.info("IrTransmitterTask initialized on GPIO %d", self.IR_TRANSMITTER_GPIO)

    def send(self, codeName: str) -> bool:
        """
        codeName: 전송할 코드 이름 (예: 'hvac_on', 'hvac_off')
        """
        if not self.pi.connected:
            logging.warning("pigpio not connected.")
            return False

        if codeName not in self.codes:
            logging.warning("IR code '%s' not found. Available: %s", codeName, list(self.codes.keys()))
            return False

        pulses     = self.codes[codeName]
        pigpioPulses = []
        on          = True  # 첫 펄스는 ON

        for duration in pulses:
            if on:
                # 38kHz 캐리어로 ON 펄스 생성
                pigpioPulses.append(pigpio.pulse(1 << self.IR_TRANSMITTER_GPIO, 0, duration))
            else:
                # OFF 펄스 (아무것도 안 보냄)
                pigpioPulses.append(pigpio.pulse(0, 1 << self.IR_TRANSMITTER_GPIO, duration))
            on = not on

        self.pi.wave_clear()
        self.pi.wave_add_generic(pigpioPulses)
        waveID = self.pi.wave_create()

        if waveID >= 0:
            self.pi.wave_send_once(waveID)
            while self.pi.wave_tx_busy():
                import time
                time.sleep(0.001)
            self.pi.wave_delete(waveID)
            logging.info("IR code '%s' sent successfully.", codeName)
            return True
        else:
            logging.warning("Failed to create IR wave for '%s'.", codeName)
            return False

    def cleanup(self):
        if self.pi.connected:
            self.pi.wave_clear()
            self.pi.stop()