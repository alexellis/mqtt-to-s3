import paho.mqtt.client as mqtt
import sys, time, os

if len(sys.argv) == 1:
    print("Give a message to send as an argument to send.py")
    sys.exit(1)

ch = "openfaas-sensor-data"
sent = False

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    global sent
    print("Connected with result code "+str(rc))

    msg = sys.argv[1]
    client.publish(ch, msg)
    print("Message \"{}\" published to \"{}\"".format(msg, ch))
    sent = True 

client.on_connect = on_connect

server = "test.mosquitto.org"
port = 1883
print("Connecting to {}:{}".format(server, 1883))

client.connect(server, port, 60)
client.loop_start()

while not sent:
     time.sleep(0.5)
client.loop_stop()
client.disconnect()
