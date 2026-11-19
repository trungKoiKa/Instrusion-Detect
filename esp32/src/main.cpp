#include <Arduino.h>
#include "pins.h"

//B1: test phần cứng, chưa dùng mạng
const uint8_t BUTTONS[] = {BTN_ACK, BTN_MUTE, BTN_NEXT, BTN_TEST};
const uint8_t LEDS[] = {LED_RED, LED_YELLOW, LED_GREEN};

void setup(){
    Serial.begin(115200);
    for(uint8_t pin : BUTTONS) pinMode(pin, INPUT);
    for(uint8_t pin : LEDS) pinMode(pin, OUTPUT);
    pinMode(BUZZER, OUTPUT);
    digitalWrite(BUZZER, LOW);
    Serial.println("alarm01: thu phan cung");
}

void loop(){
    // Đèn chạy vòng: mỗi 500 ms đổi sang đèn kế tiếp
    uint8_t on = (millis() / 500) % 3;
    for(uint8_t i = 0; i < 3; i++){
        digitalWrite(LEDS[i], i == on ? HIGH : LOW);
    }

    // Nhấn nút nào thì còi kêu và in số nút
    bool anyPressed = false;
    for(uint8_t i=0; i<4; i++){
        if(digitalRead(BUTTONS[i]) == LOW){
            //LOW = đang nhấn
            anyPressed = true;
            Serial.printf("Nut %u dang nhan\n", i+1);
        }
    }
    digitalWrite(BUZZER, anyPressed ? HIGH : LOW);
    delay(50); // chỉ dùng ở bước thử; từ bước 2 bỏ delay
}