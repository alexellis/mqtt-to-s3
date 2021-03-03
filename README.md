# mqtt-s3

Store MQTT messages in S3

## Installation

Make sure have Minio and OpenFaaS installed to your Kubernetes cluster:

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
git clone --depth=1 https://github.com/openfaas/faas-netes
cd faas-netes/chart

helm template mqtt-connector --namespace openfaas mqtt-connector/  \
 --set topic=openfaas-sensor-data \
 --set broker=tcp://test.mosquitto.org:8883 \
 --set clientID=mqtt-connector1 \
  | kubectl apply -f -

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

