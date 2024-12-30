from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

SCOPES = SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/forms.responses.readonly']


def get_google_service():
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=creds)
    forms_service = build('forms', 'v1', credentials=creds)
    return sheets_service, forms_service

def fetch_form_data(forms_service, form_id):
    try:
        print("🔄 Fetching data from Google Forms API...")
        result = forms_service.forms().responses().list(formId=form_id).execute()
        print("📝 Google Forms API Response:", result)  # <-- Add this line
        return result
    except Exception as e:
        print(f"❌ Error fetching form data: {e}")
        return None

# def update_sheet(sheets_service, spreadsheet_id, data, range_name='Sheet1'):
#     body = {'values': data}
#     result = sheets_service.spreadsheets().values().update(
#         spreadsheetId=spreadsheet_id,
#         range=range_name,
#         valueInputOption='RAW',
#         body=body
#     ).execute()
#     return result

# def update_sheet(sheets, spreadsheet_id, data):
#     """
#     Append data to Google Sheets without overwriting.
#     """
#     if isinstance(data, list):
#         sheets.spreadsheets().values().append(
#             spreadsheetId=spreadsheet_id,
#             range='Sheet1!A:H',
#             valueInputOption='USER_ENTERED',
#             insertDataOption='INSERT_ROWS',
#             body={'values': data}
#         ).execute()
#     else:
#         raise ValueError("Data passed to update_sheet must be a list of lists.")



def update_sheet(sheets, spreadsheet_id, data):
    """
    Append data to Google Sheets without overwriting.
    """
    if not isinstance(data, list):
        raise ValueError("❌ Data passed to update_sheet must be a list of lists.")

    google_values = sheets.spreadsheets().values()
    if not hasattr(google_values, 'append'):
        raise AttributeError("❌ Google Sheets API 'values' object does not have 'append' method.")

    google_values.append(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A:H',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': data}
    ).execute()
