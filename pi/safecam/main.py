"""Vòng lặp chính: camera -> YOLO -> 4 KHU -> trạng thái -> MQTT."""
from pathlib import Path

from .camera import Camera
from .config import load_config
from .detector import PersonDetector
from .intrusion import Intrusion
from .mqtt_client import MqttClient
from .outputs import OBS_OK
from .persistence import intrusion_from_dict, load_state
from .zones import ZoneMonitor

ROOT = Path(__file__).resolve().parents[2] #goc repo
STATE_PATH = ROOT / "data" / "state.json" #data / khong len git

class FakeObservation:
    """Đóng thể cho observation.py: luôn coi camera nhìn tốt.
     Có observation.py thật thì xóa calss này, chỉ đổi một dòng trong main(),"""
    state = OBS_OK
    event_id = None

    def update(self, now, *args):
        return False
    def ack(self, ids):
        return False

def main():
    cam_cfg = load_config("camera")
    det_cfg = load_config("detection")
    zone_cfg = load_config("zones")
    mqtt_cfg = load_config("mqtt")

    # Kiểm tra cấu hình khu trước: sai thì dừng ngay, không phải chờ nạp mô hình
    zones = ZoneMonitor.from_config(zone_cfg, det_cfg)

    #Khôi phục sự kiện chưa xác nhận (K7); chưa có file hoặc file hỏng thì bắt đầu mới
    saved = load_state(STATE_PATH)
    intr = intrusion_from_dict(saved) if saved else Intrusion()
    obs = FakeObservation() #tam thoi 
    detector = PersonDetector(str(ROOT / det_cfg["model"]), det_cfg["imgsz"], det_cfg["conf"])
    camera = Camera(cam_cfg)
    mqtt = MqttClient(mqtt_cfg)
    camera.start()
    mqtt.start()
    print("Sẵn sàng, Trạng thái xâm nhập: ", intr.state)

if __name__ == "__main__":
    main()
    