# Sơ đồ đấu nối bo cảnh báo ESP32

Module ESP32-WROOM-32 hàn trực tiếp (38 chân), đối chiếu Gerber ngày 06/10/2026.
Chân ghi theo số chân module kèm tên GPIO.

## Nút bấm

Mỗi nút nối giữa GPIO và GND, tích cực mức thấp (không nhấn đọc 1, nhấn đọc 0). Mỗi nút có điện trở kéo lên 10 kΩ và tụ chống dội 100 nF.

| Nút | Net | Chân module | GPIO | Kéo lên | Tụ | Chức năng |
|---|---|---|---|---|---|---|
| SW1 | BTN_ACK | Pin 6 | GPIO34 | R7 | C8 | Xác nhận cảnh báo |
| SW2 | BTN_MUTE | Pin 7 | GPIO35 | R8 | C9 | Tắt còi (đèn đỏ và OLED vẫn giữ) |
| SW3 | BTN_NEXT | Pin 8 | GPIO32 | R9 | C10 | Chuyển trang OLED |
| SW4 | BTN_TEST | Pin 9 | GPIO33 | R10 | C11 | Thử còi và LED |

> Chức năng ở cột cuối là dự kiến theo tên net. Hiện firmware cho cả 4 nút cùng chức năng ACK (chốt 19/11, xem `docs/mqtt.md`).

Nút trên bo:

| Nút | Net | Chân module | GPIO | Ghi chú |
|---|---|---|---|---|
| FLASH | BOOT | Pin 25 | GPIO0 | Giữ khi nạp chương trình |
| RESET | EN | Pin 3 | EN | Khởi động lại module |

> **Lưu ý:** GPIO34 và GPIO35 chỉ là input và không có pull-up nội. Không được bỏ R7, R8 khi hàn. Trong code khai báo `INPUT`, không dùng `INPUT_PULLUP`.

## LED

Chuỗi nối: GPIO → điện trở → anode, cathode → GND. LED sáng khi GPIO ở mức cao.

| LED | Chân module | GPIO | Điện trở |
|---|---|---|---|
| LED_RED | Pin 10 | GPIO25 | R4 (330 Ω) |
| LED_GREEN | Pin 11 | GPIO26 | R13 (330 Ω) |
| LED_YELLOW | Pin 12 | GPIO27 | R14 (330 Ω) |

## Các chân liên quan khác

| Khối | Net | Chân module | GPIO | Ghi chú |
|---|---|---|---|---|
| Còi (Q1) | BUZZER | Pin 37 | GPIO23 | Qua R12 (1 kΩ) vào Q1, R11 (10 kΩ) kéo xuống GND. Còi kêu khi mức cao |
| OLED SDA | SDA | Pin 33 | GPIO21 | Chân 4 header OLED |
| OLED SCL | SCL | Pin 36 | GPIO22 | Chân 3 header OLED |
| P1 chân 1 | TXD0 | Pin 35 | GPIO1 | Nối vào RX của mạch USB–UART |
| P1 chân 2 | RXD0 | Pin 34 | GPIO3 | Nối vào TX của mạch USB–UART |

- Header OLED (trái sang phải): GND – 3V3 – SCL – SDA.
- Header P1: TX0 – RX0 – GND – NC. P1 không có chân cấp nguồn, phải cấp nguồn qua jack DC.

## Khai báo trong code

```cpp
// Nút nhấn - tích cực mức thấp, đã có điện trở kéo lên 10k bên ngoài
#define BTN_ACK    34   // input-only, không có pull-up nội
#define BTN_MUTE   35   // input-only, không có pull-up nội
#define BTN_NEXT   32
#define BTN_TEST   33
// LED - tích cực mức cao
#define LED_RED    25
#define LED_GREEN  26
#define LED_YELLOW 27
// Còi - tích cực mức cao (qua Q1)
#define BUZZER     23
// OLED I2C
#define OLED_SDA   21
#define OLED_SCL   22

pinMode(BTN_ACK, INPUT);  pinMode(BTN_MUTE, INPUT);
pinMode(BTN_NEXT, INPUT); pinMode(BTN_TEST, INPUT);
Wire.begin(OLED_SDA, OLED_SCL);
```
