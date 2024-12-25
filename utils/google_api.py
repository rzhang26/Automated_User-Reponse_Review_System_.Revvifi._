# from googleapiclient.discovery import build
# from google.oauth2.service_account import Credentials
# import os

# SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/forms.responses.readonly']

# def get_google_service():
#     try:
#         print("🔑 Loading credentials.json...")
#         creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
#         print("✅ Credentials loaded successfully.")

#         print("🔄 Initializing Google Sheets service...")
#         sheets_service = build('sheets', 'v4', credentials=creds)
#         print("✅ Google Sheets service initialized.")

#         print("🔄 Initializing Google Forms service...")
#         forms_service = build('forms', 'v1', credentials=creds)
#         print("✅ Google Forms service initialized.")

#         return sheets_service, forms_service

#     except FileNotFoundError:
#         print("❌ Error: credentials.json file not found. Ensure it's in the root folder.")
#     except ValueError as ve:
#         print(f"❌ Error in credentials.json: {ve}")
#     except Exception as e:
#         print(f"❌ General error: {e}")
#     return None, None

# # Testing
# if __name__ == "__main__":
#     sheets, forms = get_google_service()
#     if sheets and forms:
#         print("✅ Services are ready to use!")
#     else:
#         print("❌ Failed to initialize services.")

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
    result = forms_service.forms().responses().list(formId=form_id).execute()
    return result

def update_sheet(sheets_service, spreadsheet_id, data, range_name='Sheet1'):
    body = {'values': data}
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    return result
