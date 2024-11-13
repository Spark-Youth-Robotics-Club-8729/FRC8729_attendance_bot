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
service = build('sheets', 'v4', credentials=creds)

def writeToGoogleSheet(data, raw, name):
    SHEET_NAME = "Overall Timesheet Summary"
    sheet_range = f'{SHEET_NAME}!A1:Z'
    
    # fetch all values from sheet (checking which cells they occupy)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEETID,
        range=sheet_range
    ).execute()
    all_values = result.get('values', [])

    # find next available row
    next_row = len(all_values) + 1

    # construct range name for next available row
    range_name = f'{SHEET_NAME}!A{next_row}'

    try:
        # prepare data (list of rows (each individual row is a list))
        body = {
            'values': data  # data is a list of lists where each list is a row
        }

        if raw:
            # update spreadsheet
            result = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEETID,
                range=range_name,
                valueInputOption="RAW",
                body=body
            ).execute()
            print(f"Data written to sheet: {result}")
        else:
            NEW_SHEET_NAME = data[0][0]
            person_hours = f"='{name}'!B34"
            data[0].append(person_hours)
            body = {
                'values': data
            }
        
            result = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEETID,
                range=range_name,
                valueInputOption="USER_ENTERED", #to make it a formula
                body=body
            ).execute()
            print(f"Data written to sheet: {result}")
        
    except HttpError as err:
        print(f"Error: {err}")


# CALENDAR TIMESHEET FUNCTION
def createNewCalendar(name):
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
                        "title": name,
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

    # update new sheet with calendar
    update_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": f"'{name}'!A1:M35", 
                "majorDimension": "ROWS",
                "values": values
            }
        ]
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEETID,
        body=update_body
    ).execute()

    # new sheet if want to make further updates
    new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

    addHyperLink(new_sheet_id, name)


def addHyperLink(new_sheet_id, name):
    link = f'=HYPERLINK("https://docs.google.com/spreadsheets/d/{SPREADSHEETID}/edit#gid={new_sheet_id}", {name})'
    writeToGoogleSheet([[link]], False, name)

createNewCalendar("1")