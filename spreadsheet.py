import os
import datetime
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
    "timesheet-2024-2025-6a701c48c246.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
service = build("sheets", "v4", credentials=creds)


# FUNCTIONS

def highestRowOriginalSheet(data, name):
    SHEET_NAME = "Overall Timesheet Summary"
    sheet_range = f"{SHEET_NAME}!A1:Z"

    # fetch all values from sheet (checking which cells they occupy)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEETID, range=sheet_range)
        .execute()
    )
    all_values = result.get("values", [])

    # find next available row
    next_row = len(all_values) + 1

    # construct range name for next available row
    range_name = f"{SHEET_NAME}!A{next_row}"

    try:
        # prepare data (list of rows (each individual row is a list))
        body = {"values": data}  # data is a list of lists where each list is a row

        person_hours = f"='{name}'!B34"
        data[0].append(person_hours)
        body = {"values": data}

        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=SPREADSHEETID,
                range=range_name,
                valueInputOption="USER_ENTERED",  # to make it a formula
                body=body,
            )
            .execute()
        )
        print(f"Data written to sheet: {result}")
    except HttpError as err:
        print(f"Error: {err}")


# CALENDAR TIMESHEET FUNCTION
def createNewCalendar(name, value):
    SHEET_NAME = "Overall Timesheet Summary"
    column_range = f"{SHEET_NAME}!A2:A"  # no A1 because header

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=SPREADSHEETID,
            range=column_range,
            valueRenderOption="UNFORMATTED_VALUE",
        )
        .execute()
    )
    column_values = result.get("values", [])

    # check if exists in first column (name should match)
    calendar_exists = False
    for i, row in enumerate(column_values):
        if row and row[0] == name:
            print(row, row[0])
            cell_location = (
                f"{SHEET_NAME}!A{i + 2}"  # +2 to account for header and 0-based index
            )
            print(f"Name '{name}' found in cell {cell_location}")
            calendar_exists = True

    print(calendar_exists)
    if calendar_exists:
        addToCalendar(name, value)
    else:
        try:
            calendar_header = [
                [
                    "Date",
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]
            ]
            days_of_month = [[str(day)] + [""] * 12 for day in range(1, 32)]
            totals_row = ["TOTAL"] + [
                f"=SUM({chr(66 + i)}2:{chr(66 + i)}32)" for i in range(12)
            ]
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
                                    "columnCount": 23,
                                },
                            }
                        }
                    }
                ]
            }
            # batch update to make multiple requests/operations
            response = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=SPREADSHEETID, body=sheet_body)
                .execute()
            )

            # update new sheet with calendar
            update_body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"'{name}'!A1:M35",
                        "majorDimension": "ROWS",
                        "values": values,
                    }
                ],
            }
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEETID, body=update_body
            ).execute()

            # new sheet if want to make further updates
            new_sheet_id = response["replies"][0]["addSheet"]["properties"]["sheetId"]

            addHyperLink(new_sheet_id, name)

            addToCalendar(name, value)

        except HttpError as err:
            print(f"Error: {err}")


def addHyperLink(new_sheet_id, name):
    link = f'=HYPERLINK("https://docs.google.com/spreadsheets/d/{SPREADSHEETID}/edit#gid={new_sheet_id}", "{name}")'
    highestRowOriginalSheet([[link]], name)


def determineCurrentDay():
    try:
        today = datetime.date.today()
        day_index = today.day  # 1-31 for the day
        month_index = today.month  # 1-12 for the month
        print(today, day_index, month_index)
        return day_index, month_index
    except Exception as e:
        print(f"Error: {e}")
        return None, None


def addToCalendar(name, value):
    # determine current day and month
    day_index, month_index = determineCurrentDay()
    if day_index is None or month_index is None:
        print("Error determining current day or month")
        return

    # map month_index (1-12) to correct column in spreadsheet (B-M)
    col = month_index + 1 
    row = day_index + 1

    # convert column index to letter
    col_letter = chr(64 + col)  

    cell_range = f"'{name}'!{col_letter}{row}"

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEETID, range=cell_range)
            .execute()
        )
        current_value = float(
            result.get("values", [[]])[0][0] if result.get("values") else 0
        )
    except (ValueError, IndexError, HttpError):
        current_value = 0  # Default to 0 if no value or an error occurs

    new_value = current_value + value
    update_body = {"values": [[new_value]]}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEETID,
        range=cell_range,
        valueInputOption="RAW",  # use RAW to input value directly
        body=update_body,
    ).execute()

    print(f"Updated cell {cell_range} with value: {new_value}")


#createNewCalendar("Lucas", 1)

# determineCurrentDay()
