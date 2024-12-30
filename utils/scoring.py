def calculate_score(role, clients=0, volunteers=0, hours=0, effort=False, gemini_feedback=""):
    """
    Calculate engagement scores based on role-specific criteria and Gemini feedback.
    
    Args:
        role (str): The role of the team member (Outreach/Developer).
        clients (int): Number of clients recruited.
        volunteers (int): Number of volunteers recruited.
        hours (int): Number of hours worked.
        effort (bool): Whether effort was made.
        gemini_feedback (str): AI-generated feedback on activities.

    Returns:
        dict: A dictionary containing score, strike, and effort acknowledgment.
    """
    try:
        score = 0
        strike = False  # Initialize strike to False
        effort_acknowledged = effort

        if role == "Outreach & Social Media":
            score = (clients * 3) + (volunteers * 5)
            if clients == 0 and volunteers == 0 and not effort: 
                strike = True  # Set strike to True if no clients/volunteers and no effort

        elif role == "Developer":
            score = hours
            if hours == 0 and not effort: 
                strike = True  # Set strike to True if no hours worked and no effort

        return {
            "score": max(score, 0),
            "strike": strike, 
            "effort_acknowledged": effort_acknowledged
        }

    except Exception as e:
        print(f"❌ Error in scoring logic: {e}")
        return {"score": 0, "strike": True, "effort_acknowledged": False}
    
# # Testing the Scoring Logic
# if __name__ == "__main__":
#     print("🧮 Testing Scoring Logic:")
#     print("Outreach - 5 clients, 3 volunteers:", calculate_score("Outreach", clients=5, volunteers=3))
#     print("Outreach - 0 clients, 0 volunteers, effort made:", calculate_score("Outreach", clients=0, volunteers=0, effort=True))
#     print("Developer - 12 hours worked:", calculate_score("Developer", hours=12))
#     print("Developer - 0 hours worked, effort made:", calculate_score("Developer", hours=0, effort=True))
#     print("Undefined Role:", calculate_score("Undefined"))
