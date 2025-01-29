#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <FastLED.h>

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

const char* mqtt_server = "BROKER_ADRESS";
const int mqtt_port = 1883;
const char* mqtt_topic = "led_control_channel";
const char* device_id = "DEVICE1";


#define LED_PIN D4
#define BUTTON_PIN D2
#define NUM_LEDS 19
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB


CRGB leds[NUM_LEDS];
WiFiClient espClient;
PubSubClient client(espClient);


const unsigned long COUNT_INTERVAL = 2000;  
unsigned long firstClickTime = 0;
int clickCount = 0;
bool isCountingClicks = false;
bool buttonState = HIGH;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;


bool isAnimating = false;
uint8_t currentPos = 0;
int currentAnimation = 0;

й
const int PULSE_SPEED = 18;     
const int RUNNER_SPEED = 45;    
const int RAINBOW_SPEED = 50;   


uint8_t pulseValue = 0;
bool pulseDirection = true;

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Подключение к ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi подключен");
    Serial.println("IP адрес: ");
    Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
    String message = "";
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }

    if (!message.startsWith(device_id)) {
        int clicks = message.substring(message.length() - 1).toInt();
        startAnimation(clicks);
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("Подключение к MQTT...");
        String clientId = "ESP8266-";
        clientId += String(random(0xffff), HEX);

        if (client.connect(clientId.c_str())) {
            Serial.println("подключено");
            client.subscribe(mqtt_topic);
        } else {
            Serial.print("ошибка, rc=");
            Serial.print(client.state());
            Serial.println(" повтор через 5 секунд");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(128);
    FastLED.clear();

    setup_wifi();
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(callback);
}

void checkButton() {
    int reading = digitalRead(BUTTON_PIN);

    if (reading != lastButtonState) {
        lastDebounceTime = millis();
    }

    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading != buttonState) {
            buttonState = reading;

            if (buttonState == LOW) {  
                if (!isCountingClicks) {
                    isCountingClicks = true;
                    firstClickTime = millis();
                    clickCount = 1;
                } else {
                    clickCount++;
                }
                Serial.println("Нажатие " + String(clickCount));
            }
        }
    }


    if (isCountingClicks && (millis() - firstClickTime > COUNT_INTERVAL)) {
        isCountingClicks = false;
        Serial.println("Финальное количество нажатий: " + String(clickCount));


        if (clickCount > 0) {
            String message = String(device_id) + "_clicks_" + String(clickCount);
            client.publish(mqtt_topic, message.c_str());
            startAnimation(clickCount);
            clickCount = 0;
        }
    }

    lastButtonState = reading;
}

void startAnimation(int clicks) {
    if (clicks < 1 || clicks > 3) return;

    isAnimating = true;
    currentPos = 0;
    pulseValue = 0;
    pulseDirection = true;
    currentAnimation = clicks;
    FastLED.clear();
    Serial.println("Запуск анимации " + String(clicks));
}

void updateAnimation() {
    if (!isAnimating) return;

    switch (currentAnimation) {
        case 1:
            updatePulseAnimation();
            break;
        case 2:
            updatePinkRunnerAnimation();
            break;
        case 3:
            updateRainbowRunnerAnimation();
            break;
    }
}

void updatePulseAnimation() {
    EVERY_N_MILLISECONDS(PULSE_SPEED) {
        if (pulseDirection) {
            pulseValue++;
            if (pulseValue == 255) pulseDirection = false;
        } else {
            pulseValue--;
            if (pulseValue == 0) {
                pulseDirection = true;
                isAnimating = false;
                FastLED.clear();
                return;
            }
        }

        for(int i = 0; i < NUM_LEDS; i++) {
            leds[i] = CHSV(230, 255, pulseValue);
        }
        FastLED.show();
    }
}

void updatePinkRunnerAnimation() {
    EVERY_N_MILLISECONDS(RUNNER_SPEED) {
        fadeToBlackBy(leds, NUM_LEDS, 128);  

        // Розовый цвет (HSV: 230, 255, 255)
        leds[currentPos] = CHSV(230, 255, 255);

        if (currentPos > 0) {
            leds[currentPos - 1] = CHSV(230, 255, 192);
        }
        if (currentPos > 1) {
            leds[currentPos - 2] = CHSV(230, 255, 128);
        }

        FastLED.show();

        currentPos++;
        if (currentPos >= NUM_LEDS) {
            isAnimating = false;
            FastLED.clear();
            FastLED.show();
        }
    }
}

void updateRainbowRunnerAnimation() {
    EVERY_N_MILLISECONDS(RAINBOW_SPEED) {
        fadeToBlackBy(leds, NUM_LEDS, 128);

        uint8_t hue = (currentPos * 255 / NUM_LEDS) + (millis() / 10);

        leds[currentPos] = CHSV(hue, 255, 255);

        if (currentPos > 0) {
            leds[currentPos - 1] = CHSV(hue - 8, 255, 192);
        }
        if (currentPos > 1) {
            leds[currentPos - 2] = CHSV(hue - 16, 255, 128);
        }

        FastLED.show();

        currentPos++;
        if (currentPos >= NUM_LEDS) {
            isAnimating = false;
            FastLED.clear();
            FastLED.show();
        }
    }
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    checkButton();

    if (isAnimating) {
        updateAnimation();
    }
}
