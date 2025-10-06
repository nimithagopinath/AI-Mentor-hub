from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime, timedelta
import json
import os
import hashlib
from dotenv import load_dotenv
from together import Together
import textwrap

load_dotenv()

app = Flask(__name__)
app.secret_key = "ai_mentor_hub_secret_key_2025"

# Load Together AI API key
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY) if TOGETHER_API_KEY else None

def prompt_llm(prompt, with_linebreak=False):
    """Function to prompt the LLM via Together API"""
    if not client:
        return "AI service not available. Please check your API configuration."
    
    model = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        output = response.choices[0].message.content
        
        if with_linebreak:
            wrapped_output = textwrap.fill(output, width=50)
            return wrapped_output
        else:
            return output
    except Exception as e:
        return f"Error generating response: {str(e)}"

def generate_user_id(name, background, goal):
    """Generate a unique user ID based on user information."""
    user_string = f"{name.lower()}_{background.lower()}_{goal.lower()}"
    return hashlib.md5(user_string.encode()).hexdigest()[:12]

def save_user_recommendations(user_id, recommendations, schedule):
    """Save user recommendations to a JSON file."""
    try:
        os.makedirs('user_data', exist_ok=True)
        
        user_data = {
            'user_id': user_id,
            'recommendations': recommendations,
            'schedule': schedule,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        file_path = f'user_data/{user_id}.json'
        with open(file_path, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        print(f"Saved recommendations for user: {user_id}")
        return True
    except Exception as e:
        print(f"Error saving user recommendations: {e}")
        return False

def load_user_recommendations(user_id):
    """Load user recommendations from JSON file."""
    try:
        file_path = f'user_data/{user_id}.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                user_data = json.load(f)
            
            # Check if data is not too old (optional: 30 days)
            created_at = datetime.fromisoformat(user_data['created_at'])
            if datetime.now() - created_at < timedelta(days=30):
                print(f"Loaded existing recommendations for user: {user_id}")
                return user_data['recommendations'], user_data['schedule']
            else:
                print(f"Recommendations too old for user: {user_id}")
                return None, None
        else:
            print(f"No existing recommendations found for user: {user_id}")
            return None, None
    except Exception as e:
        print(f"Error loading user recommendations: {e}")
        return None, None

def get_recommendations(background, goal):
    """Generate personalized course recommendations using AI."""
    prompt = f"""
    Based on the user's background: "{background}" and goal: "{goal}", 
    recommend 6 high-quality online courses/resources that would help them achieve their goal.
    
    For each recommendation, provide:
    - title: Course/resource name
    - url: Link to the resource
    - platform: Where it's hosted (Coursera, Udemy, YouTube, etc.)
    - duration: How long it takes
    - level: Beginner/Intermediate/Advanced
    - rating: Quality rating (4.0+ format)
    - desc: 1-2 sentence description
    - why: Why this helps their goal
    
    Format as JSON array with these exact field names.
    """
    
    try:
        response = prompt_llm(prompt)
        # Try to parse JSON response
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            recommendations = json.loads(json_match.group())
            return recommendations
    except Exception as e:
        print(f"Error parsing AI response: {e}")
    
    # Fallback recommendations
    return [
        {
            "title": "Introduction to Programming",
            "url": "https://www.codecademy.com/learn/introduction-to-programming",
            "platform": "Codecademy",
            "duration": "20 hours",
            "level": "Beginner",
            "rating": "4.5+",
            "desc": "Learn programming fundamentals and basic concepts",
            "why": "Build essential programming skills for your career"
        },
        {
            "title": "Web Development Basics",
            "url": "https://www.freecodecamp.org/",
            "platform": "freeCodeCamp",
            "duration": "Self-paced",
            "level": "Beginner",
            "rating": "4.8",
            "desc": "HTML, CSS, and JavaScript fundamentals",
            "why": "Create interactive web applications"
        }
    ]

def build_schedule(background, goal, recommendations):
    """Generate a 6-week learning schedule based on recommendations."""
    prompt = f"""
    Create a realistic 6-week learning schedule for someone with background: "{background}" 
    trying to achieve goal: "{goal}".
    
    Based on these recommended courses: {[rec['title'] for rec in recommendations]}
    
    For each week, provide:
    - week: Week number (1-6)
    - items: List of 3-4 specific tasks/activities
    - completed: false
    - progress: 0
    
    Make tasks specific and actionable. Format as JSON array.
    """
    
    try:
        response = prompt_llm(prompt)
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            schedule = json.loads(json_match.group())
            return schedule
    except Exception as e:
        print(f"Error parsing schedule response: {e}")
    
    # Fallback schedule
    return [
        {"week": 1, "items": ["Complete programming basics", "Practice coding exercises"], "completed": False, "progress": 0},
        {"week": 2, "items": ["Learn HTML and CSS", "Build first webpage"], "completed": False, "progress": 0},
        {"week": 3, "items": ["Study JavaScript fundamentals", "Create interactive elements"], "completed": False, "progress": 0},
        {"week": 4, "items": ["Build a complete project", "Deploy your work"], "completed": False, "progress": 0},
        {"week": 5, "items": ["Learn advanced concepts", "Work on portfolio"], "completed": False, "progress": 0},
        {"week": 6, "items": ["Final project completion", "Prepare for next phase"], "completed": False, "progress": 0}
    ]

@app.route("/")
def landing():
    """Landing page"""
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple demo login - accepts any credentials"""
    if request.method == "POST":
        # Demo login - accept any credentials
        session['logged_in'] = True
        session['user_name'] = request.form.get('email', 'User')
        return redirect(url_for('dashboard_selection'))
    return render_template("login.html")

@app.route("/dashboard-selection")
def dashboard_selection():
    """Dashboard selection page"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("dashboard_selection.html")

@app.route("/study-dashboard")
def study_dashboard():
    """Study preparations dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("study_dashboard.html")

@app.route("/career-dashboard")
def career_dashboard():
    """Career guidance dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("career_dashboard.html")

@app.route("/check-recommendations", methods=["POST"])
def check_recommendations():
    """Check if user has existing recommendations."""
    user = {
        "name": request.form.get("name", "").strip(),
        "background": request.form.get("background", "").strip(),
        "goal": request.form.get("goal", "").strip(),
    }
    
    user_id = generate_user_id(user["name"], user["background"], user["goal"])
    recommendations, schedule = load_user_recommendations(user_id)
    
    if recommendations:
        return {"has_recommendations": True, "message": "You have existing recommendations. Click 'Generate Recommendations' to view them, or 'Regenerate' to create new ones."}
    else:
        return {"has_recommendations": False, "message": "No existing recommendations found. Click 'Generate Recommendations' to create your personalized learning path."}

@app.route("/recommendations", methods=["POST"])
def recommendations():
    """Generate and display personalized learning recommendations."""
    print("Recommendations route called!")
    user = {
        "name": request.form.get("name", "").strip(),
        "background": request.form.get("background", "").strip(),
        "goal": request.form.get("goal", "").strip(),
    }
    print(f"User data: {user}")
    
    # Generate unique user ID
    user_id = generate_user_id(user["name"], user["background"], user["goal"])
    
    # Check if user wants to regenerate (from regenerate button)
    regenerate = request.form.get("regenerate", "false").lower() == "true"
    
    # Try to load existing recommendations first (unless regenerating)
    recommendations = None
    schedule = None
    
    if not regenerate:
        recommendations, schedule = load_user_recommendations(user_id)
    
    # Generate new recommendations if none exist or user requested regeneration
    if recommendations is None or regenerate:
        print(f"Generating new recommendations for user: {user_id}")
        try:
            recommendations = get_recommendations(user["background"], user["goal"])
            schedule = build_schedule(user["background"], user["goal"], recommendations)
            
            # Save the new recommendations
            save_user_recommendations(user_id, recommendations, schedule)
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            # Fallback recommendations
            recommendations = [
                {
                    "title": "Introduction to Programming",
                    "url": "https://www.codecademy.com/learn/introduction-to-programming",
                    "platform": "Codecademy",
                    "duration": "20 hours",
                    "level": "Beginner",
                    "rating": "4.5+",
                    "desc": "Learn programming fundamentals and basic concepts",
                    "why": "Build essential programming skills for your career"
                },
                {
                    "title": "Web Development Basics",
                    "url": "https://www.freecodecamp.org/",
                    "platform": "freeCodeCamp",
                    "duration": "Self-paced",
                    "level": "Beginner",
                    "rating": "4.8",
                    "desc": "HTML, CSS, and JavaScript fundamentals",
                    "why": "Create interactive web applications"
                }
            ]
            schedule = [
                {"week": 1, "items": ["Complete programming basics", "Practice coding exercises"], "completed": False, "progress": 0},
                {"week": 2, "items": ["Learn HTML and CSS", "Build first webpage"], "completed": False, "progress": 0},
                {"week": 3, "items": ["Study JavaScript fundamentals", "Create interactive elements"], "completed": False, "progress": 0},
                {"week": 4, "items": ["Build a complete project", "Deploy your work"], "completed": False, "progress": 0},
                {"week": 5, "items": ["Learn advanced concepts", "Work on portfolio"], "completed": False, "progress": 0},
                {"week": 6, "items": ["Final project completion", "Prepare for next phase"], "completed": False, "progress": 0}
            ]
    
    # Ensure they are lists
    if not isinstance(recommendations, list):
        recommendations = []
    if not isinstance(schedule, list):
        schedule = []
    
    # Store user info in session for future reference
    session['user_id'] = user_id
    session['user_name'] = user["name"]
    session['user_background'] = user["background"]
    session['user_goal'] = user["goal"]
    
    return render_template("recommendations.html", user=user, recommendations=recommendations, schedule=schedule)

# Feature detail pages
@app.route("/ai-skills-analysis")
def ai_skills_analysis():
    return render_template("ai_skills_analysis.html")

@app.route("/personalized-learning-paths")
def personalized_learning_paths():
    return render_template("personalized_learning_paths.html")

@app.route("/structured-timeline")
def structured_timeline():
    return render_template("structured_timeline.html")

@app.route("/career-guidance")
def career_guidance():
    return render_template("career_guidance.html")

@app.route("/quality-curation")
def quality_curation():
    return render_template("quality_curation.html")

@app.route("/project-recommendations")
def project_recommendations():
    return render_template("project_recommendations.html")

@app.route("/chat", methods=["POST"])
def chat():
    """AI Mentor chatbot for learning guidance"""
    data = request.get_json()
    user_message = data.get("message", "")
    
    context = """You are an AI Learning Mentor for the AI Mentor Hub. 
    This app helps students and career-switchers by:
    - Analyzing their skills and background
    - Creating personalized learning paths
    - Recommending quality online courses
    - Building structured study schedules
    - Providing career guidance
    
    Answer questions about learning, courses, career advice, and study planning.
    Be encouraging, practical, and specific.
    
    Instructions:
    - Keep responses concise (3-4 lines max)
    - Use bullet points when helpful
    - Focus on actionable advice
    """
    
    prompt = f"{context}\n\nUser question: {user_message}"
    
    # Save the conversation for debugging
    os.makedirs("results", exist_ok=True)
    with open("results/chat_prompt.txt", "w") as f:
        f.write(prompt)
    
    response = prompt_llm(prompt)
    
    # Format the response for better display
    formatted_response = response.replace("•", "<br>•").replace("- ", "<br>• ")
    if formatted_response.startswith("<br>"):
        formatted_response = formatted_response[4:]  # Remove leading <br>
    
    return jsonify({"response": formatted_response})

@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('landing'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)

