import random
from operator import length_hint

import bson
import pymongo

from Config.constants import MAX_ALLOWED_STAY_DURATION, MAX_ALLOWED_PERSONS
from Helpers.email import sendBookingConfirmation
from Importers.common_imports import *
from Importers.common_functions import *
from Config.models import *
from Helpers.mongo import get_check_availability_pipeline, get_booking_check_pipeline, get_bookings_dashboard_pipeline, \
    get_booking_statistics_pipeline, get_requests_dashboard_pipeline,get_user_bookings_pipeline


# def insert_room():
#     inserts = []
#     for room_no in range(301,309):
#         room = Room(room_number=str(room_no),room_type = "Executive",status="Available",capacity=2,bookings=[])
#         room_json = room.model_dump()
#         inserts.append(room_json)
#     conn = pymongo.MongoClient("")
#     db = conn["vfast-client"]
#     rooms = db["Room"]
#     result = rooms.insert_many(inserts)
#
# def insert_room_bookings():
#
#     room_no = "103"
#     room = RoomBookings(check_in="2024-10-29T12:00:00+0530",check_out="2024-10-30T10:00:00+0530",booked_user_id="670baab543739bce7e2f68cd",booking_id=get_uuid())
#     room_json = room.model_dump()
#
#     conn = pymongo.MongoClient("")
#     db = conn["vfast-client"]
#     rooms = db["Room"]
#     result = rooms.update_one({"room_number":room_no}, {"$addToSet":{"bookings":room_json}})
#     print(result)

# insert_room_bookings()
# insert_room()

# def book_room(check_in,check_out,room_type,pax,user):
#     pipeline = [
#         {"$match"}
#
#
#     ]

def generate_date_series(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    start.astimezone(pytz.timezone('Asia/Kolkata'))
    end.astimezone(pytz.timezone('Asia/Kolkata'))
    date_series = []
    current_date = start
    while current_date <= end:
        date_series.append(current_date)
        current_date += timedelta(days=1)

    return date_series

async def check_availability(start, end, db):
    try:
        dates_to_check = generate_date_series(start, end)
        pipeline = get_check_availability_pipeline(dates_to_check)
        rooms = db["Room"]
        result = await rooms.aggregate(pipeline).to_list()
        return result,None

    except Exception as error:
            return None,JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                     content=error_response(message=str(error)))


async def booking_request(data,user,db):
    try:
        if data["pax"] > MAX_ALLOWED_PERSONS:
            return None,JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content=error_response(message="Online booking is limited to 4 persons"))
        master_data = db["MASTER"]
        room_info = await master_data.find_one({"entity": "ROOM_TYPE", "properties.name": data["room_type"]})
        rooms_required = math.ceil(data["pax"]/int(room_info["properties"]["capacity"]))
        pipeline = get_booking_check_pipeline(data["check_in"],data["check_out"],data["room_type"],rooms_required)
        rooms = db["Room"]
        results = rooms.aggregate(pipeline)
        async for result in results:
            if result.get("num_rooms") < rooms_required:
                return None,JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content=error_response(message="All rooms are booked"))
            else:
                room_info = result.get("rooms")
                if len(room_info) < rooms_required:
                    return None,JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content=error_response(message="All rooms are booked"))
                else:
                    bookings = db["Bookings"]
                    booking_exists = await bookings.find_one({"$and":[{"booked_user_id":ObjectId(user["id"])},
                                               {"check_in": {"$gte": data["check_in"]}},
                                               { "booking_status":{"$in":[BOOKING_STATUS.RESERVED.value,BOOKING_STATUS.CHECKED_IN.value,BOOKING_STATUS.CHECKED_OUT.value,BOOKING_STATUS.PENDING.value]}}]})
                    # if booking_exists:
                    #     return None,JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content=error_response(message="A booking already exists"))

                    booking_id = ObjectId()
                    doc = {
                        "_id":booking_id,
                        "check_in":data["check_in"],
                        "check_out":data["check_out"],
                        "first_name":data["first_name"],
                        "last_name":data["last_name"],
                        "gender":data["gender"],
                        "remarks":data["remarks"],
                        "email":data["email"],
                        "phone_number":data["phone_number"],
                        "booked_user_id":ObjectId(user["id"]),
                        "booked_room_id":[],
                        "booked_room_type":data["room_type"],
                        "booking_status":BOOKING_STATUS.PENDING.value,
                        "purpose_of_visit":data["purpose_of_visit"],
                        "relation_to_user":data["relation_to_user"],
                        "pax":data["pax"],
                        "booking_ts":get_timestamp(),
                    }
                    try:
                        res = Booking(**doc)
                    except Exception as error:
                        return None,JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))

                    await bookings.insert_one(doc)
                    data = {"booking_id":str(booking_id),"num_rooms":rooms_required}
                    return JSONResponse(status_code=status.HTTP_201_CREATED,content=success_response(data=data,message="Booking Requested")),None

    except Exception as error:
        return None,JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))



async def confirm_booking(booking_id,status,user,db,reason=None,rooms_alloted= None):
    rooms = db["Room"]
    bookings = db["Bookings"]
    users = db["Users"]

    booking_info = await bookings.find_one({"_id": ObjectId(booking_id)})
    user_info = await users.find_one({"_id": ObjectId(booking_info["booked_user_id"])})
    if status == "accept":
        booking_status = BOOKING_STATUS.RESERVED.value
        for alloted in rooms_alloted:
            alloted["_id"] = ObjectId(alloted.pop("id"))
        await bookings.update_one({"_id":ObjectId(booking_id)},{"$set":{"booking_status":booking_status,"status_change_ts":get_timestamp(),"booked_room_id":rooms_alloted}})
        rooms_booked = rooms_alloted

        for room in rooms_booked:
            existing = await bookings.find_one({"$and":[{"_id":room["_id"]},{"bookings.booking_id":ObjectId(booking_id)}]})
            if existing:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content=error_response(message="Booking already exists"))
            room_bookings = RoomBookings(check_in = booking_info["check_in"],check_out = booking_info["check_out"],booking_id = booking_info["_id"],booked_user_id=ObjectId(user["id"]))
            await rooms.update_one({"_id":room["_id"]},{"$addToSet":{"bookings":room_bookings.model_dump()}})
            vars = {
                "check_in_date":booking_info["check_in"],"check_out_date":booking_info["check_out"],"number_of_rooms":len(rooms_booked),"number_of_persons":booking_info["pax"],
            }
            error = sendBookingConfirmation(user_info["email"],vars,status="success")
            error = sendBookingConfirmation(booking_info["email"], vars, status="success")

    else:
        booking_status = BOOKING_STATUS.REJECTED.value
        await bookings.update_one({"_id":ObjectId(booking_id)},{"$set":{"booking_status":booking_status,"status_change_ts":get_timestamp()}})
        vars = {"check_in_date":booking_info["check_in"],"check_out_date":booking_info["check_out"],"rejected_reason":reason}
        sendBookingConfirmation(user_info["username"], vars, status="fail")




async def get_bookings_dashboard_helper(req_date,user,db):
    try:
        bookings = db["Bookings"]
        pipe = get_bookings_dashboard_pipeline(req_date)
        results = []
        async for result in bookings.aggregate(pipeline=pipe):
            results.append(result)
        return results, None
    except Exception as error:
        return None,JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))


async def get_dashboard_statistics(user,req_date,db):
    try:
        bookings = db["Bookings"]
        pipe = get_booking_statistics_pipeline(req_date)
        async for result in bookings.aggregate(pipeline=pipe):
            return result, None
        return {
        "total_bookings": 0,
        "total_checkins": 0,
        "total_checkouts": 0,
        "pending_checkins": 0,
        "pending_checkouts": 0,
        "today_bookings": 0,
        "today_completed_checkins": 0,
        "today_completed_checkouts": 0
    },None
    except Exception as error:
        return None, JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))

async def get_dashboard_requests(user,req_date,db):
    try:
        bookings = db["Bookings"]
        pipe = get_requests_dashboard_pipeline(req_date)
        results = []
        async for result in bookings.aggregate(pipeline=pipe):
            results.append(result)
        return results, None
    except Exception as error:
        return None, JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))


async def get_user_bookings(user,db):
    try:
        bookings = db["Bookings"]
        pipe = get_user_bookings_pipeline(user)
        results = []
        async for result in bookings.aggregate(pipeline=pipe):
            result["_id"] = str(result["_id"])
            results.append(result)
        return results, None
    except Exception as error:
        return None, JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))


async def booking_action_helper(booking_id,status,user,db):
    rooms = db["Room"]
    bookings = db["Bookings"]
    users = db["Users"]
    try:
        booking_info = await bookings.find_one({"_id": ObjectId(booking_id)})
        user_info = await users.find_one({"_id": ObjectId(booking_info["booked_user_id"])})
        if status == "check-in":
            booking_status = BOOKING_STATUS.CHECKED_IN.value
            await bookings.update_one({"_id":ObjectId(booking_id)},{"$set":{"booking_status":booking_status,"status_change_ts":get_timestamp()}})
            rooms_booked = booking_info["booked_room_id"]

            for room in rooms_booked:
                await rooms.update_one({"_id":room["_id"]}, {"status":BOOKING_STATUS.CHECKED_IN.value,"status_change_ts":get_timestamp()})
        elif status == "check-out":
            booking_status = BOOKING_STATUS.CHECKED_OUT.value
            await bookings.update_one({"_id":ObjectId(booking_id)},{"$set":{"booking_status":booking_status,"status_change_ts":get_timestamp()}})
            rooms_booked = booking_info["booked_room_id"]

            for room in rooms_booked:
                await rooms.update_one({"_id":room["_id"]}, {"status":"Available","status_change_ts":get_timestamp()})
    except Exception as error:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))



