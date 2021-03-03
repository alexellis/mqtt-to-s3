import os
from minio import Minio
import uuid

def read_secret(name):
    r = None
    with open("/var/openfaas/secrets/{}".format(name)) as f:
        r = f.read()
        f.close()
    return r

def upload(mc, req, dest_bucket):
    # write to temporary file
    uuid_value = str(uuid.uuid4())
    dest_file_name = uuid_value + ".json"

    fullPath = "/tmp/" + dest_file_name
    f = open(fullPath, "wb")
    f.write(req)
    f.close()

    # sync to Minio
    mc.fput_object(bucket_name=dest_bucket, 
        object_name=dest_file_name,
        file_path=fullPath)

    os.remove(fullPath)

def handle(req):
    access_key = read_secret("access-key")
    secret_key = read_secret("secret-key")

    dest_bucket = os.getenv("s3_bucket")
    hostname = os.environ['s3_host']
    region = os.environ['s3_region']

    mc = Minio(hostname,
                  access_key=access_key,
                  secret_key=secret_key,
                  secure=False,
                  region=region)

    upload(mc, req, dest_bucket)

    return "OK"
