from Config.constants import ROLES
from Importers.common_imports import *
from Importers.common_functions import *
from Config.oauth import  get_current_user
from Helpers.room import *


_PATH_PREFIX = "/api/v1/rooms"


@app.get(_PATH_PREFIX + "/all-status",tags=["Rooms"])
async def all_rooms_status(request:Request,response:Response,req_date : str=None):
    if not req_date:
        req_date = get_timestamp().strftime("%Y-%m-%d")
    data,error = await get_rooms(req_date,request.app.mongodb)
    if error:
        return error

    else:
        response_data = {"rooms": data}
        return JSONResponse(content=success_response(message="Rooms Fetched",data=response_data),status_code=status.HTTP_200_OK)
