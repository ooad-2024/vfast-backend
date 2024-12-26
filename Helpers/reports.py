from io import StringIO

import pandas as pd

from Importers.common_imports import *
from Importers.common_functions import *
from Config.models import *

# async def get_occupancy_report(start,end,format="csv"):
#     data = [{"date":"2024-12-01","occupied_no":34,"empty_no":12,"check-ins":11,"check-outs":1}]
#     json_data = json.dumps(data)
#     df = pd.read_json(json_data)
#     csv_data = StringIO()
#     df.to_csv(csv_data,index=False)
#     return csv_data.getvalue()


def json_to_csv(json_obj):
    """
    Converts a JSON object to a CSV file-like object.

    Parameters:
        json_obj (list of dict): A list of dictionaries representing JSON data.

    Returns:
        StringIO: A file-like object containing the CSV data.
    """
    if not isinstance(json_obj, list) or not all(isinstance(item, dict) for item in json_obj):
        raise ValueError("Input must be a list of dictionaries.")

    # Create an in-memory file-like object
    file_obj = StringIO()
    writer = csv.writer(file_obj)

    # Write the header row
    if json_obj:
        header = json_obj[0].keys()
        writer.writerow(header)

        # Write the data rows
        for entry in json_obj:
            writer.writerow(entry.values())

    file_obj.seek(0)  # Reset file pointer to the beginning
    return file_obj

