import pytest

from safecam.mqtt_client import parse_ack


@pytest.mark.parametrize("payload, expected", [
    (b'{"ids":["I3","O1"]}', {"I3", "O1"}),     # bản tin đúng
    (b'{"ids":["I1","I1"]}', {"I1"}),           # mã trùng gộp lại
    (b'{"ids":[]}', set()),                     # bấm nút khi không có gì chờ ACK
    (b'abc', None),                             # JSON hỏng
    (b'["I1"]', None),                          # JSON đúng nhưng không phải dict
    (b'{"id":["I1"]}', None),                   # sai tên khóa
    (b'{"ids":"I1"}', None),                    # ids không phải danh sách
    (b'{"ids":[1,2]}', None),                   # mã phải là chữ ("I1"), không phải số
    (b'\xff\xfe', None),                        # byte rác, không phải UTF-8
])
def test_parse_ack(payload, expected):
    assert parse_ack(payload) == expected