import requests
import json
import time
import hashlib
import hmac
import base64
import uuid
import os
from dotenv import load_dotenv

# 環境変数のロード（.env ファイルに TOKEN, SECRET, DEVICE_ID 等を定義しておく）
load_dotenv()

class SwitchBotAPI:
    BASE_URL = "https://api.switch-bot.com/v1.1"

    def __init__(self, token=None, secret=None, device_id=None):
        # API キー・シークレット・デバイスIDは引数または環境変数から取得
        self.token = token or os.getenv('SWITCHBOT_TOKEN')
        self.secret = secret or os.getenv('SWITCHBOT_SECRET')
        self.device_id = device_id or os.getenv('SWITCHBOT_SMART_PLUG_DEVICE_ID')
        # secret はバイト列に変換して保持
        if isinstance(self.secret, str):
            self.secret = self.secret.encode('utf-8')

    def _generate_headers(self):
        """
        認証ヘッダーを生成する内部メソッド
        """
        t = int(round(time.time() * 1000))  # 13 桁のタイムスタンプ
        nonce = uuid.uuid4()                # 毎回新規の UUID
        # 署名用の文字列を作成
        string_to_sign = '{}{}{}'.format(self.token, t, nonce)
        string_to_sign = string_to_sign.encode('utf-8')
        # HMAC-SHA256 で署名生成、Base64 エンコード
        sign = base64.b64encode(hmac.new(self.secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            'charset': 'utf8',
            't': str(t),
            'sign': sign.decode('utf-8'),
            'nonce': str(nonce)
        }
        return headers

    def get_devices(self):
        """
        登録されている全デバイスの一覧を取得
        """
        url = f"{self.BASE_URL}/devices"
        headers = self._generate_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error in get_devices:", response.status_code, response.text)
            return None

    def get_status(self, device_id=None):
        """
        指定のデバイスの状態を取得する
        """
        device_id = device_id or self.device_id
        url = f"{self.BASE_URL}/devices/{device_id}/status"
        headers = self._generate_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error in get_status:", response.status_code, response.text)
            return None

    def send_command(self, device_id, command, parameter="default", command_type="command"):
        """
        指定のデバイスに対してコマンドを送信する
        """
        url = f"{self.BASE_URL}/devices/{device_id}/commands"
        headers = self._generate_headers()
        data = {
            "command": command,
            "parameter": parameter,
            "commandType": command_type
        }
        response = requests.post(url, headers=headers, json=data)
        try:
            return response.json()
        except Exception as e:
            print("Error parsing response:", e)
            return None

    def turn_on(self, device_id=None):
        """
        指定のデバイスを ON にする
        """
        device_id = device_id or self.device_id
        return self.send_command(device_id, "turnOn")

    def turn_off(self, device_id=None):
        """
        指定のデバイスを OFF にする
        """
        device_id = device_id or self.device_id
        return self.send_command(device_id, "turnOff")


# --- 利用例 ---
if __name__ == "__main__":
    # クラスインスタンスの生成（環境変数から認証情報を読み込み）
    api = SwitchBotAPI()
    
    # ① デバイス一覧の取得
    devices = api.get_devices()
    if devices:
        print("Devices:")
        print(json.dumps(devices, indent=4, ensure_ascii=False))
    
    # ② 指定デバイスのステータス確認
    status = api.get_status()
    if status:
        print("Device Status:")
        print(json.dumps(status, indent=4, ensure_ascii=False))
    
    # ③ デバイスを ON にする（例）
    result_on = api.turn_on()
    print("Turn On Result:")
    print(json.dumps(result_on, indent=4, ensure_ascii=False))
    
    # ④ デバイスを OFF にする（例）
    result_off = api.turn_off()
    print("Turn Off Result:")
    print(json.dumps(result_off, indent=4, ensure_ascii=False))
