from Config.constants import ROLES
from Importers.common_imports import *
from Importers.common_functions import *
from Config.oauth import  get_current_user
from Helpers.booking import *


_PATH_PREFIX = "/api/v1/booking"


class BookingRequestRequest(BaseModel):
    first_name: str
    last_name: Optional[str] = ""
    gender : Literal["male", "female" , "others"]
    purpose_of_visit : str
    relation_to_user : str
    remarks : Optional[str] = ""
    email :str
    phone_number: str
    check_in : str
    check_out : str
    room_type : Literal["Standard","Deluxe","Suite","Royal Suite","Dormitory"]
    pax : int

class ConfirmBookingRequest(BaseModel):
    status : str
    reason : Optional[str] = None
    booking_id : str
    status_reason : Optional[str] = None

class BookingActionRequest(BaseModel):
    action : str
    booking_id : str


def check_date_fmt(some_date):
    pattern = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    return re.match(pattern, some_date)

def validate_check_availability_request(start,end):
    if start > end:
        return False
    if start < format_timestamp(get_timestamp(),"%Y-%m-%d"):
        return False
    if end < format_timestamp(get_timestamp(),"%Y-%m-%d"):
        return False
    if start > format_timestamp(get_timestamp() + timedelta(days=60),"%Y-%m-%d"):
        return False
    if end > format_timestamp(get_timestamp() + timedelta(days=60),"%Y-%m-%d"):
        return False
        # end = format_timestamp(get_timestamp() + timedelta(days=60),"%Y-%m-%d")
    return True

@app.get(_PATH_PREFIX + "/availability",tags=["Bookings"])
async def availability_calendar(request:Request,response:Response,start:str,end:str,user=Depends(get_current_user(scopes="login"))):
    try:
        if not check_date_fmt(start) or not check_date_fmt(end):
            return JSONResponse(error_response(message="Invalid date format"),
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        valid = validate_check_availability_request(start, end)
        if not valid:
            return JSONResponse(content=error_response(message="Invalid date format"),
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

        result,error = await check_availability(start,end,request.app.mongodb)
        if error:
            return error
        return JSONResponse(content=success_response(data=result),status_code=status.HTTP_200_OK)
    except Exception as error:
        return JSONResponse(content=error_response(str(error)),status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def validate_booking_request(db,data):
    master_data  = db["MASTER"]
    room_info = await master_data.find_one({"entity":"ROOM_TYPE","props.name":data["room_type"]})
    if not check_date_fmt(data["check_in"]) or not check_date_fmt(data["check_out"]):
        return False,JSONResponse(error_response(message="Invalid date format"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["check_in"] > data["check_out"]:
        return False,JSONResponse(error_response(message="Invalid check_in date"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["check_in"] < format_timestamp(get_timestamp(), "%Y-%m-%d"):
        return False,JSONResponse(error_response(message="Invalid check_in date"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["check_out"] < format_timestamp(get_timestamp(), "%Y-%m-%d"):
        return False,JSONResponse(error_response(message="Invalid check_out date"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["check_in"] > format_timestamp(get_timestamp() + timedelta(days=60), "%Y-%m-%d"):
        return False,JSONResponse(error_response(message="Invalid check_in date"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["check_out"] > format_timestamp(get_timestamp() + timedelta(days=60), "%Y-%m-%d"):
        return False,JSONResponse(error_response(message="Invalid check_out date"),status_code=status.HTTP_400_BAD_REQUEST)
    diff = datetime.strptime(data["check_out"],"%Y-%m-%d") - datetime.strptime(data["check_in"],"%Y-%m-%d")
    if diff > timedelta(days=MAX_ALLOWED_STAY_DURATION):
        return False,JSONResponse(error_response(message="Stay duration must be 3 days or less"),status_code=status.HTTP_400_BAD_REQUEST)
    if data["pax"] > MAX_ALLOWED_PERSONS:
        return False,JSONResponse(error_response(message="No of guests must be 4 or less"),status_code=status.HTTP_400_BAD_REQUEST)
    return True,None


@app.post(_PATH_PREFIX + "/booking-request",tags=["Bookings"])
async def request_booking(request:Request,response:Response,jData : BookingRequestRequest,user=Depends(get_current_user(scopes="login"))):
    data = jData.model_dump()
    valid,error = await validate_booking_request(request.app.mongodb,data)
    if not valid:
        return error
    results,error = await booking_request(data,user,request.app.mongodb)
    if error:
        return error
    else:
        return results




@app.post(_PATH_PREFIX + "/confirm-booking",tags=["Bookings"])
async def booking_confirmation(request:Request,response:Response,jData : ConfirmBookingRequest,user=Depends(get_current_user(scopes="login",roles=ROLES.ADMINS))):
    # data = jData.model_dump()
    error = await confirm_booking(jData.booking_id,jData.status,user,request.app.mongodb,reason=jData.reason)

    if error:
        return error
    else:
        return JSONResponse(content=success_response(message="Booking Status Updated"),status_code=status.HTTP_200_OK)




@app.get(_PATH_PREFIX + "/booking-dashboard",tags=["Bookings"])
async def booking_dashboard(request:Request,response:Response,req_date : str=None,user=Depends(get_current_user(scopes="login",roles=ROLES.ADMINS))):
    # data = jData.model_dump()
    if not req_date:
        req_date = get_timestamp().strftime("%Y-%m-%d")
    data,error = await get_bookings_dashboard_helper(req_date, user,request.app.mongodb)
    if error:
        return error

    else:
        response_data = {"bookings": data}
        return JSONResponse(content=success_response(message="Bookings Fetched",data=response_data),status_code=status.HTTP_200_OK)


@app.get(_PATH_PREFIX + "/booking-statistics",tags=["Bookings"])
async def booking_stats(request:Request,response:Response,req_date : str=None,user=Depends(get_current_user(scopes="login",roles=ROLES.ADMINS))):
    # data = jData.model_dump()
    if not req_date:
        req_date = get_timestamp().strftime("%Y-%m-%d")
    data,error = await get_dashboard_statistics( user,req_date,request.app.mongodb)
    if error:
        return error

    else:
        response_data = data
        return JSONResponse(content=success_response(message="Booking Statistics Fetched",data=response_data),status_code=status.HTTP_200_OK)


@app.get(_PATH_PREFIX + "/booking-requests",tags=["Bookings"])
async def booking_requests(request:Request,response:Response,req_date : str=None,user=Depends(get_current_user(scopes="login",roles=ROLES.ADMINS))):
    if not req_date:
        req_date = get_timestamp().strftime("%Y-%m-%d")
    data,error = await get_dashboard_requests( user,req_date,request.app.mongodb)
    if error:
        return error

    else:
        response_data = {"requests": data}
        return JSONResponse(content=success_response(message="Bookings Requests Fetched",data=response_data),status_code=status.HTTP_200_OK)

@app.get(_PATH_PREFIX + "/user-bookings",tags=["Bookings"])
async def user_bookings(request:Request,response:Response,user=Depends(get_current_user(scopes="login",roles=ROLES.ANY))):

    data,error = await get_user_bookings(user,request.app.mongodb)
    if error:
        return error
    else:
        response_data = {"bookings": data}
        return JSONResponse(content=success_response(message="User Bookings Fetched",data=response_data),status_code=status.HTTP_200_OK)



@app.post(_PATH_PREFIX + "/booking-action",tags=["Bookings"])
async def booking_action(request:Request,response:Response,jData : BookingActionRequest,user=Depends(get_current_user(scopes="login",roles=ROLES.ADMINS))):
    error = await booking_action_helper(jData.booking_id,jData.action,user,request.app.mongodb)
    if error:
        return error
    else:
        return JSONResponse(content=success_response(message="Booking Status Updated"),status_code=status.HTTP_200_OK)


