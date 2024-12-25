from flask import Flask, jsonify
from utils.google_api import get_google_service, fetch_form_data, update_sheet
from utils.scoring import calculate_score
from utils.gemini_api import get_gemini_feedback
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
    """
    Fetch data from Google Forms, process scores, generate feedback, and update Google Sheets.
    """
    try:
        print("🔄 Fetching data from Google Forms...")
        sheets, forms = get_google_service()
        form_data = fetch_form_data(forms, os.getenv('FORM_ID'))

        if not form_data or 'responses' not in form_data:
            return jsonify({"status": "error", "message": "No responses found in Google Form."})

        print("✅ Data fetched. Processing responses...")

        processed_data = []
        for entry in form_data.get('responses', []):
            name = entry.get('name', 'Unknown')
            role = entry.get('role', 'Undefined')
            clients = int(entry.get('clients', 0))
            volunteers = int(entry.get('volunteers', 0))
            hours = int(entry.get('hours', 0))
            activity = entry.get('activity', 'No activity')

            # Calculate engagement score
            score = calculate_score(role, clients, volunteers, hours)
            print(f"🧮 Calculated score for {name} ({role}): {score}")

            # Get feedback from Gemini API
            feedback = get_gemini_feedback(activity)
            print(f"🤖 Gemini feedback for {name}: {feedback}")

            # Add to processed data
            processed_data.append([name, role, score, feedback])

        # Update Google Sheet with processed data
        update_sheet(sheets, os.getenv('SPREADSHEET_ID'), processed_data)
        print("✅ Google Sheet updated successfully!")

        return jsonify({"status": "success", "message": "Data processed and updated successfully!"})

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
