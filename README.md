# mqtt-to-s3

Store MQTT messages in S3 - part of the course [Introduction to Kubernetes on Edge with K3s](https://www.edx.org/course/introduction-to-kubernetes-on-edge-with-k3s)

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

Install [Minio](https://min.io/) and [OpenFaaS](https://www.openfaas.com/) to your Kubernetes cluster, and follow related post-install instructions:

```bash
arkade install openfaas
# Then follow the post-install instructions to log in and start
# port-forwarding.

arkade install minio
# Then follow the post-install instructions to log in and start
# port-forwarding.
```

Get CLIs for the Minio client and OpenFaaS:

```bash
arkade get mc
arkade get faas-cli
```

You must have the latest version of faas-cli for this step, check it with `faas-cli version`

Then set up secret for Minio:

```bash
echo -n $SECRETKEY > ./secret-key.txt
echo -n $ACCESSKEY > ./access-key.txt

faas-cli secret create secret-key --from-file ./secret-key.txt --trim
faas-cli secret create access-key --from-file ./access-key.txt --trim
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

# Show the bucket exists:

mc ls minio
[2021-07-17 12:34:06 BST]     0B sensor-data/

# Show that it's empty, and found
mc ls minio/sensor-data
```

Then install the mqtt-connector, which will invoke your functions:

```bash
# Use a unique client ID
# client ID conflicts will cause connect events to fire over and over
# https://github.com/eclipse/paho.mqtt.golang#common-problems
CLIENT_ID=$(head -c 12 /dev/urandom | shasum| cut -d' ' -f1)

arkade install mqtt-connector \
  --topics openfaas-sensor-data \
  --broker-host tcp://test.mosquitto.org:1883 \
  --client-id $CLIENT_ID

kubectl logs deploy/mqtt-connector -n openfaas -f
```

Next, deploy the functions:

```bash
# Change directory to the function folder
cd mqtt-s3-example

# get the template this function depends on
faas-cli template store pull python3-flask

# deploy this function
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

2021-03-14T13:49:13Z 2021/03/14 13:49:13 POST / - 200 OK - ContentLength: 2
2021-03-14T13:50:01Z 2021/03/14 13:50:01 POST / - 200 OK - ContentLength: 2
```

Now check the contents of your S3 bucket with `mc`:

```
mc ls minio/sensor-data

[2021-03-14 09:50:01 EDT]    35B 23c7cb33-246c-4173-af3e-5ce2898aa564.json
[2021-03-14 09:49:13 EDT]    35B 77fb7012-e893-40d6-b23f-477a143bcb5f.json
```

You should see a number of .json files created for each message you create with the sender.


To view the result stored in the file:

```bash
mc cat 23c7cb33-246c-4173-af3e-5ce2898aa564.json

{"sensor_id": 1, "temperature_c": 53}
```

You can also retrieve the file:

```bash
mc cp minio/sensor-data/23c7cb33-246c-4173-af3e-5ce2898aa564.json .
```
