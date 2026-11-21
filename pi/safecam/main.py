"""Vòng lặp chính: camera -> YOLO -> 4 khu -> trạng thái -> MQTT."""
import sys
import time
from pathlib import Path

from .camera import Camera
from .config import load_config
from .detector import PersonDetector
from .intrusion import Intrusion
from .mqtt_client import MqttClient
from .observation import OBS_LOST, OBS_OK, Observation, image_detail
from .outputs import (RecentAcks, build_state, intrusion_event_msg, observation_event_msg,
                      split_ack_ids)
from .persistence import intrusion_from_dict, intrusion_to_dict, load_state, save_state
from .zones import EMPTY, UNKNOWN, ZoneMonitor

ROOT = Path(__file__).resolve().parents[2]  # gốc repo
STATE_PATH = ROOT / "data" / "state.json"    # data/ không lên git


def main():
    cam_cfg = load_config("camera")
    det_cfg = load_config("detection")
    zone_cfg = load_config("zones")
    mqtt_cfg = load_config("mqtt")

    if sys.platform == "win32":
        cam_cfg["device"] = 1  # laptop: số camera thay cho đường dẫn của Pi

    mqtt_cfg = load_config("mqtt")
    obs_cfg = load_config("observation")

    # Kiểm tra cấu hình khu trước: sai thì dừng ngay, không phải chờ nạp mô hình
    zones = ZoneMonitor.from_config(zone_cfg, det_cfg)

    # Khôi phục sự kiện chưa xác nhận (K7); chưa có file hoặc file hỏng thì bắt đầu mới
    saved = load_state(STATE_PATH)
    intr = intrusion_from_dict(saved) if saved else Intrusion()
    obs = Observation.from_config(obs_cfg)  
    detector = PersonDetector(str(ROOT / det_cfg["model"]), det_cfg["imgsz"], det_cfg["conf"])
    camera = Camera(cam_cfg)
    mqtt = MqttClient(mqtt_cfg)
    camera.start()
    mqtt.start()

    recent = RecentAcks()  # các mã vừa ACK, gửi trong trường "acked"

    def send_state():
        mqtt.publish_state(build_state(intr, obs.state, obs.event_id, recent.as_list()))

    send_state()  # ESP32 có trạng thái ngay, kể cả sự kiện vừa khôi phục (K7)
    print("Sẵn sàng. Trạng thái xâm nhập:", intr.state)

    last_seq = 0
    last_hb = 0.0  # lượt đầu tiên gửi hb ngay
    hb_interval = mqtt_cfg["hb_interval_s"]

    try:
        while True:
            frame = camera.get_latest(last_seq)  # chờ tối đa 2 giây
            mono = time.monotonic()  # đồng hồ bấm giờ: cho cửa sổ T giây
            wall = time.time()       # đồng hồ treo tường: cho giờ sự kiện
            if mono - last_hb >= hb_interval:  # gõ từ vòng lặp chính: vòng treo thì hb dừng
                mqtt.publish_hb()
                last_hb = mono

            seen = False # Lượt này có ảnh nhìn được không
            if frame is not None:
                last_seq, img = frame
                # Ảnh bị che không vào cửa sổ khu, giống mất hình: không bao giờ coi là "vắng" (K1)
                if image_detail(img) >= obs_cfg["detail_min"]:
                    zones.add_frame(mono, detector.detect(img))
                    seen = True
                # không có ảnh hoặc bị che: không ghi gì vào cửa sổ, zones tự ra unknown

            verdicts = zones.verdicts(mono)
            # Nhìn được = có ảnh tốt và cửa sổ đủ ảnh (Pi quá chậm cũng là lỗi quan sát)
            good = seen and UNKNOWN not in verdicts.values()
            judged = verdicts
            if not obs.clear_for(mono, det_cfg["window_s"]):
                # Chưa nhìn tốt liên tục đủ T giây: chưa được kết luận "vắng" (K1)
                judged = {z: UNKNOWN if v == EMPTY else v for z, v in verdicts.items()}
            old_id = intr.event.id if intr.event else None
            if intr.update(wall, judged):
                save_state(STATE_PATH, intrusion_to_dict(intr)) # ghi sổ trước, gửi sau
                if intr.event and intr.event.id != old_id: # vừa mở sự kiện mới
                    blind = obs.state != OBS_OK  # vừa mất quan sát xong (K4)
                    mqtt.publish_event(intrusion_event_msg(intr.event, after_blind=blind))

                send_state()
                zs = sorted(intr.event.zones) if intr.event else []
                print("Xâm nhập:", intr.state, "khu", zs)

            if obs.update(mono, good):
                if obs.state == OBS_LOST: # vừa vào mất quan sát
                    mqtt.publish_event(observation_event_msg(obs.event_id))
                send_state()
                print("Quan sát:", obs.state, obs.event_id)
                

            acks = mqtt.get_acks()  # mã ESP32 gửi từ lượt trước, có thể rỗng
            if acks:
                recent.add(acks)  # ghi cả mã cũ để ESP32 ngừng gửi lặp
                intr_ids, obs_ids = split_ack_ids(acks)
                if intr.ack(intr_ids):
                    save_state(STATE_PATH, intrusion_to_dict(intr))
                obs.ack(obs_ids)
                send_state()  # luôn gửi, kể cả khi không có gì đổi
                print("ACK:", sorted(acks), "->", intr.state, obs.state)

    except KeyboardInterrupt:
        print("Đang tắt...")
    finally:
        camera.stop()
        mqtt.stop()


if __name__ == "__main__":
    main()
