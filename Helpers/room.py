import random
import bson
import pymongo
from Config.constants import MAX_ALLOWED_STAY_DURATION, MAX_ALLOWED_PERSONS
from Helpers.email import sendBookingConfirmation
from Importers.common_imports import *
from Importers.common_functions import *
from Config.models import *
from Helpers.mongo import get_all_room_status_pipeline, get_rooms_pipeline


async def get_rooms_status(req_date, db):
    try:
        rooms = db["Room"]

        pipe = get_all_room_status_pipeline(req_date)

        results = []
        async for result in rooms.aggregate(pipeline=pipe):
            results.append(result)

        return results, None
    except Exception as error:
        return None, JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))


async def get_rooms(type, check_in, check_out, db):
    try:
        rooms = db["Room"]
        pipe = get_rooms_pipeline(type, check_in, check_out)
        results = []
        async for result in rooms.aggregate(pipeline=pipe):
            results.append(result)
        return results, None

    except Exception as error:
        return None, JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,content=error_response(message=str(error)))
