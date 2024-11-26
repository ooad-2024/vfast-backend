import hashlib
import uuid
import pytz
from datetime import datetime



def get_uuid():
    return str(uuid.uuid4())

def generate_uuid():
    return uuid.uuid4()
def get_timestamp():
    return datetime.now(tz=pytz.timezone("Asia/Kolkata"))

def format_timestamp(timestamp,fmt="%Y-%m-%d %H:%M:%S"):
    return timestamp.strftime(fmt)

def sha256_hash(obj):
    return hashlib.sha256(obj.encode()).hexdigest()

def success_response(data=None,message=""):
    return {"status":"success","data":data,"message":message}

def error_response(data=None,message=""):
    return {"status":"error","data":data,"message":message}