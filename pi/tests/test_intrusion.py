from safecam.intrusion import ACKED, ALARM, NONE, SUSPECTED, Intrusion
from safecam.zones import ALERT, EMPTY, SUSPECT, UNKNOWN

def v(z2, z3=EMPTY):
    return {2: z2, 3: z3}

def make_alarm():
    it = Intrusion()
    it.update(0, v(ALERT))
    return it

def test_starts_none():
    assert Intrusion().state == NONE

def test_suspect_then_empty_back_to_none():
    it = Intrusion()
    it.update(0, v(SUSPECT))
    assert it.state == SUSPECTED
    it.update(1, v(EMPTY))
    assert it.state == NONE
    assert it.event is None

def test_alert_opens_event():
    it = make_alarm()
    assert it.state == ALARM
    assert it.event.id == 1
    assert it.event.zones == {2}


def test_unknown_does_not_open_or_close():
    it = Intrusion()
    assert it.update(0, v(UNKNOWN, UNKNOWN)) is False
    assert it.state == NONE


def test_alarm_stays_after_person_leaves():
    it = make_alarm()
    it.update(5, v(EMPTY))
    assert it.state == ALARM


def test_zones_accumulate():
    it = make_alarm()
    assert it.update(1, v(EMPTY, ALERT)) is True
    assert it.event.zones == {2, 3}


def test_ack_wrong_id_ignored():
    it = make_alarm()
    assert it.ack([99]) is False
    assert it.state == ALARM


def test_ack_then_empty_closes():
    it = make_alarm()
    assert it.ack([1]) is True
    assert it.state == ACKED
    it.update(10, v(EMPTY))
    assert it.state == NONE
    assert it.last_closed.id == 1
    assert it.last_closed.end == 10


def test_k1_covered_camera_does_not_close():
    # K1: đang cảnh báo → che camera → ACK → sự kiện vẫn mở
    it = make_alarm()
    it.update(1, v(UNKNOWN, UNKNOWN))
    it.ack([1])
    it.update(30, v(UNKNOWN, UNKNOWN))
    assert it.state == ACKED
    assert it.event.id == 1


def test_k10_person_returns_opens_new_event():
    # K10: sự kiện kết thúc rồi có người lại → mở sự kiện mới
    it = make_alarm()
    it.ack([1])
    it.update(10, v(EMPTY))
    it.update(11, v(ALERT))
    assert it.state == ALARM
    assert it.event.id == 2