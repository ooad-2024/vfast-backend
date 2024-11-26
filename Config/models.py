import uuid
from datetime import datetime
from typing import Literal, List, Any
from pydantic import BaseModel


class User(BaseModel):
    username: str
    password: str
    type : str


class RoomBookings(BaseModel):
    check_in : datetime
    check_out : datetime
    booked_user_id: Any
    booking_id : Any

class Room(BaseModel):
    room_number: str
    room_type: Literal["Standard","Deluxe","Executive"]
    status: Literal["Checked-In","Reserved","Checked-Out","Available"]
    capacity: int
    bookings :  List[RoomBookings]


class BookingLog(BaseModel):
    action: Literal["Checked-In","Checked-Out","Reserved","Settled","Cancelled","Pending"]
    timestamp: datetime


class PaymentInformation(BaseModel):
    amount_paid : float
    amount_due : float


class Booking(BaseModel):
    _id : Any
    booked_user_id : Any
    booked_room_id : List[Any] = None
    booked_room_type : str
    booking_status : Literal["Checked-In","Checked-Out","Reserved","Settled","Cancelled","Pending"]
    check_in : datetime
    check_out : datetime
    pax : int
    # booking_log:List[str]
    booking_ts: datetime
    # payment :List
    # bill : List



