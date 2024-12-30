from flask import Flask, jsonify
from utils.google_api import get_google_service, fetch_form_data
from utils.scoring import calculate_score
from utils.gemini_api import analyze_activity_with_gemini
from utils.notifications import send_discord_notification, send_email_notification
from utils.reports import generate_weekly_summary
import os
from dotenv import load_dotenv
import schedule
import time
import threading

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)


@app.route('/')
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "success", "message": "Backend is up and running!"})


@app.route('/process', methods=['GET'])
def process_data():
    """
    Fetch form responses, analyze activities using Gemini AI,
    calculate scores dynamically, and update Google Sheets.
    """
    try:
        # Initialize Google services
        sheets, forms = get_google_service()
        form_data = fetch_form_data(forms, os.getenv('FORM_ID'))

        # Fetch existing timestamps and their corresponding rows
        sheet_data = sheets.spreadsheets().values().get(
            spreadsheetId=os.getenv('SPREADSHEET_ID'),
            range='Sheet1!A:H'  # Fetch all relevant columns
        ).execute()

        existing_rows = sheet_data.get('values', [])[1:]  # Skip header row
        existing_timestamps = {row[0]: index + 2 for index, row in enumerate(existing_rows)}

        processed_data = []  # Collect new data for appending

        for entry in form_data.get('responses', []):
            timestamp = entry.get('createTime', '')  # Get timestamp from form submission
            
            # Skip already processed timestamps
            if timestamp in existing_timestamps:
                print(f"🔄 Skipping already processed timestamp: {timestamp}")
                continue
            
            # Extract basic data from form
            name = entry.get('answers', {}).get('40836d3c', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'Unknown')
            role = entry.get('answers', {}).get('37580eae', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'Undefined')
            activity = entry.get('answers', {}).get('4c26168e', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'No activity')
            
            print(f"📝 Name: {name}")
            print(f"🎭 Role: {role}")
            print(f"📝 Activity Data Sent to Gemini: {activity}")

            # Analyze activity with Gemini
            metrics = analyze_activity_with_gemini(activity)
            clients = metrics['clients']
            volunteers = metrics['volunteers']
            hours = metrics['hours']
            effort = metrics['effort']

            # Calculate score dynamically
            result = calculate_score(
                role=role,
                clients=clients, 
                volunteers=volunteers, 
                hours=hours, 
                effort=effort,
                gemini_feedback=activity
            )
            score = result['score']
            strike = result['strike']

            feedback_summary = (
                f"Clients: {clients}, "
                f"Volunteers: {volunteers}, "
                f"Hours: {hours}, "
                f"Effort: {'Yes' if effort else 'No'}"
            )

            # Append new data to the processed_data list
            processed_data.append([
                timestamp,
                name,
                role,
                score,
                "Yes" if effort else "No",
                "Yes" if strike else "No",
                "No",  # Default Strike Notified value
                feedback_summary
            ])

        if processed_data:
            google_values = sheets.spreadsheets().values()
            if not hasattr(google_values, 'append'):
                raise AttributeError("❌ Google Sheets API 'values' object does not have 'append' method.")

            google_values.append(
                spreadsheetId=os.getenv('SPREADSHEET_ID'),
                range='Sheet1!A:H',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': processed_data}
            ).execute()
            print("✅ New submissions processed and added to Google Sheets without overwriting existing rows.")
        else:
            print("🔄 No new submissions found to process.")

        return jsonify({"status": "success", "message": "New submissions processed successfully"})

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)})

def send_strike_report():
    """
    Check for new strikes and send notifications only for new ones.
    """
    try:
        sheets, _ = get_google_service()
        sheet_data = sheets.spreadsheets().values().get(
            spreadsheetId=os.getenv('SPREADSHEET_ID'),
            range='Sheet1!A:H'
        ).execute()

        rows = sheet_data.get('values', [])[1:]  # Skip header row

        # Track already processed timestamps to prevent double processing
        processed_timestamps = set()

        for index, row in enumerate(rows):
            try:
                # Safeguard against IndexError if row has fewer columns
                if len(row) < 8:
                    continue

                timestamp, name, role, score, effort, strike, notified, feedback = row[0:8]

                # Skip if already processed in the current run
                if timestamp in processed_timestamps:
                    continue

                if strike == "Yes" and notified != "Yes":
                    # Send Discord notification for new strikes
                    message = f"🚨 **New Strike Alert**:\n- **Name:** {name}\n- **Role:** {role}\n- **Score:** {score}\n- **Effort:** {effort}"
                    send_discord_notification({"report": message, "has_strikes": True})
                    print(f"✅ Notification sent for strike detected: {name}")
                    
                    # Update 'Strike Notified' column
                    google_values = sheets.spreadsheets().values()
                    if not hasattr(google_values, 'update'):
                        raise AttributeError("❌ Google Sheets API 'values' object does not have an 'update' method.")

                    google_values.update(
                        spreadsheetId=os.getenv('SPREADSHEET_ID'),
                        range=f"Sheet1!G{index + 2}",  # Column G for 'Strike Notified'
                        valueInputOption='USER_ENTERED',
                        body={'values': [["Yes"]]}
                    ).execute()
                    print(f"✅ Strike notified updated for: {name}")
                    
                    # Add timestamp to the processed set
                    processed_timestamps.add(timestamp)

            except (ValueError, IndexError) as e:
                print(f"❌ Row Processing Error: {e}")
                continue

        if processed_timestamps:
            print("✅ Strike notifications updated successfully.")
        else:
            print("🔄 No new strike notifications were processed this time.")

    except Exception as e:
        print(f"❌ Error in send_strike_report: {e}")

def send_weekly_report():
    """
    Generate and send a weekly performance summary via email.
    """
    try:
        report = generate_weekly_summary()
        if report:
            send_email_notification(
                subject="Weekly Performance Report",
                body=report['report']
            )
            print("✅ Weekly performance report sent successfully via email.")
        else:
            print("❌ Failed to generate weekly performance report.")
    except Exception as e:
        print(f"❌ Error in send_weekly_report: {e}")


def run_flask():
    """
    Start the Flask server without debug mode in a thread-safe way.
    """
    app.run(host='127.0.0.1', port=5000, use_reloader=False)


if __name__ == '__main__':
    threading.Thread(target=run_flask).start()

    schedule.every(1).minutes.do(send_strike_report)
    schedule.every().friday.at("17:30").do(send_weekly_report)

    print("✅ Schedulers initialized. Strike checks run every minute, and weekly reports every Friday at 17:30.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("🛑 Scheduler stopped by user.")




# feedback:

# issue 1 (major): Formatting Issue
# ask for question format regarding google form responses
# ask for recorded data and feedback format regarding google sheets 
# data does NOT seem to have been processed. 
# gemini to sheets connection is good,
# forms to gemini data gathering may be an issue at play here (possibly) 
# - RESOLVED

# issue 2 (minor): Gemini Response to Google Sheets Issue
# first form and data fetch and update onto sheets function without issue
# second form and beyond seem to have issues  (test first)
# - RESOLVED, not a problem anymore

# issue 3 (major): Hosting issue
# received the message for terminal: " WARNING: This is a development server. 
# Do not use it in a production deployment. 
# Use a production WSGI server instead. "
# will be resolved in later milestones when transfering application's
# hosting envrioment from locally onto github pages 
# to be solved...

# issue 4 (major): Scoring issue
# scores not properly calculated 
# something likely wrong with scoring.py's intake of the hours worked, 
# clients, as well as volunteers recruited arguments 
# SHOULD have values initiated via gemini feedback, PRIOR to its
# passing as arguments into the calculate_score() function
# but is currently not? ASK chat gpt after shower 
# - RESOLVED, true, understood not bad, pat on the back, good job

# issue 5 (major): Gemini Response to Google Sheets Issue ONCE MORE
# old forms and data fetches and updates onto sheets function without issue
# new forms and beyond seem to have issues --> 
# Specifically, newly fetched data replaces rows of the old data
# ask chatGPT tommorrow. 
# Solution is potentially to incooporate a memory system like did before?
# But this time, rather than account for google forms timestamps, 
# its for google sheets row positions 
# (try it tommorrow and ask what chatGPT thinks)
# - could be a hosting issue? ASK AFTER finished hosting
# - temparaily resolved, not an issue with this version of the program 

# issue 6 (minor): Google Sheets updates overwrites
# google sheets updates overwrite the titles of each coloum written on 
# the toppest row whenever application is run 
# Brainstorm fixes and ask ChatGPT for opinion.
# (try it tommorrow and ask what chatGPT thinks)
# Does not overwrite but appends the old data more 
# than a couple times unnessiaryly --> an issue (issue 10)
# - RESOLVED

# ---------------------|||||||

# RESOLVE FRIDAY (12/27/24))
# issue 7 (major): Something "Feels Off" about notification system 
# needs to undergo some validation checks
# devise tests and gather data: if no inconsistiencies / errors /
# deviation from preferences, then good. else not good, then go fix.
# currently under development...
# off was that haven't tested, testing revealed indeed was off
# still a problem... 

#----------------------|||||||

# issue 8 (major): Strike Errors
# strike under previous code did not ever return True, accidental.
# fixed, just set to return strike as True whenever clients, volunteers,
# hours was equal to zero and effort was "No"
# - RESOLVED, quick fix

# issue 9 (major): Notification Errors
# immediate notifications regarding strikes pertaining to individual
# submissions not received and processed properly.
# issue is in app.py, the current Flask Backend code calls the discord
# notification function WITH the email function all contained within the 
# "send_weekly_report" function- which is only called every friday. 
# I want email ones to be weekly, but discord ones to be immediate.  
# SOLUTION: call each indivdidual functions seperatedly with all the 
# same required preconditions and stuff set inside the current 
# send_weekly_report function. 
    # REPLACE the current weekly report function with 2 new ones:
    # 1st --> same thing but with only discord notifs now present as 
    # only function
    # 2nd --> same thing but with only email notifs now present as 
    # only function
# Yep, referencing a variables was a good call, but right now 
# code is VERY redudant, re-creates variables pertianing to the same 
# statistics over and over again since it's locally declared within
# a very specific variable --> fix at the end
# - RESOLVED


# ---------------------_||||||||||

# RESOLVE FRIDAY (12/27/24))
# issue 10 (major): Undesired Appending Errors
# not an error persay, but it's definetly unwanted. 
# Good that application does not overwrite and instead 
# appends new to old data, but right now has a problem;
# appends old and new data. why? idk. It does it more than a couple 
# of times unnessiaryly --> an issue indeed.
# hashtag Complex issue (or not an issue at all):
    # --> when has old data in the first place, appends old AND new data
    # unessisarily
    # --> when has no data, does the same thing
    # --> in both cases, notifications are sent- GOOD, but the appending
    # -BAD
    # --> looks like this:
    # runs the application
    # data 1 here
    # data 2 here
    # data 1 here again 
    # data 2 here again
    # --> strikes or not doesn't matter, in both scenarios 
    # data is appened over and over again and it doesn't stop
    # it's like the function to screen for the already processed 
    # timestamps and skip over the data that has the already processed
    # timestamsps is not working as intended 
# Possible Issues:
    # 1) lack of access to previous / already processed timestamps, 
    # (sheets should be empty to simulate when program starts and does 
    # not end via hosting service)
    # 2) inability to change the previous strike notified column value.
    # instead, it appends to the sheets a version of the same 
    # already-processed data but now with the strike notified value as yes  

# ---------------------_||||||||||



