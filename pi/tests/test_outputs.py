import json

import pytest

from safecam.intrusion import ACKED, ALARM, NONE, SUSPECTED, Intrusion
from safecam.outputs import (
    OBS_LOST, OBS_LOST_ACKED, OBS_OK, OBS_SUSPECT,
    RecentAcks, build_state, intrusion_event_msg, obs_code,
    observation_event_msg, pending_ids, pick_light_buzzer, split_ack_ids,
)
from safecam.zones import ALERT, EMPTY


def make_alarm():
    it = Intrusion()
    it.update(0, {2: ALERT})  # mở sự kiện I1 ở khu 2
    return it


@pytest.mark.parametrize("intr_st, obs_st, expected", [
    (ALARM, OBS_LOST, ("red_blink", "on")),         # ưu tiên 1 thắng 3
    (ACKED, OBS_LOST, ("yellow_blink", "slow")),    # 3 thắng 4
    (ACKED, OBS_LOST_ACKED, ("red", "off")),        # 4 thắng 5
    (NONE, OBS_LOST_ACKED, ("yellow", "off")),
    (SUSPECTED, OBS_SUSPECT, ("green", "off")),     # nghi ngờ thì chưa báo
    (NONE, OBS_OK, ("green", "off")),
])
def test_priority_table(intr_st, obs_st, expected):
    assert pick_light_buzzer(intr_st, obs_st) == expected


def test_codes():
    assert obs_code(1) == "O1"  # chữ O, không phải số 0
    assert split_ack_ids({"I3", "O1", "X5", "I", "", "Iabc"}) == ({3}, {1})


def test_pending_alarm_and_lost():
    assert pending_ids(make_alarm(), OBS_LOST, 1) == ["I1", "O1"]


def test_acked_not_pending():
    it = make_alarm()
    it.ack({1})
    assert pending_ids(it, OBS_LOST_ACKED, 1) == []


def test_old_ack_does_not_silence_new_event():
    """Quy tắc 2: ACK gửi cho I1 không tắt sự kiện I2 mở sau đó."""
    it = make_alarm()
    it.ack({1})
    it.update(5, {2: EMPTY})   # vắng người -> I1 kết thúc
    it.update(6, {2: ALERT})   # người quay lại -> mở I2
    intr_ids, _ = split_ack_ids({"I1"})  # ESP32 vẫn còn gửi lại ACK cũ
    assert it.ack(intr_ids) is False
    assert pending_ids(it, OBS_OK, None) == ["I2"]


def test_recent_acks_no_duplicate_and_limited():
    r = RecentAcks(size=3)
    r.add({"I1"})
    r.add({"I1", "O1"})
    assert r.as_list() == ["I1", "O1"]
    r.add({"I2", "I3"})
    assert r.as_list() == ["O1", "I2", "I3"]  # I1 cũ nhất bị đẩy ra


def test_state_normal():
    s = build_state(Intrusion(), OBS_OK, None, [])
    assert s["light"] == "green" and s["buzzer"] == "off"
    assert s["intr"] == {"st": NONE, "id": None, "zones": []}
    assert s["pending"] == []


def test_state_fits_esp32_buffer():
    """Bản tin dài nhất vẫn dưới 512 byte (setBufferSize của ESP32)."""
    it = Intrusion()
    it.update(0, {0: ALERT, 1: ALERT, 2: ALERT, 3: ALERT})
    s = build_state(it, OBS_LOST, 99, ["I100", "I101", "O102", "I103", "O104"])
    text = json.dumps({"seq": 999999, **s}, separators=(",", ":"))  # giống mqtt_client
    assert len(text.encode()) < 512


def test_event_messages():
    assert intrusion_event_msg(make_alarm().event) == {
        "id": "I1", "type": "intrusion", "zones": [2], "after_blind": False}
    assert observation_event_msg(1) == {
        "id": "O1", "type": "observation", "reason": "lost"}