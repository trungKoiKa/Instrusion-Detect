from safecam.intrusion import ACKED, ALARM, NONE, SUSPECTED, Intrusion
from safecam.persistence import (intrusion_from_dict, intrusion_to_dict,
                                 load_state, save_state)
from safecam.zones import ALERT, EMPTY, SUSPECT


def test_save_then_load(tmp_path):
    f = tmp_path / "state.json"
    save_state(f, {"a": 1, "b": [2, 3]})
    assert load_state(f) == {"a": 1, "b": [2, 3]}
    assert not (tmp_path / "state.json.tmp").exists()   # file tạm đã được đổi tên


def test_missing_file_returns_none(tmp_path):
    assert load_state(tmp_path / "khong_co.json") is None


def test_corrupt_file_returns_none_and_kept(tmp_path):
    f = tmp_path / "state.json"
    f.write_text('{"state": "ala')      # giả lập file bị cắt giữa chừng
    assert load_state(f) is None
    assert (tmp_path / "state.json.bad").exists()


def test_old_file_survives_failed_write(tmp_path):
    # K13: mất điện lúc đang ghi file tạm, file chính vẫn là bản cũ đọc được
    f = tmp_path / "state.json"
    save_state(f, {"v": 1})
    (tmp_path / "state.json.tmp").write_text('{"v": 2')
    assert load_state(f) == {"v": 1}


def test_alarm_restored_after_restart(tmp_path):
    # K7: đang cảnh báo thì khởi động lại, sự kiện vẫn mở và báo tiếp
    it = Intrusion()
    it.update(10.0, {2: ALERT, 3: EMPTY})
    f = tmp_path / "state.json"
    save_state(f, intrusion_to_dict(it))

    it2 = intrusion_from_dict(load_state(f))
    assert it2.state == ALARM
    assert it2.event.id == 1
    assert it2.event.start == 10.0
    assert it2.event.zones == {2}
    assert it2.next_id == 2             # sự kiện mới không trùng mã cũ


def test_acked_restored():
    it = Intrusion()
    it.update(0, {2: ALERT, 3: EMPTY})
    it.ack([1])
    it2 = intrusion_from_dict(intrusion_to_dict(it))
    assert it2.state == ACKED
    assert it2.ack([1]) is False        # đã ACK rồi thì không ACK lại


def test_suspected_not_restored():
    it = Intrusion()
    it.update(0, {2: SUSPECT, 3: EMPTY})
    assert it.state == SUSPECTED
    it2 = intrusion_from_dict(intrusion_to_dict(it))
    assert it2.state == NONE
    assert it2.event is None