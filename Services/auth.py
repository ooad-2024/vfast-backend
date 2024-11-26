from fastapi.responses import HTMLResponse

from Importers.common_imports import *
from Importers.common_functions import *
from Config.jwt import *
from Config.oauth import  get_current_user
from Helpers.auth import *
_PATH_PREFIX = "/api/v1/user"

class LoginRequest(BaseModel):
    username: str
    password: str

class VerifyOtpRequest(BaseModel):
    otp: str

class GAuthRequest(BaseModel):
    token: str

@app.post(_PATH_PREFIX + "/login",tags=["User Auth"])
async def login(request: Request,response: Response,jData : LoginRequest):
    try:
        response,error = await  login_helper(request.app.mongodb,jData.username,jData.password)
        if error:
            return error
        else:
            data = {"access_token":response}
            return JSONResponse(content=success_response(data=data,message="Proceed to verify otp"),status_code=status.HTTP_200_OK)

    except Exception as e:
        content = {"status": "error","message":str(e)}
        return JSONResponse(content=content,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@app.post(_PATH_PREFIX + "/verify-otp",tags=["User Auth"])
async def verify_otp(request: Request,response: Response,jData : VerifyOtpRequest,user = Depends(get_current_user(scopes="verify_otp"))):
    try:

        response,error = await otp_verification_helper(request.app.mongodb,user.get("id"),jData.otp)
        if error:
            return error
        else:
            data = {"access_token": response}
            return JSONResponse(content=success_response(data=data, message="Login Successful"),
                                status_code=status.HTTP_200_OK)

    except Exception as error:
        return JSONResponse(content=error,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post(_PATH_PREFIX + "/gauth",tags=["User Auth"])
async def g_auth(request: Request,response: Response,jData : GAuthRequest):
    try:

        response,error = await gauth_login_helper(jData.token,request.app.mongodb)
        if error:
            return error

        data = {"access_token": response}
        return JSONResponse(content=success_response(message="Success",data=data), status_code=status.HTTP_200_OK)
    except Exception as error:
        return JSONResponse(content=error,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get(_PATH_PREFIX + "/google-sign-in",tags=["User Auth"])
async def google_sign_in(request: Request,response: Response):
    return HTMLResponse("""
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Sign-In Test</title>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body>
    <h1>Google Sign-In Test</h1>
    <div id="g_id_onload"
         data-client_id="855258357265-pl8s44g0hvdpmhcju8l0p2rapu8c536n.apps.googleusercontent.com"
         data-callback="handleCredentialResponse"
         data-redirect_uri="https://efc4-103-144-92-224.ngrok-free.app/api/v1/auth/gauth"
>
    </div>
    <div class="g_id_signin"
         data-type="standard"
         data-size="large"
         data-theme="outline"
         data-text="sign_in_with"
         data-shape="rectangular"
         data-logo_alignment="left">
    </div>

    <script>
        function handleCredentialResponse(response) {
            console.log("Encoded JWT ID token: " + response.credential);
            // Decode the JWT token if needed for further processing
            const base64Url = response.credential.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));

            console.log("Decoded ID Token:", JSON.parse(jsonPayload));
        }
    </script>
</body>
</html>

    
    """)