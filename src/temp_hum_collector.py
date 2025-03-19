from dotenv import load_dotenv
import logging
from cysystemd.journal import JournaldLogHandler
import os
import asyncio
from bleak import BleakScanner
import struct
from database import log_data
from datetime import datetime
from switchbot_api import SwitchBotAPI
import json

# .envファイルの読み込み
load_dotenv(".env")
SENSOR_ADDRESS = os.getenv("SENSOR_ADDRESS")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 60))
SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT", 5))

TARGET_UUID = "0000181a-0000-1000-8000-00805f9b34fb"

logger = logging.getLogger("SensorService")
logger.setLevel(logging.INFO)
logger.addHandler(JournaldLogHandler())

switchbot_api = SwitchBotAPI()
CONFIG_FILE = "config.json"

# 受信したBytes型データの解析
def parse_data(data: bytes):
    # uint8_t     MAC[6]; // [0] - lo, .. [6] - hi digits
    # int16_t     temperature;    // x 0.01 degree
    # uint16_t    humidity;       // x 0.01 %
    # uint16_t    battery_mv;     // mV
    # uint8_t     battery_level;  // 0..100 %
    # uint8_t     counter;        // measurement count
    # uint8_t     flags;  // GPIO_TRG pin (marking "reset" on circuit board) flags: 
    #                     // bit0: Reed Switch, input
    #                     // bit1: GPIO_TRG pin output value (pull Up/Down)
    #                     // bit2: Output GPIO_TRG pin is controlled according to the set parameters
    #                     // bit3: Temperature trigger event
    #                     // bit4: Humidity trigger event
    mac_addr = ":".join(f"{b:02X}" for b in reversed(data[:6]))
    temp, hum, _, batt_level = struct.unpack_from('<hhHB', data, 6)
    return {
        "date": f"[{datetime.now().astimezone().isoformat(sep=' ', timespec='milliseconds')}]",
        "mac_addr": mac_addr,
        "temp": temp / 100,
        "hum": hum / 100,
        "batt": batt_level
    }
    
def control_heater(current_temp):
    default_threshold = 25.0
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            threshold = config.get("threshold_temperature", default_threshold)
    except FileNotFoundError:
        threshold = default_threshold
        # ファイルが存在しない場合はデフォルト設定で生成
        with open(CONFIG_FILE, "w") as f:
            json.dump({"threshold_temperature": threshold}, f, indent=4)
    
    if current_temp < threshold - 0.25:
        switchbot_api.turn_on()  # ON
    elif current_temp > threshold + 0.25:
        switchbot_api.turn_off()  # OFF

async def scan_and_log():
    while True:
        async def detection_callback(device, advertisement_data):
            if device.address == SENSOR_ADDRESS:
                data = advertisement_data.service_data[TARGET_UUID]
                try:
                    parsed = parse_data(data)
                    log_data(parsed['mac_addr'], parsed['temp'], 
                        parsed['hum'], parsed['batt'])
                    # print(f"Logged: {parsed}")
                    logger.info(f"Logged: {parsed}")
                    control_heater(parsed['temp'])
                except Exception as e:
                    # print(f"Error: {str(e)}")
                    logger.error(f"Error: {str(e)}", exc_info=True)
                found_event.set()

        scanner = BleakScanner(detection_callback)
        found_event = asyncio.Event()
        
        try:
            await scanner.start()
            await asyncio.wait_for(found_event.wait(), timeout=SCAN_TIMEOUT)
        except asyncio.TimeoutError:
            # print("Timeout: No target devices found.")
            logger.error("Timeout: No target devices found.", exc_info=False)
        await scanner.stop()
        await asyncio.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    asyncio.run(scan_and_log())
