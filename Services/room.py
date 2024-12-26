from Config.constants import ROLES
from Importers.common_imports import *
from Importers.common_functions import *
from Config.oauth import  get_current_user
from Helpers.room import *


_PATH_PREFIX = "/api/v1/rooms"

class GetRoomsRequest(BaseModel):
    type :str
    check_in : str
    check_out : str

@app.get(_PATH_PREFIX + "/all-status",tags=["Rooms"])
async def all_rooms_status(request:Request,response:Response,req_date : str=None):
    if not req_date:
        req_date = get_timestamp().strftime("%Y-%m-%d")
    data,error = await get_rooms_status(req_date, request.app.mongodb)
    if error:
        return error

    else:
        response_data = {"rooms": data}
        return JSONResponse(content=success_response(message="Rooms Fetched",data=response_data),status_code=status.HTTP_200_OK)

@app.post(_PATH_PREFIX + "/available-rooms",tags=["Rooms"])
async def get_available_rooms(request:Request,response:Response,jData :  GetRoomsRequest):
    try:
        data,error = await get_rooms(jData.type,jData.check_in ,jData.check_out,request.app.mongodb)
        if error:
            return error
        return JSONResponse(content=success_response(message="Rooms Fetched",data=data),status_code=status.HTTP_200_OK)
    except Exception as error:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))



@app.get(_PATH_PREFIX + "/room-types",tags=["Rooms"])
async def get_room_dd(request:Request,response:Response):

    data,error = await get_room_type_dd(request.app.mongodb)
    if error:
        return error

    else:
        response_data = {"room_types": data}
        return JSONResponse(content=success_response(message="Rooms Types Fetched",data=response_data),status_code=status.HTTP_200_OK)
