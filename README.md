# mqtt-to-s3

Store MQTT messages in S3

This sample uses an [OpenFaaS MQTT-connector](https://github.com/openfaas/mqtt-connector) along with a Python function to receive JSON messages from MQTT and to store them in an S3 bucket.

The use-case could be ingestion of IoT sensor data from edge devices. It is a starting point, and easy to modify for your own uses.

## Installation

Install [arkade](https://get-arkade.dev), the open-source Kubernetes marketplace:

```bash
# Move arkade into your $PATH
curl -sLS https://dl.get-arkade.dev | sh

# Or have arkade move itself into /usr/local/bin/
curl -sLS https://dl.get-arkade.dev | sudo sh
```

Make sure have [Minio](https://min.io/) and [OpenFaaS](https://www.openfaas.com/) installed to your Kubernetes cluster:

```bash
# Follow the post-install instructions to log in and start
# port-forwarding.
arkade install openfaas

arkade install minio
```

Get CLIs for the Minio client and OpenFaaS:

```bash
arkade get mc
arkade get faas-cli
```

Then set up secret for Minio:

```bash
faas-cli secret create secret-key --from-file ./secret-key.txt
faas-cli secret create access-key --from-file ./access-key.txt
```

Setup `mc` to access Minio:

```bash
kubectl port-forward svc/minio 9000:9000 &

mc alias set minio http://127.0.0.1:9000 $(cat access-key.txt) $(cat secret-key.txt)

Added `minio` successfully.
```

Then make a bucket for the sensor data:

```bash
mc mb minio/sensor-data

# Show that it's empty
mc ls minio/sensor-data
```

Then install the mqtt-connector, which will invoke your functions:

```bash
arkade install mqtt-connector \
  --topics openfaas-sensor-data \
  --broker-host tcp://test.mosquitto.org:1883 \
  --client-id mqtt-connector-1

kubectl logs deploy/mqtt-connector -n openfaas -f
```

Next, deploy the functions:

```bash
faas-cli deploy
```

## Testing the functions

Then publish an event to the "openfaas-sensor-data" topic on the iot.eclipse.org test server.

You can run the [sender/send.py](sender/send.py) file to publish a message to the topic. Our function will store the message in an S3 bucket.

First run:

```bash
pip3 install paho-mqtt
```

Then run `sender/send.py`

```bash
$ python3 send.py '{"sensor_id": 1, "temperature_c": 50}'

Connecting to test.mosquitto.org:1883
Connected with result code 0
Message "{"sensor_id": 1, "temperature_c": 53}" published to "openfaas-sensor-data"

$ python3 send.py '{"sensor_id": 1, "temperature_c": 53}'
```

Check the logs of the function to see that it was invoked:

```bash
faas-cli logs mqtt-s3
```

Now check the contents of your S3 bucket with `mc`:

```
mc ls minio/sensor-data
```

You should see a number of .json files created for each message you create with the sender.

