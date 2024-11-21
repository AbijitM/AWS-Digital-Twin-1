import time
import json
import Adafruit_DHT
import spidev
import ssl
import paho.mqtt.client as mqtt

# AWS IoT Core Configuration
ENDPOINT = "<YOUR_AWS_IOT_ENDPOINT>"  # Replace with your AWS IoT endpoint
CLIENT_ID = "RaspberryPi"
PATH_TO_CERT = "/path/to/cert.pem.crt"  # Replace with your certificate file path
PATH_TO_KEY = "/path/to/private.pem.key"  # Replace with your private key file path
PATH_TO_ROOT_CA = "/path/to/AmazonRootCA1.pem"  # Replace with your Root CA file path
TOPIC = "raspberrypi/sensors"

# Sensor Pins and Configuration
DHT_SENSOR = Adafruit_DHT.DHT22  # or Adafruit_DHT.DHT11
DHT_PIN = 4                      # GPIO pin for DHT sensor
MCP3008_CHANNEL = 0              # MCP3008 channel for soil moisture sensor

# Function to initialize SPI for MCP3008
def init_spi():
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Open SPI bus 0, device 0
    spi.max_speed_hz = 1350000
    return spi

# Function to read from MCP3008
def read_adc(spi, channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# MQTT Callback Function
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to AWS IoT Core!")
    else:
        print(f"Failed to connect. Return code: {rc}")

# Initialize MQTT Client
mqtt_client = mqtt.Client(CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.tls_set(ca_certs=PATH_TO_ROOT_CA,
                    certfile=PATH_TO_CERT,
                    keyfile=PATH_TO_KEY,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,
                    ciphers=None)
mqtt_client.tls_insecure_set(False)
mqtt_client.connect(ENDPOINT, port=8883, keepalive=60)

# Initialize SPI for MCP3008
spi = init_spi()

# Main Loop to Collect and Send Data
try:
    mqtt_client.loop_start()
    while True:
        # Read temperature and humidity from DHT sensor
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        
        if humidity is None or temperature is None:
            print("Failed to read from DHT sensor. Retrying...")
            continue
        
        # Read soil moisture value from MCP3008
        soil_moisture = read_adc(spi, MCP3008_CHANNEL)

        # Normalize soil moisture value (0-100%)
        soil_moisture_percentage = (1023 - soil_moisture) / 1023 * 100

        # Prepare data payload
        sensor_data = {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "soil_moisture": round(soil_moisture_percentage, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        }

        # Publish to AWS IoT Core
        mqtt_client.publish(TOPIC, json.dumps(sensor_data), qos=1)
        print(f"Published: {sensor_data} to topic: {TOPIC}")

        # Delay before next reading
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping MQTT Client")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    spi.close()
