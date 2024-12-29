import datetime
from utils.google_api import get_google_service
import os

def generate_weekly_summary():
    """
    Generate a weekly performance summary from Google Sheets data.
    Returns:
        dict: {
            "report": "<Weekly Summary Text>",
            "has_strikes": bool
        }
    """
    try:
        sheets, _ = get_google_service()
        sheet_data = sheets.spreadsheets().values().get(
            spreadsheetId=os.getenv('SPREADSHEET_ID'),
            range='Sheet1'
        ).execute()

        rows = sheet_data.get('values', [])[1:]  # Skip header row

        summary = {
            "total_hours": 0,
            "total_clients": 0,
            "total_volunteers": 0,
            "top_performer": None,
            "warnings_issued": 0
        }

        for row in rows:
            try:
                name, role, score, effort, strike, feedback = row[1:7]
                summary["total_hours"] += int(score) if role == "Developer" else 0
                summary["total_clients"] += int(score) if role == "Outreach & Social Media" else 0
                if strike == "Yes":
                    summary["warnings_issued"] += 1
            except (ValueError, IndexError):
                continue

        has_strikes = summary["warnings_issued"] > 0

        report = f"""
        Weekly Performance Summary ({datetime.date.today()}):
        - Total Hours Worked: {summary['total_hours']}
        - Total Clients Recruited: {summary['total_clients']}
        - Total Volunteers Recruited: {summary['total_volunteers']}
        - Warnings Issued: {summary['warnings_issued']}
        """
        
        print("✅ Weekly summary generated.")
        return {
            "report": report,
            "has_strikes": has_strikes
        }

    except Exception as e:
        print(f"❌ Error generating weekly summary: {e}")
        return {
            "report": "Failed to generate summary.",
            "has_strikes": False
        }


# import datetime
# from utils.google_api import get_google_service
# import os

# def generate_weekly_summary():
#     """
#     Generate a weekly performance summary from Google Sheets data.
#     """
#     try:
#         sheets, _ = get_google_service()
#         sheet_data = sheets.spreadsheets().values().get(
#             spreadsheetId=os.getenv('SPREADSHEET_ID'),
#             range='Sheet1'
#         ).execute()

#         rows = sheet_data.get('values', [])[1:]  # Skip header row

#         summary = {
#             "total_hours": 0,
#             "total_clients": 0,
#             "total_volunteers": 0,
#             "top_performer": None,
#             "warnings_issued": 0
#         }

#         for row in rows:
#             try:
#                 name, role, score, effort, strike, feedback = row[1:7]
#                 summary["total_hours"] += int(score) if role == "Developer" else 0
#                 summary["total_clients"] += int(score) if role == "Outreach & Social Media" else 0
#                 if strike == "Yes":
#                     summary["warnings_issued"] += 1
#             except ValueError:
#                 continue

#         report = f"""
# Weekly Performance Summary ({datetime.date.today()}):
# - Total Hours Worked: {summary['total_hours']}
# - Total Clients Recruited: {summary['total_clients']}
# - Total Volunteers Recruited: {summary['total_volunteers']}
# - Warnings Issued: {summary['warnings_issued']}
#         """
#         print("✅ Weekly summary generated.")
#         return report

#     except Exception as e:
#         print(f"❌ Error generating weekly summary: {e}")
#         return None

# feels off: acccounting data for roles or for individuals?
# check later...