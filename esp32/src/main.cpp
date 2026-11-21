#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
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
const char *TOPIC_STATUS = "safecam/alarm01/status";
const char *TOPIC_STATE = "safecam/cam01/state";
const char *TOPIC_HB = "safecam/cam01/hb";
const uint32_t RECONNECT_MS = 5000;  // thu ket noi lai broker moi 5s
const uint32_t HB_TIMEOUT_MS = 6000; // mat 3 nhip hb (2 s/nhip) thi coi la mat Pi

WiFiClient net;
PubSubClient mqtt(net);
uint32_t lastReconnectMs = 0;

// Dieu Pi yeu cau (doc tu state). Den/coi that su do decideOutputs() chon
Light piLight = Light::GREEN;
Buzzer piBuzzer = Buzzer::OFF;
bool gotHb = false;    // da nhan it nhat 1 nhip hb chua
uint32_t lastHbMs = 0; // luc nhan nhip hb gan nhat

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

// Doc ban tin state cua Pi, bat den/coi theo "light", "buzzer"
void handleState(const byte *payload, unsigned int len)
{
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, len);
    if (err)
    {
        Serial.printf("state hong: %s\n", err.c_str());
        return; // giu nguyen den cu
    }
    String lightStr = doc["light"] | "";
    String buzzerStr = doc["buzzer"] | "";
    Light l;
    Buzzer b;
    if (!parseLight(lightStr, l) || !parseBuzzer(buzzerStr, b))
    {
        Serial.printf("state la: light=%s buzzer=%s\n", lightStr.c_str(), buzzerStr.c_str());
        return; // giu nguyen den cu
    }
    piLight = l; // chi ghi dieu Pi muon; decideOutputs() moi bat den
    piBuzzer = b;
    Serial.printf("state seq=%d light=%s buzzer=%s\n",
                  doc["seq"] | 0, lightStr.c_str(), buzzerStr.c_str());
}

// Thu vien goi ham nay trong mqtt.loop() moi khi co ban tin
void onMessage(char *topic, byte *payload, unsigned int len)
{
    if (strcmp(topic, TOPIC_HB) == 0)
    {
        gotHb = true; // khong can doc noi dung, chi can biet Pi con song
        lastHbMs = millis();
        return;
    }
    if (strcmp(topic, TOPIC_STATE) == 0)
        handleState(payload, len);
}

// In 1 lan moi khi WiFi doi trang thai
void reportWifi()
{
    static bool lastUp = false;
    bool up = WiFi.status() == WL_CONNECTED;
    if (up != lastUp)
    {
        if (up)
            Serial.printf("WiFi OK, IP: %s\n",
                          WiFi.localIP().toString().c_str());
        else
            Serial.println("Mat WiFi");
        lastUp = up;
    }
}

// Goi moi vong loop: chua ket noi thi 5s thu 1 lan, khong chan
void connectMqtt()
{
    if (WiFi.status() != WL_CONNECTED || mqtt.connected())
        return;
    uint32_t now = millis();
    if (lastReconnectMs != 0 && now - lastReconnectMs < RECONNECT_MS)
        return;
    lastReconnectMs = now;

    Serial.print("MQTT dang ket noi...");
    // Di chuc (LWT): ESP32 rot dot ngot thi broker tu gui "offline" (QoS 1, retain)
    if (mqtt.connect(CLIENT_ID, MQTT_USER, MQTT_PASS, TOPIC_STATUS, 1, true, "offline"))
    {
        Serial.println("OK");
        mqtt.publish(TOPIC_STATUS, "online", true); // retain
        mqtt.subscribe(TOPIC_STATE, 1);             // state co retain: dang ky xong la nhan ngay
        mqtt.subscribe(TOPIC_HB, 0);                // hb QoS 0: mat 1 nhip cung khong sao
    }
    else
    {
        // -2: khong toi duoc broker; 4: sai tai khoan/mat khau; 5: khong co quyen
        Serial.printf("loi rc=%d\n", mqtt.state());
    }
}

// Chon den/coi that su bat: theo Pi, hay kieu "mat Pi"
void decideOutputs()
{
    static bool lastLinkOk = true; // de lan dau in "MAT TIN HIEU PI" neu chua co hb
    uint32_t now = millis();
    bool linkOk = mqtt.connected() && gotHb && (now - lastHbMs < HB_TIMEOUT_MS);
    if (linkOk != lastLinkOk)
    {
        Serial.println(linkOk ? "Nghe duoc Pi" : "MAT TIN HIEU PI");
        lastLinkOk = linkOk;
    }

    if (linkOk)
    {
        currentLight = piLight;
        currentBuzzer = piBuzzer;
    }
    else if (piLight == Light::RED_BLINK)
    {
        // Uu tien 1 tren 2: dang canh bao xam nhap thi giu do nhay va coi
        currentLight = Light::RED_BLINK;
        currentBuzzer = Buzzer::ON;
    }
    else
    {
        currentLight = Light::LINK_LOST; // do vang xen ke
        currentBuzzer = Buzzer::SHORT_BEEP;
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
    mqtt.setCallback(onMessage);
    mqtt.setBufferSize(512); // mac dinh 256 byte: state dai hon bi bo ma khong bao loi
    Serial.println("alarm01: buoc 5 - hb, mat tin hieu Pi");
}

void loop()
{
    reportWifi();
    connectMqtt();
    mqtt.loop();     // giu ket noi, nhan ban tin
    decideOutputs(); // chon den/coi: theo Pi hay "mat Pi"
    updateOutputs(); // khong con delay
}
