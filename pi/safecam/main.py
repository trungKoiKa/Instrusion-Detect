"""Vòng lặp chính: camera -> YOLO -> 4 khu -> trạng thái -> MQTT."""
import sys
import time
from pathlib import Path

from .camera import Camera
from .config import load_config
from .detector import PersonDetector
from .mqtt_client import MqttClient
from .observation import OBS_LOST, OBS_LOST_ACKED, OBS_OK, image_detail
from .outputs import (RecentAcks, build_state, intr_code, intrusion_event_msg, obs_code,
                      observation_event_msg, split_ack_ids)
from .persistence import (intrusion_from_dict, intrusion_to_dict, load_state,
                          observation_from_dict, observation_to_dict, save_state)
from .zones import EMPTY, UNKNOWN, ZoneMonitor
from .stream import StreamServer

ROOT = Path(__file__).resolve().parents[2]  # gốc repo
STATE_PATH = ROOT / "data" / "state.json"    # data/ không lên git
FPS_EVERY_S = 30  # mỗi 30 giây in FPS một lần (đo tốc độ, xem Pi có chậm đi không)

def status_line(intr, obs):
    """Dòng chữ vẽ ở đáy luồng hình. Không dấu vì cv2.putText chỉ vẽ được ASCII."""
    text = f"XAM NHAP: {intr.state}"
    if intr.event:
        text += f" {intr_code(intr.event.id)} khu {sorted(intr.event.zones)}"
    text += f" / QUAN SAT: {obs.state}"
    if obs.event_id is not None:
        text += f" {obs_code(obs.event_id)}"
    return text


def main():
    cam_cfg = load_config("camera")
    det_cfg = load_config("detection")
    zone_cfg = load_config("zones")
    mqtt_cfg = load_config("mqtt")
    stream_cfg = load_config("stream")

    if sys.platform == "win32":
        cam_cfg["device"] = 1  # laptop: số camera thay cho đường dẫn của Pi

    mqtt_cfg = load_config("mqtt")
    obs_cfg = load_config("observation")

    # Kiểm tra cấu hình khu trước: sai thì dừng ngay, không phải chờ nạp mô hình
    zones = ZoneMonitor.from_config(zone_cfg, det_cfg)

    # Khôi phục sự kiện chưa xác nhận (K7); chưa có file hoặc file hỏng thì bắt đầu mới
    saved = load_state(STATE_PATH) or {}  # chưa có file hoặc file hỏng: dict rỗng, bắt đầu mới
    intr = intrusion_from_dict(saved.get("intr", {}))
    obs = observation_from_dict(saved.get("obs", {}), obs_cfg["lost_after_s"])  
    detector = PersonDetector(str(ROOT / det_cfg["model"]), det_cfg["imgsz"], det_cfg["conf"])
    camera = Camera(cam_cfg)
    mqtt = MqttClient(mqtt_cfg)
    camera.start()
    mqtt.start()

    stream = None
    if stream_cfg["enabled"]:
        stream = StreamServer(stream_cfg["port"], zone_cfg["boundaries"],
                              zone_cfg["forbidden"], stream_cfg["jpeg_quality"])
        if not stream.start():  # cổng bận: chạy tiếp không có stream
            stream = None

    def save():
        """Ghi cả hai trạng thái vào một file, một lần ghi nguyên tử (K7, K13)"""
        save_state(STATE_PATH, {"intr": intrusion_to_dict(intr),
                                "obs": observation_to_dict(obs)})


    recent = RecentAcks()  # các mã vừa ACK, gửi trong trường "acked"

    def send_state():
        mqtt.publish_state(build_state(intr, obs.state, obs.event_id, recent.as_list()))

    send_state()  # ESP32 có trạng thái ngay, kể cả sự kiện vừa khôi phục (K7)
    print("Sẵn sàng. Trạng thái xâm nhập:", intr.state)

    last_seq = 0
    last_hb = 0.0  # lượt đầu tiên gửi hb ngay
    hb_interval = mqtt_cfg["hb_interval_s"]
    n_frames = 0                  # số ảnh xử lý được từ lần in FPS trước
    fps_t0 = time.monotonic()
    
    try:
        while True:
            frame = camera.get_latest(last_seq)  # chờ tối đa 2 giây
            mono = time.monotonic()  # đồng hồ bấm giờ: cho cửa sổ T giây
            wall = time.time()       # đồng hồ treo tường: cho giờ sự kiện
            if mono - last_hb >= hb_interval:  # gõ từ vòng lặp chính: vòng treo thì hb dừng
                mqtt.publish_hb()
                last_hb = mono

            seen = False # Lượt này có ảnh nhìn được không
            img = None   # ảnh của lượt này, để đưa lên stream
            dets = []    # ảnh bị che thì không chạy YOLO, stream vẽ không có khung
            if frame is not None:
                last_seq, img = frame
                n_frames += 1
                # Ảnh bị che không vào cửa sổ khu, giống mất hình: không bao giờ coi là "vắng" (K1)
                if image_detail(img) >= obs_cfg["detail_min"]:
                    dets = detector.detect(img)
                    zones.add_frame(mono, dets)
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
                save() # ghi sổ trước, gửi sau
                if intr.event and intr.event.id != old_id: # vừa mở sự kiện mới
                    blind = obs.state != OBS_OK  # vừa mất quan sát xong (K4)
                    mqtt.publish_event(intrusion_event_msg(intr.event, after_blind=blind))

                send_state()
                zs = sorted(intr.event.zones) if intr.event else []
                print("Xâm nhập:", intr.state, "khu", zs)

            old_obs = obs.state
            if obs.update(mono, good):
                # ok <-> suspect không ghi: không khôi phục, lại bật tắt liên tục làm mòn thẻ SD
                if old_obs in (OBS_LOST, OBS_LOST_ACKED) or obs.state in (OBS_LOST, OBS_LOST_ACKED):
                    save()
                if obs.state == OBS_LOST: # vừa vào mất quan sát
                    mqtt.publish_event(observation_event_msg(obs.event_id))
                send_state()
                print("Quan sát:", obs.state, obs.event_id)
                

            acks = mqtt.get_acks()  # mã ESP32 gửi từ lượt trước, có thể rỗng
            if acks:
                recent.add(acks)  # ghi cả mã cũ để ESP32 ngừng gửi lặp
                intr_ids, obs_ids = split_ack_ids(acks)
                intr_changed = intr.ack(intr_ids)
                obs_changed = obs.ack(obs_ids)  # dòng riêng: không để "or" bỏ qua obs.ack
                if intr_changed or obs_changed:
                    save()
                send_state()  # luôn gửi, kể cả khi không có gì đổi
                print("ACK:", sorted(acks), "->", intr.state, obs.state)
            # Đưa sang stream sau khi trạng thái đã cập nhật: chữ trên hình khớp log.
            # publish chỉ cất ảnh, vẽ và mã hóa chạy ở luồng của stream
            if stream and img is not None:
                stream.publish(img, dets, status_line(intr, obs))
            if mono - fps_t0 >= FPS_EVERY_S:
                print(f"FPS: {n_frames / (mono - fps_t0):.2f}")
                n_frames = 0
                fps_t0 = mono

    except KeyboardInterrupt:
        print("Đang tắt...")
    finally:
        if stream:
            stream.stop()
        camera.stop()
        mqtt.stop()


if __name__ == "__main__":
    main()
