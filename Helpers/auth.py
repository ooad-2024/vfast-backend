from Config.constants import ROLES
from Config.oauth import verify_google_token
from Importers.common_imports import *
from Importers.common_functions import *
from Config.jwt import *
from Helpers.email import sendOtp
username_regex = r'[a-zA-Z0-9._%+-]+@pilani\.bits-pilani\.ac\.in'
import pyotp


def generate__otp(secret_key, interval=900):
    totp = pyotp.TOTP(secret_key, interval=interval)
    otp = totp.now()
    return otp


def verify_otp(secret_key, otp_input, interval=900):
    totp = pyotp.TOTP(secret_key, interval=interval)
    if totp.verify(otp_input):
        return True
    else:
        return False


async def login_helper(db,username, password,role=ROLES.USER):
    try:
        if not re.match(username_regex, username):
            return None, JSONResponse(status_code=400, content=error_response(message='Invalid username'))
        users_col = db["Users"] if role == ROLES.USER else db["AdminUsers"]
        user = await users_col.find_one({"$and": [{"username": username}, {"password": sha256_hash(password)}]},{"_id":1,"role":1})
        if not user:
            return None, JSONResponse(status_code=400, content=error_response(message='Invalid username or password'))
        else:
            user_role = user.get("role")
            user_id = str(user.get("_id"))
            access_token,error = create_access_token({"roles": user_role, "id": user_id, "scopes": ["verify_otp"]},10)
            otp = random.randint(100000, 999999)
            error = sendOtp(username,otp)
            if error:
                return None, JSONResponse(status_code=500, content=error_response(message=str(error)))
            users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"otp": str(otp)}})
        return access_token, None
    except Exception as error:
        return None,JSONResponse(status_code=500, content=error_response(message=str(error)))



async def otp_verification_helper(db,id,otp,role=ROLES.USER):
    users_col = db["Users"] if role == ROLES.USER else db["AdminUsers"]
    user = await users_col.find_one({"$and": [{"otp": otp}, {"_id": ObjectId(id)}]})
    if not user:
        return None, JSONResponse(status_code=400, content=error_response(message='Invalid OTP'))
    else:
        access_token,error = create_access_token({"roles": user.get("role"), "id": str(user["_id"]), "scopes": ["login"]})
        if error:
            return None, JSONResponse(status_code=500, content=error_response(message=str(error)))
        otp = random.randint(100000, 999999)
        users_col.update_one({"_id":user["_id"]}, {"$set": {"otp": str(otp)}})

        return access_token, None



async def gauth_login_helper(token,db,role=ROLES.USER):
    user_info =  verify_google_token(token)
    if not user_info:
        return None, JSONResponse(status_code=400, content=error_response(message='Invalid token'))
    users_col = db["Users"] if role == ROLES.USER else db["AdminUsers"]
    user = await users_col.find_one({"$or":[{"google-id": user_info["sub"]},{"email": user_info["email"]}]},)
    if user is None and role == ROLES.USER:
        user = {
                "_id":ObjectId(),
                "username": user_info["email"],
                "email": user_info["email"],
                "google_id": user_info["sub"],
                "role": ROLES.USER.value,
                "otp":str(random.randint(100000, 999999)),
                "password":None
            }
        await users_col.insert_one(user)
    elif user is None and role != ROLES.USER:
        return None, JSONResponse(status_code=400, content=error_response(message='Invalid token'))

    if not user.get("google_id"):
        await users_col.update_one({"email":user["email"]},{"$set":{"google_id": user_info["sub"]}})

    access_token, error = create_access_token({"roles": user.get("role"), "id": str(user["_id"]), "scopes": ["login"]})
    if error:
        return None, JSONResponse(status_code=500, content=error_response(message=str(error)))

    return access_token, None


