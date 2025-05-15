
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY is not set. Please verify your .env file.")

genai.configure(api_key=api_key)


def clean_gemini_response(response_text):
    """
    Clean Gemini response text by removing Markdown artifacts like triple backticks and JSON labels.
    
    Args:
        response_text (str): Raw text response from Gemini.
    
    Returns:
        str: Cleaned JSON string.
    """
    try:
        cleaned_text = re.sub(r'^\s*```[a-zA-Z]*\s*', '', response_text.strip())
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        
        print("🔄 Cleaned response for parsing:", cleaned_text)
        return cleaned_text
    except Exception as e:
        print(f"❌ Error while cleaning Gemini response: {e}")
        return "{}"  # bro what why empty wthijrgnerfioernfreifermfirefm


def analyze_activity_with_gemini(activity_data):
    """
    Analyze activity data using Gemini and extract key metrics.
    
    Args:
        activity_data (str): Free-text activity description.

    Returns:
        dict: Extracted metrics (clients, volunteers, hours, effort).
    """
    try:
        print("🔄 Sending activity data to Gemini for analysis...")

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"""
            Analyze the following weekly activity report and extract the following metrics:
            - Number of clients recruited
            - Number of volunteers recruited
            - Number of hours worked on website(s)  
            - Was effort shown? (Yes(if any of previous metrics is not 0)/No)
            Activity Report: {activity_data}
            
            Respond in JSON format like this and do NOT say the word JSON:
            {{
                "clients": <number>,
                "volunteers": <number>,
                "hours": <number>,
                "effort": "<Yes/No>"
            }}
            """
        )

        print("🔄 Raw response from Gemini:", response.text)

        cleaned_text = clean_gemini_response(response.text)

        if not cleaned_text.startswith("{") or not cleaned_text.endswith("}"):
            print("❌ Cleaned text does not match JSON structure.")
            return {"clients": 0, "volunteers": 0, "hours": 0, "effort": False}

        try:
            metrics = json.loads(cleaned_text)
            print("✅ Metrics extracted from Gemini feedback:", metrics)
            return {
                "clients": metrics.get("clients", 0),
                "volunteers": metrics.get("volunteers", 0),
                "hours": metrics.get("hours", 0),
                "effort": metrics.get("effort", "No").lower() == "yes"
            }
        except json.JSONDecodeError as json_err:
            print(f"❌ Failed to parse JSON from Gemini response: {cleaned_text}")
            print(f"JSON Parsing Error: {json_err}")
            return {"clients": 0, "volunteers": 0, "hours": 0, "effort": False}

    except Exception as e:
        print(f"❌ Error during Gemini analysis: {e}")
        return {"clients": 0, "volunteers": 0, "hours": 0, "effort": False}
