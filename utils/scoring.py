def calculate_score(role, clients=0, volunteers=0, hours=0):
    """
    Calculate engagement scores based on role-specific criteria.
    """
    try:
        if role == "Outreach":
            score = (clients * 2) + volunteers
            return min(score, 9999999999999)  # Cap the score at max
        
        if role == "Developer":
            score = hours
            return min(score, 9999999999999)  # Cap the score at max
        
        return 0  # Default score for undefined roles

    except Exception as e:
        print(f"❌ Error in scoring logic: {e}")
        return 0

# Testing the Scoring Logic
if __name__ == "__main__":
    print("🧮 Testing Scoring Logic:")
    print("Outreach - 5 clients, 3 volunteers:", calculate_score("Outreach", clients=5, volunteers=3))
    print("Developer - 12 hours worked:", calculate_score("Developer", hours=12))
    print("Undefined Role:", calculate_score("Undefined"))
