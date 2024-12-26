from Importers.common_imports import *
from Importers.common_functions import *


def get_check_availability_pipeline(dates):
    return [
        {
            '$addFields': {
                'checkDates': dates
            }
        }, {
        '$unwind': '$checkDates'
    }, {
        '$addFields': {
            'booked': {
                '$filter': {
                    'input': '$bookings',
                    'as': 'bkgs',
                    'cond': {
                        '$and': [
                            {
                                '$lte': [
                                    '$$bkgs.check_in', '$checkDates'
                                ]
                            }, {
                                '$gt': [
                                    '$$bkgs.check_out', '$checkDates'
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'isBooked': {
                '$gt': [
                    {
                        '$size': '$booked'
                    }, 0
                ]
            }
        }
    }, {
        '$group': {
            '_id': {
                'roomType': '$room_type',
                'checkDate': '$checkDates'
            },
            'bookedRooms': {
                '$sum': {
                    '$cond': [
                        '$isBooked', 1, 0
                    ]
                }
            },
            'totalRooms': {
                '$sum': 1
            }
        }
    }, {
        '$project': {
            '_id': 0,
            'roomType': '$_id.roomType',
            'checkDate': '$_id.checkDate',
            'availableRooms': {
                '$subtract': [
                    '$totalRooms', '$bookedRooms'
                ]
            }
        }
    }, {
        '$group': {
            '_id': '$checkDate',
            'roomAvailability': {
                '$push': {
                    'roomType': '$roomType',
                    'availableRooms': '$availableRooms'
                }
            }
        }
    }, {
        '$project': {
            '_id': 0,
            'checked_for_date':{ "$dateToString": { "format": "%Y-%m-%d", "date": "$_id" } },
            'roomAvailability': 1
        }
    }, {
        '$sort': {
            'checked_for_date': 1
        }
    }
    ]


def get_booking_check_pipeline(check_in,check_out,type,rooms):
    return [
    {
        '$match': {
            'room_type': type
        }
    }, {
        '$addFields': {
            'check_in': check_in,
            'check_out': check_out,
            'num_rooms': rooms
        }
    }, {
        '$addFields': {
            'fltrd_bookings': {
                '$filter': {
                    'input': '$bookings',
                    'as': 'res',
                    'cond': {
                        '$or': [
                            {
                                '$and': [
                                    {
                                        '$gte': [
                                            '$check_in', '$$res.check_in'
                                        ]
                                    }, {
                                        '$lte': [
                                            '$check_in', '$$res.check_out'
                                        ]
                                    }
                                ]
                            }, {
                                '$and': [
                                    {
                                        '$gte': [
                                            '$check_out', '$$res.check_in'
                                        ]
                                    }, {
                                        '$lte': [
                                            '$check_out', '$$res.check_out'
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }, {
        '$match': {
            'fltrd_bookings': {
                '$eq': []
            }
        }
    }, {
        '$project': {
            '_id': 1,
            'room_number': 1,
            'room_type': 1
        }
    }, {
        '$facet': {
            'count': [
                {
                    '$count': 'rooms'
                }
            ],
            'rooms': [
                {
                    '$project': {
                        '_id': 1,
                        'room_number': 1,
                    }
                }, {
                    '$limit': rooms
                }
            ]
        }
    }, {
        '$unwind': {
            'path': '$count'
        }
    }, {
        '$project': {
            "_id":1,
            'num_rooms': '$count.rooms',
            'rooms': 1
        }
    }
]


def get_bookings_dashboard_pipeline(req_date):
    return [
        {
            '$match': {
                '$and': [
                    {
                        'check_in': {'$lte': req_date},
                    }, {
                        'check_out': {'$gte': req_date},
                    }
                ]
            }
        }, {
        '$project': {
            '_id': {
                '$toString': '$_id'
            },
            'first_name': 1,
            'last_name': 1,
            'gender': 1,
            'check_in': 1,
            'check_out': 1,
            'phone_number': 1,
            'booked_room_type': 1,
            'room_number': '$booked_room_id.room_number',
            'pax': 1,
            'booking_status': 1
        }
    }
]


def get_booking_statistics_pipeline(req_date):
    return [
    {
        # Match bookings where the given date falls between check-in and check-out
        '$match': {
            '$and': [
                { 'check_in': { '$lte': req_date } },
                { 'check_out': { '$gte': req_date } }
            ]
        }
    },
    {
        # Add computed fields for various booking states
        '$addFields': {
            'is_checkin_date': {
                '$eq': ['$check_in', req_date]
            },
            'is_checkout_date': {
                '$eq': ['$check_out', req_date]
            },
            'pending_checkin': {
                '$cond': [
                    {
                        '$and': [
                            { '$eq': ['$check_in', req_date] },
                            { '$eq': ['$booking_status', BOOKING_STATUS.RESERVED.value] }
                        ]
                    }, 1, 0
                ]
            },
            'pending_checkout': {
                '$cond': [
                    {
                        '$and': [
                            { '$eq': ['$check_out', req_date] },
                            { '$eq': ['$booking_status', BOOKING_STATUS.CHECKED_IN.value] }
                        ]
                    }, 1, 0
                ]
            },
            'completed_checkin': {
                '$cond': [
                    {
                        '$and': [
                            { '$eq': ['$check_in', req_date] },
                            { '$eq': ['$booking_status', BOOKING_STATUS.CHECKED_IN.value] }
                        ]
                    }, 1, 0
                ]
            },
            'completed_checkout': {
                '$cond': [
                    {
                        '$and': [
                            { '$eq': ['$check_out', req_date] },
                            { '$eq': ['$booking_status', BOOKING_STATUS.CHECKED_OUT.value] }
                        ]
                    }, 1, 0
                ]
            },
            # Add a field to identify if the booking is created today
            'is_today_booking': {
                '$eq': [
                    { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$booking_ts' } },
                    req_date
                ]
            }
        }
    },
    {
        # Group data to calculate totals
        '$group': {
            '_id': None,
            'total_bookings': { '$sum': 1 },
            'total_checkins': { '$sum': '$completed_checkin' },
            'total_checkouts': { '$sum': '$completed_checkout' },
            'pending_checkins': { '$sum': '$pending_checkin' },
            'pending_checkouts': { '$sum': '$pending_checkout' },
            'today_bookings': {
                '$sum': {
                    '$cond': ['$is_today_booking', 1, 0]
                }
            },
            'today_completed_checkins': {
                '$sum': {
                    '$cond': ['$completed_checkin', 1, 0]
                }
            },
            'today_completed_checkouts': {
                '$sum': {
                    '$cond': ['$completed_checkout', 1, 0]
                }
            }
        }
    },
    {
        # Project only the required fields
        '$project': {
            '_id': 0,
            'total_bookings': 1,
            'total_checkins': 1,
            'total_checkouts': 1,
            'pending_checkins': 1,
            'pending_checkouts': 1,
            'today_bookings': 1,
            'today_completed_checkins': 1,
            'today_completed_checkouts': 1
        }
    }
]


def get_requests_dashboard_pipeline(req_date):
    return [
        {
            '$match': {
                '$and': [
                    {
                        'check_in': {'$lte': req_date},
                    }, {
                        'booking_status': {'$nin': [BOOKING_STATUS.CHECKED_IN.value, BOOKING_STATUS.CHECKED_OUT.value]},
                    }
                ]
            }
        },
        {
            '$sort': {
                'booking_ts': -1
            }
        }
        ,
        {
        '$project': {
            '_id': {
                '$toString': '$_id'
            },
            'first_name': 1,
            'last_name': 1,
            'gender': 1,
            'check_in': 1,
            'check_out': 1,
            'phone_number': 1,
            'booked_room_type': 1,
            'room_number': '$booked_room_id.room_number',
            'pax': 1,
            'booking_status': 1
        }
    }
]


def get_user_bookings_pipeline(user):
    return [
    {
        '$match': {
            'booked_user_id': ObjectId(user["id"])
        }
    }, {
        '$addFields': {
            'days_to_checkin': {
                '$abs': {
                    '$dateDiff': {
                        'startDate': '$$NOW',
                        'endDate': {
                            '$dateFromString': {
                                'dateString': '$check_in'
                            }
                        },
                        'unit': 'day'
                    }
                }
            }
        }
    }, {
        '$sort': {
            'days_to_checkin': 1
        }
    }, {
        '$project': {
            '_id': 1,
            'check_in': 1,
            'check_out': 1,
            'booked_room_type': 1,
            'booking_status': 1,
            'pax': 1,
            'number_of_rooms': {
                '$size': '$booked_room_id'
            }
        }
    },
        {"$limit":1}
]


def get_all_room_status_pipeline(req_date):
    return [
        {
            '$addFields': {
                'given_date': {
                    '$dateFromString': {
                        'dateString': req_date
                    }
                }
            }
        }, {
        '$project': {
            'room_number': 1,
            'room_type': 1,
            'status': 1,
            'capacity': 1,
            'bookings': 1,
            'is_booked': {
                '$anyElementTrue': {
                    '$map': {
                        'input': '$bookings',
                        'as': 'booking',
                        'in': {
                            '$and': [
                                {
                                    '$lte': [
                                        '$$booking.check_in', '$given_date'
                                    ]
                                }, {
                                    '$gt': [
                                        '$$booking.check_out', '$given_date'
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'status': {
                '$cond': {
                    'if': '$is_booked',
                    'then': 'Booked',
                    'else': 'Available'
                }
            }
        }
    }, {
        '$project': {
            '_id': {"$toString": "$_id"},
            'room_number': 1,
            'room_type': 1,
            'status': 1
        }
    }
    ]


def get_rooms_pipeline(type,check_in,check_out):
    return [
    {
        '$match': {
            'room_type': type
        }
    }, {
        '$addFields': {
            'check_in': check_in,
            'check_out': check_out
        }
    }, {
        '$addFields': {
            'fltrd_bookings': {
                '$filter': {
                    'input': '$bookings',
                    'as': 'res',
                    'cond': {
                        '$or': [
                            {
                                '$and': [
                                    {
                                        '$gte': [
                                            '$check_in', '$$res.check_in'
                                        ]
                                    }, {
                                        '$lte': [
                                            '$check_in', '$$res.check_out'
                                        ]
                                    }
                                ]
                            }, {
                                '$and': [
                                    {
                                        '$gte': [
                                            '$check_out', '$$res.check_in'
                                        ]
                                    }, {
                                        '$lte': [
                                            '$check_out', '$$res.check_out'
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }, {
        '$match': {
            'fltrd_bookings': {
                '$eq': []
            }
        }
    }, {
        '$project': {
            '_id': {"$toString":"$_id"},
            'room_number': 1,
            'room_type': 1
        }
    }

]


async def get_room_type_dd_pipeline():
    return [
        {"$match":{"entity":"ROOM_TYPE"}},
        {"$project":{"_id": 0,"type":"$properties.name"}}
    ]