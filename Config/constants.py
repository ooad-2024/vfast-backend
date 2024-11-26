from enum import Enum

class BOOKING_STATUS(Enum):
    PENDING = "Pending"
    RESERVED = "Reserved"
    CHECKED_IN = "CheckedIn"
    CHECKED_OUT = "CheckedOut"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

class ROLES(Enum):
    USER = "User"
    ADMIN = "Admin"
    SUPER_ADMIN = "SuperAdmin"
    ADMINS = ("Admin","SuperAdmin")
    ANY = ("Admin","SuperAdmin","User")



MAX_ALLOWED_PERSONS = 4
MAX_ALLOWED_STAY_DURATION = 3