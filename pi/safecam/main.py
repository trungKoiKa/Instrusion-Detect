"""Vòng lặp chính: camera -> YOLO -> 4 KHU -> trạng thái -> MQTT."""
from pathlib import Path
import sys
import time
from pathlib import Path
from .camera import Camera
from .config import load_config
from .detector import PersonDetector
from .intrusion import Intrusion
from .mqtt_client import MqttClient
from .outputs import OBS_OK, RecentAcks, build_state, intrusion_event_msg, split_ack_ids
from .persistence import intrusion_from_dict, intrusion_to_dict , load_state, save_state
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

    if sys.platform == "win32":
        cam_cfg["device"] = 1 # laptop: số camera thay cho đường dẫn của Pi

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

    recent = RecentAcks() # Các mã vừa ACK, gửi trong trường "acked"

    def send_state():
        mqtt.publish_state(build_state(intr, obs.state, obs.event_id, recent.as_list()))

    send_state() # ESP32 có trạng thái ngay, kể cả sự kiện vừa khôi phục (K7)
    print("Sẵn sàng, Trạng thái xâm nhập: ", intr.state)

    last_seq = 0
    try:
        while True:
            frame = camera.get_latest(last_seq) # chờ tối đa 2 giây
            mono = time.monotonic() # đồn hồ bấm giờ: cho cửa sổ T giây
            wall = time.time() # đồng hồ treo tường: cho giờ sự kiện
            if frame is not None:
                last_seq, img = frame
                zones.add_frame(mono, detector.detect(img))
                # không có ảnh: không ghi gì vào cửa sổ, vẫn xét tiếp (zones tự ra unkown)
                
                old_id = intr.event.id if intr.event else None
                if intr.update(wall, zones.verdicts(mono)):
                    save_state(STATE_PATH, intrusion_to_dict(intr)) #ghi sổ trước, gửi sau

                    if intr.event and intr.event.id != old_id: # vừa mở sự kiện mới
                        mqtt.publish_event(intrusion_event_msg(intr.event))
                    send_state()
                    zs = sorted(intr.event.zones) if intr.event else []
                    print("Xâm nhập:", intr.state, "khu", zs)

                acks = mqtt.get_acks() # mã ESP32 gửi từ lượt trước, có thể rỗng
                if acks:
                    recent.add(acks) # ghi cả mã cũ để ESP32 ngừng gửi lặp
                    intr_ids, obs_ids = split_ack_ids(acks)
                    if intr.ack(intr_ids):
                        save_state(STATE_PATH, intrusion_to_dict(intr))
                    obs.ack(obs_ids)
                    send_state() # luôn gửi, kể cả khi không có gì đổi
                    print("ACK:", sorted(acks),"->", intr.state)

    except KeyboardInterrupt:
        print("Đang tắt...")
    finally:
        camera.stop()
        mqtt.stop() 

if __name__ == "__main__":
    main()
    