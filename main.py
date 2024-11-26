import uvicorn

from Importers.common_imports import *
from Config.fastapi import *
from Helpers.booking import *
from Services.admin_auth import *
from Services.auth import *
from Services.booking import *
from Services.room import *


if __name__ == '__main__':
    uvicorn.run(app=app,host='0.0.0.0', port=8000, log_level='debug')