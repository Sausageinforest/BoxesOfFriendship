import time
import paho.mqtt.client as mqtt
from rpi_ws281x import *
from datetime import datetime
from gpiozero import Button
from threading import Timer

# LED strip configuration:
LED_COUNT      = 19      # ���������� �����������
LED_PIN        = 12      # GPIO ��� ��� ����� (BCM)
LED_FREQ_HZ    = 800000  # ������� �������
LED_DMA        = 10      # DMA �����
LED_BRIGHTNESS = 128     # ������� (0-255)
LED_INVERT     = False   # �������� �������
LED_CHANNEL    = 0       # ����� PWM (0 ��� 1)

# ��������� ������ (GPIO2 = PIN3)
BUTTON_PIN = 2
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)

# MQTT ���������
MQTT_BROKER = "178.159.112.70"
MQTT_PORT = 1883
MQTT_TOPIC = "led_control_channel"
DEVICE_ID = "DEVICE2"

# ���������� ��� �������� �������
click_count = 0
click_timer = None
CLICK_TIMEOUT = 2.0  # ����� �������� ����� ��������� (2 �������)

# ������� ������ LED-�����
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def wheel(pos):
    """��������� ����� ������ �� ������� 0-255."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def clear_strip():
    """������� �����."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def pink_color(brightness):
    """�������� �������� ����� �������� �������."""
    r = int((255 * brightness) / 255)
    g = int((20 * brightness) / 255)
    b = int((147 * brightness) / 255)
    return Color(r, g, b)

class AnimationController:
    def __init__(self):
        self.current_animation = 0
        self.is_animating = False
        self.current_pos = 0
        self.pulse_value = 0
        self.pulse_direction = True
        self.last_update = time.time()

    def start_animation(self, animation_number):
        self.current_animation = animation_number
        self.is_animating = True
        self.current_pos = 0
        self.pulse_value = 0
        self.pulse_direction = True
        clear_strip()
        print(f"������ �������� {animation_number}")

    def update_pulse_animation(self):
        """��������� �������."""
        current_time = time.time()
        if current_time - self.last_update < 0.015:
            return True

        if self.pulse_direction:
            self.pulse_value += 1
            if self.pulse_value >= 255:
                self.pulse_direction = False
        else:
            self.pulse_value -= 1
            if self.pulse_value <= 0:
                self.is_animating = False
                clear_strip()
                return False

        for i in range(strip.numPixels()):
            strip.setPixelColor(i, pink_color(self.pulse_value))
        strip.show()
        self.last_update = current_time
        return True

    def update_pink_runner_animation(self):
        """������� ������� ������."""
        current_time = time.time()
        if current_time - self.last_update < 0.03:
            return True

        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))

        strip.setPixelColor(self.current_pos, pink_color(255))

        if self.current_pos > 0:
            strip.setPixelColor(self.current_pos - 1, pink_color(192))
        if self.current_pos > 1:
            strip.setPixelColor(self.current_pos - 2, pink_color(128))

        strip.show()
        self.current_pos += 1

        if self.current_pos >= strip.numPixels():
            self.is_animating = False
            clear_strip()
            return False

        self.last_update = current_time
        return True

    def update_rainbow_runner_animation(self):
        """������� �������� ������."""
        current_time = time.time()
        if current_time - self.last_update < 0.04:
            return True

        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))

        position = (self.current_pos * 256 // strip.numPixels()) + int(time.time() * 100) % 256
        strip.setPixelColor(self.current_pos, wheel(position & 255))

        if self.current_pos > 0:
            strip.setPixelColor(self.current_pos - 1, wheel((position - 8) & 255))
        if self.current_pos > 1:
            strip.setPixelColor(self.current_pos - 2, wheel((position - 16) & 255))

        strip.show()
        self.current_pos += 1

        if self.current_pos >= strip.numPixels():
            self.is_animating = False
            clear_strip()
            return False

        self.last_update = current_time
        return True

    def update(self):
        if not self.is_animating:
            return

        if self.current_animation == 1:
            self.is_animating = self.update_pulse_animation()
        elif self.current_animation == 2:
            self.is_animating = self.update_pink_runner_animation()
        elif self.current_animation == 3:
            self.is_animating = self.update_rainbow_runner_animation()

# ������� ���������� ��������
animation_controller = AnimationController()
mqtt_client = None

def handle_click_timeout():
    """��������� �������� ����� ���������."""
    global click_count
    if click_count > 0:
        print(f"���������� �������: {click_count}")
        # ���������� ��������� � MQTT
        message = f"{DEVICE_ID}_clicks_{click_count}"
        mqtt_client.publish(MQTT_TOPIC, message)
        # ��������� ��������
        animation_controller.start_animation(click_count)
    click_count = 0

def handle_button_press():
    """��������� ������� ������."""
    global click_count, click_timer

    # �������� ���������� ������ ���� �� ���
    if click_timer:
        click_timer.cancel()

    click_count += 1
    print(f"������� {click_count}")

    # ������������� ����� ������
    click_timer = Timer(CLICK_TIMEOUT, handle_click_timeout)
    click_timer.start()

def on_connect(client, userdata, flags, rc):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ���������� � MQTT �������")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    if not message.startswith(DEVICE_ID):
        try:
            clicks = int(message.split('_')[-1])
            if 1 <= clicks <= 3:
                animation_controller.start_animation(clicks)
        except (ValueError, IndexError):
            print(f"������������ ���������: {message}")

def main():
    global mqtt_client

    # ��������� MQTT �������
    mqtt_client = mqtt.Client(client_id=DEVICE_ID, protocol=mqtt.MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # ��������� ����������� ������
    button.when_pressed = handle_button_press

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ����������� � ������� {MQTT_BROKER}...")

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()

        print("\n���������� ������ � ������")
        print("������� Ctrl+C ��� ������")

        while True:
            if animation_controller.is_animating:
                animation_controller.update()
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n���������� ������...")
    finally:
        if click_timer:
            click_timer.cancel()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        clear_strip()

if __name__ == "__main__":
    main()
