import os
import base64
import json
import pytz
import re
import random
import math
from datetime import datetime,timedelta

from fastapi import FastAPI,Request,Response,HTTPException,status,Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional,Any,Literal


from jose import jwt,JWTError


from bson import ObjectId
from pymongo import InsertOne,UpdateOne





from Config.fastapi import app
from Config.constants import BOOKING_STATUS