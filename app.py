from flask import Flask, jsonify
from utils.google_api import get_google_service, fetch_form_data, update_sheet
from utils.scoring import calculate_score
from utils.gemini_api import analyze_activity_with_gemini
import os
from dotenv import load_dotenv

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
    sheets, forms = get_google_service()
    form_data = fetch_form_data(forms, os.getenv('FORM_ID'))

    # Fetch existing timestamps from Google Sheets
    existing_timestamps = []
    sheet_data = sheets.spreadsheets().values().get(
        spreadsheetId=os.getenv('SPREADSHEET_ID'),
        range='Sheet1!A:A'  # Assuming Timestamp is in Column A
    ).execute()

    for row in sheet_data.get('values', [])[1:]:  # Skip header
        existing_timestamps.append(row[0])  # Collect all timestamps

    processed_data = []
    for entry in form_data.get('responses', []):
        timestamp = entry.get('createTime', '')  # Get timestamp from form submission
        
        # Skip already processed timestamps
        if timestamp in existing_timestamps:
            print(f"🔄 Skipping already processed timestamp: {timestamp}")
            continue
        
        # Extract basic data
        name = entry.get('answers', {}).get('40836d3c', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'Unknown')
        role = entry.get('answers', {}).get('37580eae', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'Undefined')
        activity = entry.get('answers', {}).get('4c26168e', {}).get('textAnswers', {}).get('answers', [{}])[0].get('value', 'No activity')
        
        print(f"Role Extracted from Form: {role}")
        print(f"Activity Data Sent to Gemini: {activity}")

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
        effort_acknowledged = result['effort_acknowledged']

        feedback = f"Clients: {clients}, Volunteers: {volunteers}, Hours: {hours}, Effort: {'Yes' if effort else 'No'}"

        # Append data to Google Sheets
        processed_data.append([
            timestamp,
            name,
            role,  # Use the role directly from the Google Form
            score,
            "Yes" if effort else "No",
            "Yes" if strike else "No",
            feedback
        ])

    if processed_data:
        update_sheet(sheets, os.getenv('SPREADSHEET_ID'), processed_data)
        print("✅ New submissions processed and added to Google Sheets.")
    else:
        print("🔄 No new submissions found to process.")

    return jsonify({"status": "success", "message": "New submissions processed successfully"})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)


#feedback:

# issue 1: Formatting Issue
# ask for question format regarding google form responses
# ask for recorded data and feedback format regarding google sheets 
# data does NOT seem to have been processed. 
# gemini to sheets connection is good,
# forms to gemini data gathering may be an issue at play here (possibly) 
# - RESOLVED

# issue 2: Gemini Response to Google Sheets Issue
# first form and data fetch and update onto sheets function without issue
# second form and beyond seem to have issues  (test first)
# - RESOLVED, not a problem anymore

# issue 3: Hosting issue
# received the message for terminal: " WARNING: This is a development server. 
# Do not use it in a production deployment. 
# Use a production WSGI server instead. "
# will be resolved in later milestones when transfering application's
# hosting envrioment from locally onto github pages 
# to be solved...

# issue 4: Scoring issue
# scores not properly calculated 
# something likely wrong with scoring.py's intake of the hours worked, 
# clients, as well as volunteers recruited arguments 
# SHOULD have values initiated via gemini feedback, PRIOR to its
# passing as arguments into the calculate_score() function
# but is currently not? ASK chat gpt after shower 
# - RESOLVED, true, understood not bad, pat on the back, good job

# issue 5: Gemini Response to Google Sheets Issue ONCE MORE
# old forms and data fetches and updates onto sheets function without issue
# new forms and beyond seem to have issues --> 
# Specifically, newly fetched data replaces rows of the old data
# ask chatGPT tommorrow. 
# Solution is potentially to incooporate a memory system like did before?
# But this time, rather than for google forms timestamps, 
# its for google sheets row positions 
# (try it tommorrow and ask what chatGPT thinks)

# issue 6 (minor): Google Sheets updates overwrites
# google sheets updates overwrite the titles of each coloum written on 
# the toppest row whenever application is run 
# Brainstorm fixes and ask ChatGPT for opinion.
# (try it tommorrow and ask what chatGPT thinks)