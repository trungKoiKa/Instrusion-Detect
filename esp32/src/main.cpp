#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "pins.h"
#include "secrets.h"


// Kieu den va coi (docs/mqtt.md). LINK_LOST VA SHORT_BEEP do ESP32 tu bat khi mat Pi
enum class Light
{
    GREEN,
    RED,
    RED_BLINK,
    YELLOW,
    YELLOW_BLINK,
    LINK_LOST
};

enum class Buzzer
{
    OFF,
    ON,
    SLOW,
    SHORT_BEEP
};

Light currentLight = Light::GREEN;
Buzzer currentBuzzer = Buzzer::OFF;

const uint32_t BLINK_HALF_MS = 500;   // den nhay: 0.5 s sang, 0.5 s tat
const uint32_t SLOW_PERIOD_MS = 2000; // coi "slow": bip 200ms moi 2s
const uint32_t SLOW_ON_MS = 200;
const uint32_t SHORT_PERIOD_MS = 1000; // bip ngan khi mat Pi: 80 ms moi 1s
const uint32_t SHORT_ON_MS = 80;

//----------------MQTT (docs/mqtt.md)--------------
const char *CLIENT_ID = "safecam-alarm01";
const char *TOPIC_STATUS =  "safecam/alarm01/status";
const uint32_t RECONNECT_MS = 5000; // thu ket noi lai broker moi 5s

WiFiClient net;
PubSubClient mqtt(net);
uint32_t lastReconnectMs = 0;

// Doc chuoi light cua Pi; chuoi la tra ve false de giu nguyen den cu
bool parseLight(const String &s, Light &out)
{
    if (s == "green")
    {
        out = Light::GREEN;
        return true;
    }
    if (s == "red")
    {
        out = Light::RED;
        return true;
    }
    if (s == "red_blink")
    {
        out = Light::RED_BLINK;
        return true;
    }
    if (s == "yellow")
    {
        out = Light::YELLOW;
        return true;
    }
    if (s == "yellow_blink")
    {
        out = Light::YELLOW_BLINK;
        return true;
    }
    return false;
}

// Doc chuoi buzzer cua Pi
bool parseBuzzer(const String &s, Buzzer &out)
{
    if (s == "off")
    {
        out = Buzzer::OFF;
        return true;
    }
    if (s == "on")
    {
        out = Buzzer::ON;
        return true;
    }
    if (s == "slow")
    {
        out = Buzzer::SLOW;
        return true;
    }
    return false;
}

void setLeds(bool red, bool yellow, bool green)
{
    digitalWrite(LED_RED, red ? HIGH : LOW);
    digitalWrite(LED_YELLOW, yellow ? HIGH : LOW);
    digitalWrite(LED_GREEN, green ? HIGH : LOW);
}

// Goi moi vong loop: tinh den, coi luc nay phai sang/keu hay khong, khong chan
void updateOutputs()
{
    uint32_t now = millis();

    bool blinkOn = (now / BLINK_HALF_MS) % 2 == 0;

    switch (currentLight)
    {
    case Light::GREEN:
        setLeds(false, false, true);
        break;
    case Light::RED:
        setLeds(true, false, false);
        break;
    case Light::RED_BLINK:
        setLeds(blinkOn, false, false);
        break;
    case Light::YELLOW:
        setLeds(false, true, false);
        break;
    case Light::YELLOW_BLINK:
        setLeds(false, blinkOn, false);
        break;
    case Light::LINK_LOST:
        setLeds(blinkOn, !blinkOn, false);
        break;
        // do vang xen ke
    }
    bool buzz = false;
    switch (currentBuzzer)
    {
    case Buzzer::OFF:
        buzz = false;
        break;
    case Buzzer::ON:
        buzz = true;
        break;
    case Buzzer::SLOW:
        buzz = (now % SLOW_PERIOD_MS) < SLOW_ON_MS;
        break;
    case Buzzer::SHORT_BEEP:
        buzz = (now % SHORT_PERIOD_MS) < SHORT_ON_MS;
        break;
    }
    digitalWrite(BUZZER, buzz ? HIGH : LOW);
}

// Buoc 2: go chuoi vao Serial de thu: buoc 4 thay bang ban tin state
void handleSerialTest()
{
    if (!Serial.available())
        return;
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); // bo dau \r, dau cach thua

    Light newLight;
    Buzzer newBuzzer;
    if (parseLight(cmd, newLight))
    {
        currentLight = newLight;
    }
    else if (parseBuzzer(cmd, newBuzzer))
    {
        currentBuzzer = newBuzzer;
    }
    else if (cmd == "lost")
    {
        currentLight = Light::LINK_LOST;
        currentBuzzer = Buzzer::SHORT_BEEP;
    }
    else
    {
        Serial.printf("khong hieu: %s\n", cmd.c_str());
        return;
    }
    Serial.printf("OK: %s\n", cmd.c_str());
}

// In 1 lan moi khi WiFi doi trang thai
void reportWifi()
{
    static bool lastUp = false;
    bool up = WiFi.status() == WL_CONNECTED;
    if (up != lastUp)
    {
        if(up)
            Serial.printf("WiFi OK, IP: %s\n",
            WiFi.localIp().toString().c_str());
        else
            Serial.println("Mat WiFi");
        lastUp = up;
    }
}

// Goi moi vong loop: chua ket noi thi 5s thu 1 lan, khong chan
void connectMqtt()
{
    if(WiFi.status() != WL_CONNECTED || mqtt.connected())
        return;
    uint32_t now = millis();
    if(lastReconnectMs != 0 && now - lastReconnectMs < RECONNECT_MS)
        return;
    lastReconnectMs = now;

    Serial.print("MQTT dang ket noi...");
    // Di chuc (LWT): ESP32 rot dot ngot thi broker tu gui "offline" (QoS 1, retain)
    if(mqtt.connect(CLIENT_ID, MQTT_USER, MQTT_PASS, TOPIC_STATUS, 1, true, "offline"))
    {
        Serial.println("OK");
        mqtt.publish(TOPIC_STATUS, "online", true); //retain
    }
    else{
        // -2: khong toi duoc broker; 4: sai tai khoan/mat khau; 5: khong co quyen
        Serial.printf("loi rc=%d\n", mqtt.state());
    }
}

void setup()
{
    Serial.begin(115200);
    pinMode(BTN_ACK, INPUT);
    pinMode(BTN_MUTE, INPUT);
    pinMode(BTN_NEXT, INPUT);
    pinMode(BTN_TEST, INPUT);
    pinMode(LED_RED, OUTPUT);
    pinMode(LED_YELLOW, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(BUZZER, OUTPUT);
    digitalWrite(BUZZER, LOW);

    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true); // router bat lai thi tu noi lai
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setKeepAlive(10); // broker ~15 s khong nghe thay thi gui LWT "offline"
    Serial.println("alarm01: buoc 3 - WiFi + MQTT");
}

void loop()
{
    reportWifi();
    connectMqtt();
    mqtt.loop(); // giu ket noi, nhan ban tin
    handleSerialTest();
    updateOutputs(); // khong con delay
}
