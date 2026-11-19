"""Kết nối MQTT của Pi: gửi state/event/hb, nhận ACK từ ESP32.
Định dạng bản tin: docs/mqtt.md. Mật khẩu đọc từ file .env"""

import json 
import os
import queue
import threading
from pathlib import Path 

import paho.mqtt.client as mqtt
from dotenv import load_dotenv 

ROOT = Path(__file__).resolve().parents[2] #thư mục gốc repo, nơi có file .env

def parse_ack(payload):
    """b'{"ids":["I3","O1"]}' -> {"I3", "O1"}. Sai định dạng -> None."""
    try:
        data = json.loads(payload)
    except ValueError:  # JSON hỏng hoặc không phải UTF-8
        return None
    ids = data.get("ids") if isinstance(data, dict) else None
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        return None
    return set(ids)

class MqttClient:
    def __init__(self, cfg):
        load_dotenv(ROOT / ".env") # Không ghi đè biến systemd đã nạp sẵn
        password = os.environ.get("SAFECAM_MQTT_PASS")
        if not password:
            print(" Cảnh báo: chưa có SAFECAM_MQTT_PASS trong .env, broker sẽ từ chối")
        self.cfg = cfg
        self.topics = cfg["topics"]
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cfg["client_id"])
        self.client.username_pw_set(cfg["username"], password)
        #Di chúc: Pi rớt mạng đột ngột thì broker tự báo "offline" thay 
        self.client.will_set(self.topics["status"], "offline", qos=1, retain=True)
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self._state_seq = 0
        self._hb_seq = 0
        self._last_state = None # bản state vừa gửi, gửi lại mỗi lần kết nối lại
        self._disconnected = threading.Event() # Cờ: đã ngắt kết nối xong
        self._acks = queue.Queue() # Luồng Paho bỏ vào, luồng chính lấy ra
        self.client.on_message = self._on_message

    def start(self):
        """ Bắt đầu kết nối ở luồng nền: broker chưa chạy thì tự thử lại, không làm dừng chương trình"""
        self.client.connect_async(self.cfg["host"], self.cfg["port"], self.cfg["keepalive"])
        self.client.loop_start()

    def stop(self):
        """ Tắt đàng hoàng: broker không gửi đi di chúc nên phải tự báo offline"""
        info = self.client.publish(self.topics["status"], "offline", qos=1, retain=True)
        info.wait_for_publish(timeout=2)
        self.client.disconnect()
        self._disconnected.wait(timeout=2) #Chờ gói DISCONNECT đi hết, broker không gửi di chúc
        self.client.loop_stop()

    def publish_state(self, state):
        """Gửi trnajg thái hiện tại (retain): ESP32 kết nối lại là nhận ngay"""
        self._state_seq += 1
        payload = {"seq": self._state_seq, **state}
        self._last_state = payload
        self._send(self.topics["state"], payload, qos=1, retain=True)

    def publish_event(self, event):
        """Gửi khi mở sự kiện mới. Không retain: sự kiện cũ không phát lại"""
        self._send(self.topics["event"], event, qos=1, retain=False)

    def publish_hb(self):
        """Một nhịp heartbeat. main.py gọi mỗi hb_interval_s giây từ vòng YOLO:
        vòng YOLO treo thì nhịp cũng ngừng, ESP32 biết ngay"""
        self._hb_seq += 1
        self._send(self.topics["hb"], {"seq": self._hb_seq}, qos=0, retain=False)

    def get_acks(self):
        """Gọi từ vòng lặp chính: Lấy hết mã ACK nhận được từ lần gọi lần trước (set, có thể rỗng)."""
        ids = set()
        while True:
            try:
                ids |= self._acks.get_nowait()
            except queue.Empty:
                return ids

    def _on_message(self, client, userdata, msg):
        # Chạy trên luồng paho: chỉ kiểm tra rồi bỏ vào hàng đợi, không đụng tới trạng thái
        ids = parse_ack(msg.payload)
        if ids is None:
            print(f"Bỏ qua ACK sai định dạng: {msg.payload[:50]!r}")
            return
        self._acks.put(ids)
    
    def _send(self, topic, data, qos, retain):
        self.client.publish(topic, json.dumps(data, separators=(",",":",)), qos=qos, retain=retain)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure: # không phải do stop(): mất mạng, broker tắt,...
            print(f"MQTT mất kết nối ({reason_code}), đang thử lại")
        self._disconnected.set()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # chạy trên luồng của paho, mỗi lần kết nối (kể cả kết nối lại)
        if reason_code.is_failure:
            print(f"MQTT từ chối kết nối: {reason_code}")
            return
        print("MQTT đã kết nối")
        self._disconnected.clear()
        client.publish(self.topics["status"], "online", qos=1, retain=True)
        client.subscribe(self.topics["ack"], qos=1) # đăng ký lại mỗi lần kết nối lại
        if self._last_state is not None: # broker có thể đã mất bản retain
            self._send(self.topics["state"], self._last_state, qos=1, retain=True)