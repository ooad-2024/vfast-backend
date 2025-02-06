from functools import wraps
from typing import Dict

from fastapi import Request, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from Config.secrets import settings
from jose import jwt,JWTError

from google.oauth2 import id_token
from google.auth.transport import requests


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/user/login")


def get_current_user(scopes=None,roles=None):
    def decode_jwt(token: str = Depends(oauth2_scheme)) -> Dict:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if roles is not None:
                if payload['roles'] not in roles.value:

                    raise HTTPException(status_code=401, detail='Token is invalid')
            if scopes is not None:
                if scopes not in payload['scopes']:
                    raise HTTPException(status_code=401, detail='Token is invalid')

            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail='Token is invalid')
    return decode_jwt


def verify_google_token(token):
    try:
        # CLIENT_ID = "855258357265-pl8s44g0hvdpmhcju8l0p2rapu8c536n.apps.googleusercontent.com"
        # CLIENT_ID = "464794475879-742k1rji25rb0bg25lp0cv0c9l5n1ljj.apps.googleusercontent.com"
        CLIENT_ID = settings.GOOGLE_CLIENT_ID

        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # ID token is valid. Extract claims
        print("User's Google ID:", id_info["sub"])
        print("Email:", id_info["email"])
        print("Email Verified:", id_info["email_verified"])
        print("Full Name:", id_info.get("name"))
        print("Profile Picture URL:", id_info.get("picture"))
        return id_info
    except ValueError as e:
        print("Invalid token:", e)
        return None
