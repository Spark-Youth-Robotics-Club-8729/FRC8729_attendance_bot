import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# GETTING VALUES FROM .env
load_dotenv(".env")
# spreadsheet id for accessing api
SPREADSHEETID: str = os.getenv("SPREADSHEETID")

# load credentials for google sheet
creds = Credentials.from_service_account_file(
    'timesheet-2024-2025-6a701c48c246.json',
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
# where to start making sheet
RANGE_NAME = 'Sheet1!A1'

service = build('sheets', 'v4', credentials=creds)

def write_to_google_sheet(data):
    try:
        # prepare data (list of rows (each individual row is a list))
        body = {
            'values': data  # data is a list of lists where each list is a row
        }

        # update spreadsheet
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEETID,
            range=RANGE_NAME,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"Data written to sheet: {result}")
    except HttpError as err:
        print(f"Error: {err}")

# TESTING DATA FOR RN
users_data = [
    ["Alice", "Software", "Clocked In"],
    ["Bob", "Mechanical", "Clocked Out"],
    ["Charlie", "Business", "Clocked In"]
]

#write_to_google_sheet(users_data)


# CALENDAR TIMESHEET FUNCTION
def create_new_calendar():
    calendar_header = [
        ["Date", "November, 2024", "December, 2024", "January, 2025", "February, 2025", "March, 2025", 
        "April, 2025", "May, 2025", "June, 2025", "July, 2025", "August, 2025", 
        "September, 2025", "October, 2025"]
    ]
    days_of_month = [[str(day)] + [""] * 12 for day in range(1, 32)]
    totals_row = ["TOTAL"] + [f"=SUM({chr(66 + i)}2:{chr(66 + i)}32)" for i in range(12)]
    yearly_total_row = ["Yearly Total", "=SUM(B33:M33)"] + [""] * 11

    values = calendar_header + days_of_month + [totals_row, yearly_total_row]

    # dictionary specifying list of instructions
        # create new sheet
    sheet_body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": "Work Hours Calendar",
                        "gridProperties": {
                            "rowCount": len(values) + 10,
                            "columnCount": 23
                        }
                    }
                }
            }
        ]
    }
    # batch update to make multiple requests/operations
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEETID,
        body=sheet_body
    ).execute()

    # new sheet if want to make further updates
    # new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

    # update new sheet with calendar
    update_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": "Work Hours Calendar!A1:M35", 
                "majorDimension": "ROWS",
                "values": values
            }
        ]
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEETID,
        body=update_body
    ).execute()