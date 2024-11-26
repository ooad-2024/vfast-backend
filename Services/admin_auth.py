from fastapi.responses import HTMLResponse

from Importers.common_imports import *
from Importers.common_functions import *
from Config.jwt import *
from Config.oauth import get_current_user
from Helpers.auth import *

_PATH_PREFIX = "/api/v1/admin"


class LoginRequest(BaseModel):
    username: str
    password: str


class VerifyOtpRequest(BaseModel):
    otp: str


class GAuthRequest(BaseModel):
    token: str


@app.post(_PATH_PREFIX + "/login",tags=["Admin Auth"])
async def login(request: Request, response: Response, jData: LoginRequest):
    try:
        response, error = await  login_helper(request.app.mongodb, jData.username, jData.password,role=ROLES.ADMINS)
        if error:
            return error
        else:
            data = {"access_token": response}
            return JSONResponse(content=success_response(data=data, message="Proceed to verify otp"),
                                status_code=status.HTTP_200_OK)

    except Exception as e:
        content = {"status": "error", "message": str(e)}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post(_PATH_PREFIX + "/verify-otp",tags=["Admin Auth"])
async def verify_otp(request: Request, response: Response, jData: VerifyOtpRequest,
                     user=Depends(get_current_user(scopes="verify_otp"))):
    try:

        response, error = await otp_verification_helper(request.app.mongodb, user.get("id"), jData.otp,role=ROLES.ADMINS)
        if error:
            return error
        else:
            data = {"access_token": response}
            return JSONResponse(content=success_response(data=data, message="Login Successful"),
                                status_code=status.HTTP_200_OK)

    except Exception as error:
        return JSONResponse(content=error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post(_PATH_PREFIX + "/gauth",tags=["Admin Auth"])
async def g_auth(request: Request, response: Response, token: str):
    try:
        response, error = await gauth_login_helper(token, request.app.mongodb,role=ROLES.ADMINS)
        if error:
            return error
        return JSONResponse(content=success_response(message="Success"), status_code=status.HTTP_200_OK)
    except Exception as error:
        return JSONResponse(content=error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


