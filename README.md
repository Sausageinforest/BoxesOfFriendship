# BoxesOfFriendship

**BoxesOfFriendship** is an interactive project that connects two "friendship boxes" using Raspberry Pi or any Wi-Fi-enabled microcontroller (such as ESP8266) via the MQTT protocol. By pressing a button on one box, an MQTT message is sent to the paired box, triggering actions like lighting up LEDs. This setup enables real-time, wireless interaction between users, fostering a sense of connection regardless of physical distance.

## Project Features

1. **Flexible Hardware Options**: Use a Raspberry Pi or any Wi-Fi-enabled microcontroller (e.g., ESP8266).
2. **Customizable Components**: Supports any length of addressable LED strips and various types of buttons (touch-sensitive or standard).
3. **MQTT Broker Choice**: Utilize a public broker (such as HiveMQ) or set up your own private broker.
4. **Interactive Button Actions**:
   - **Single Press**: The LED strip lights up and fades out in pink.
   - **Double Press**: A pink light chaser runs along the strip.
   - **Triple Press**: A rainbow light chaser runs along the strip.

## Assembly and Setup for ESP8266 (Wemos D1 Mini)

### Required Components

- **Microcontroller**: Wemos D1 Mini (ESP8266)
- **LED Strip**: Addressable LED strip (up to 20 LEDs can be powered directly)
- **Button**: Any type (touch-sensitive or standard)
- **Resistors**: As needed for button debouncing or LED protection
- **Power Supply**: Additional power supply if using more than 20 LEDs
- **Connecting Wires and Breadboard**: For making connections

### Wiring Diagram

#### Without Additional Power Supply



+-----------+ +---------------------+ | Wemos D1 | | Addressable LED Strip| | Mini | | | | | | | | D4 (GPIO2)|----------------->| DATA | | | | | | D2 (GPIO4)|----------------->| BUTTON | | | | | | 5V |----------------->| VCC | | GND |----------------->| GND | +-----------+ +---------------------+


#### With Additional Power Supply


+-----------+ +---------------------+ +---------------------+ | Wemos D1 | | Addressable LED Strip| | External Power Supply| | Mini | | | | | | | | | | | | D4 (GPIO2)|----------------->| DATA | | 5V | | | | | | | | D2 (GPIO4)|----------------->| BUTTON | | GND | | | | | | | | GND |----------------->| GND | | | | | | | | | +-----------+ +---------------------+ +---------------------+




### Assembly Steps

1. **Connect LEDs and Button**:
   - Connect the **DATA** line of the LED strip to **D4 (GPIO2)** on the Wemos D1 Mini.
   - Connect the **Button** to **D2 (GPIO4)**.
   - If using fewer than 20 LEDs, connect the **VCC** of the LED strip to the **5V** pin on the Wemos. Otherwise, use an external power supply to power the LEDs.
   - Connect all **GND** pins to a common ground.

2. **Upload the Sketch**:
   - Open **Arduino IDE**.
   - Select the appropriate board (**Wemos D1 Mini**) and port.
   - Open the `arduino_ide.ino` file.
   - Update the sketch with your Wi-Fi credentials and MQTT broker details:
     ```cpp
     const char* ssid = "YOUR_SSID";
     const char* password = "YOUR_PASSWORD";
     const char* mqtt_server = "YOUR_MQTT_BROKER_URL";
     #define DEVICE_ID 1 // Use 2 for the second device
     ```
     - For the second device, change `#define DEVICE_ID 1` to `#define DEVICE_ID 2`.
     - Refer to [Popular Online Public MQTT Brokers](https://github.com/emqx/blog/blob/main/en/202111/popular-online-public-mqtt-brokers.md) for free options.
   - Ensure that the MQTT topic is unique to avoid conflicts. The same topic should be used on both devices.
   - Upload the sketch to the Wemos D1 Mini.

3. **Final Setup**:
   - Once the sketch is uploaded and the device is connected to Wi-Fi and the MQTT broker, the setup is complete.
   - Pressing the button will trigger the LED actions on the paired device based on the number of presses.

### Button Press Actions

- **Single Press**: The LED strip will light up in pink and fade out.
- **Double Press**: A pink light chaser effect will run along the LED strip.
- **Triple Press**: A rainbow light chaser effect will run along the LED strip.

## Assembly and Setup for Raspberry Pi

### Required Components

- **Microcontroller**: Raspberry Pi (with an installed OS and network connection)
- **LED Strip**: Addressable LED strip
- **Connecting Wires**: For making connections
- **Additional Components**: As needed based on your specific setup

### Assembly Steps

1. **Connect to Raspberry Pi via SSH**:
   - Use an SSH client to access your Raspberry Pi.

2. **Install Necessary Packages and Libraries**:
   ```bash
   sudo apt-get update
   sudo apt-get install gcc make build-essential git scons swig
   git clone https://github.com/jgarff/rpi_ws281x
   cd rpi_ws281x/
   sudo scons
   ```

3. **Connect the LED Strip**:
   - Connect the **DATA** line of the LED strip to **GPIO18 (PWM0)** on the Raspberry Pi.
   - Connect **VCC** and **GND** appropriately.

4. **Set Up Auto-Start for `led.py`**:
   - Create a service file for systemd:
     ```bash
     sudo nano /etc/systemd/system/led-control.service
     ```
   - Add the following content, replacing `$username$` with your actual username:
     ```ini
     [Unit]
     Description=LED Control Service
     After=network.target

     [Service]
     ExecStart=/usr/bin/python3 /home/$username$/led.py
     WorkingDirectory=/home/$username$
     StandardOutput=inherit
     StandardError=inherit
     Restart=always
     User=pi

     [Install]
     WantedBy=multi-user.target
     ```
   - Save and close the file.
   - Set the appropriate permissions and enable the service:
     ```bash
     sudo chmod 644 /etc/systemd/system/led-control.service
     sudo systemctl daemon-reload
     sudo systemctl enable led-control.service
     sudo systemctl start led-control.service
     sudo systemctl status led-control.service
     ```

5. **Prepare the `led.py` Script**:
   - Ensure that the `led.py` script is configured to connect to the same MQTT broker and uses the same MQTT topic as the ESP8266 device.
   - Example `led.py` configuration:
     ```python
     import paho.mqtt.client as mqtt
     from rpi_ws281x import PixelStrip, Color
     import time

     # LED strip configuration
     LED_COUNT = 30        # Number of LED pixels.
     LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM).
     LED_FREQ_HZ = 800000  # LED signal frequency in hertz.
     LED_DMA = 10          # DMA channel to use for generating signal.
     LED_BRIGHTNESS = 255  # Brightness of the LEDs.
     LED_INVERT = False    # True to invert the signal.

     strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
     strip.begin()

     # MQTT settings
     MQTT_BROKER = "YOUR_MQTT_BROKER_URL"
     MQTT_TOPIC = "your/unique/topic"

     def on_connect(client, userdata, flags, rc):
         print("Connected with result code " + str(rc))
         client.subscribe(MQTT_TOPIC)

     def on_message(client, userdata, msg):
         message = msg.payload.decode()
         if message == "button_pressed":
             # Implement button press actions based on press counts
             # This requires additional logic to track press counts
             pass

     client = mqtt.Client()
     client.on_connect = on_connect
     client.on_message = on_message

     client.connect(MQTT_BROKER, 1883, 60)
     client.loop_forever()
     ```

6. **Final Setup**:
   - Once the service is running, pressing the button on the paired device will activate the LEDs on the Raspberry Pi based on the number of button presses.

## Running and Using the Project

1. **Ensure Both Devices are Connected**:
   - Verify that both the ESP8266 and Raspberry Pi are connected to the same Wi-Fi network and have access to the MQTT broker.

2. **Configure MQTT Topics**:
   - Make sure that both devices are set to publish and subscribe to the same unique MQTT topic to enable communication.

3. **Start the Devices**:
   - Power on both the ESP8266 and Raspberry Pi.
   - Press the button on either device to trigger the LED actions on the paired device.

4. **Button Press Actions**:
   - **Single Press**: Lights up the LED strip in pink and fades out.
   - **Double Press**: Runs a pink light chaser along the LED strip.
   - **Triple Press**: Runs a rainbow light chaser along the LED strip.

## Notes

- **Powering LEDs**: For larger LED strips, use an external power supply to prevent overloading the microcontroller.
- **MQTT Security**: When using public brokers, ensure your MQTT topics are unique and secure to prevent unauthorized access.
- **Device Configuration**: For the second device, update the `DEVICE_ID` in the code to differentiate it from the first device.
- **Enhancements**: The project can be expanded by adding more sensors or different types of feedback mechanisms (e.g., vibration motors, display screens).

## Useful Links

- [Arduino IDE](https://www.arduino.cc/en/software)
- [PubSubClient Library for MQTT](https://pubsubclient.knolleary.net/)
- [rpi_ws281x Library for Raspberry Pi](https://github.com/jgarff/rpi_ws281x)
- [List of Public MQTT Brokers](https://github.com/emqx/blog/blob/main/en/202111/popular-online-public-mqtt-brokers.md)


