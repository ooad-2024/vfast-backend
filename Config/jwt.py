
from Importers.common_imports import *
from Importers.common_functions import *
from Config.secrets import settings



def create_access_token(payload,expires_delta=settings.ACCESS_TOKEN_EXPIRE_MINUTES):
    try:
        expire = get_timestamp() + timedelta(minutes=expires_delta)
        payload['exp'] = expire
        jwtEncoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return jwtEncoded,None
    except Exception as error:
        return None,error


def decode_access_token(token):
    try:
        jwtDecoded = jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM])
        return jwtDecoded,None
    except JWTError as error:
        return None,"Invalid Access Token"
    except Exception as error:
        return None,"Invalid Access Token"


