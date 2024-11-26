import random
import bson
import pymongo
from Config.constants import MAX_ALLOWED_STAY_DURATION, MAX_ALLOWED_PERSONS
from Helpers.email import sendBookingConfirmation
from Importers.common_imports import *
from Importers.common_functions import *
from Config.models import *
from Helpers.mongo import get_all_room_status_pipeline

async def get_rooms(req_date,db):
    try:
        bookings = db["Room"]

        pipe = get_all_room_status_pipeline(req_date)

        results = []
        async for result in bookings.aggregate(pipeline=pipe):
            results.append(result)

        return results, None
    except Exception as error:
        return None, error

