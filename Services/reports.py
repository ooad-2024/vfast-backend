from Importers.common_imports import *
from Importers.common_functions import *
from Config.models import *
from Helpers.reports import json_to_csv


_PATH_PREFIX = "/api/v1/reports"
@app.get(_PATH_PREFIX + "/occupancy",tags=["Reports"])
def get_occupancy_report(start:str=None,end:str=None):
    try:
        json_obj = [{"date": "2024-12-01", "occupied_no": 34, "empty_no": 12, "check-ins": 11, "check-outs": 1}]
        csv_file = json_to_csv(json_obj)
        response = StreamingResponse(iter([csv_file.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=occupancy-{start}-to-{end}.csv"
        return response
    except Exception as e:

        return Response(content=str(e), status_code=400)


@app.get(_PATH_PREFIX + "/logs",tags=["Reports"])
def get_logs_report(start:str=None,end:str=None):
    try:
        json_obj = [{"date": "2024-12-01", "occupied_no": 34, "empty_no": 12, "check-ins": 11, "check-outs": 1}]
        csv_file = json_to_csv(json_obj)
        response = StreamingResponse(iter([csv_file.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=logs-{start}-to-{end}.csv"
        return response
    except Exception as e:
        return Response(content=str(e), status_code=400)