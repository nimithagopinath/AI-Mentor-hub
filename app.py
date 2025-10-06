# suppress warnings
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# import libraries
import requests, os

from together import Together
import textwrap

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Initialize client only if API key exists
if TOGETHER_API_KEY:
    client = Together(api_key=TOGETHER_API_KEY)
else:
    client = None
    print("Warning: TOGETHER_API_KEY not found in environment variables")

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key


## FUNCTION 1: This Allows Us to Prompt the AI MODEL
# -------------------------------------------------
def prompt_llm(prompt, with_linebreak=False):
    # This function allows us to prompt an LLM via the Together API
    
    if not client:
        raise Exception("Together API client not initialized - check TOGETHER_API_KEY")

    # model
    model = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    output = response.choices[0].message.content

    if with_linebreak:
        # Wrap the output
        wrapped_output = textwrap.fill(output, width=50)
        return wrapped_output
    else:
        return output

def format_chatbot_response(response):
    """Format chatbot response with proper HTML structure"""
    if not response:
        return ""
    
    import re
    
    # First, convert all **text** patterns to <strong>text</strong>
    formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', response)
    
    # Handle bullet points and lists
    lines = formatted.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<br>')
            continue
            
        # Handle bullet points
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            content = line[1:].strip()
            html_lines.append(f'<li>{content}</li>')
        
        # Handle numbered lists
        elif line and line[0].isdigit() and '. ' in line:
            if not in_list:
                html_lines.append('<ol>')
                in_list = True
            content = line.split('. ', 1)[1] if '. ' in line else line
            html_lines.append(f'<li>{content}</li>')
        
        # Handle headers (lines that are just bold text)
        elif line.startswith('<strong>') and line.endswith('</strong>') and len(line) > 17:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            content = line[8:-9].strip()  # Remove <strong> and </strong>
            html_lines.append(f'<h3>{content}</h3>')
        
        # Regular paragraphs
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<p>{line}</p>')
    
    # Close any open list
    if in_list:
        html_lines.append('</ul>')
    
    return ''.join(html_lines)

def save_user_recommendations(user_id, recommendations, schedule):
    """Save user recommendations to a JSON file."""
    try:
        # Create data directory if it doesn't exist
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


def generate_user_id(name, background, goal):
    """Generate a unique user ID based on user information."""
    import hashlib
    user_string = f"{name.lower()}_{background.lower()}_{goal.lower()}"
    return hashlib.md5(user_string.encode()).hexdigest()[:12]


def get_recommendations(background: str, goal: str) -> list:
    """Generate AI-powered course/resource suggestions using LLM.

    Output structure per item:
    {"title": str, "url": str, "platform": str, "duration": str, "level": str, "rating": str, "desc": str, "why": str}
    """
    try:
        prompt = f"""
        You are an expert learning mentor. Based on this information:
        - Background: {background}
        - Goal: {goal}
        
        Recommend 6 specific online courses, resources, or learning materials that would help this person achieve their goal.
        
        For each recommendation, provide:
        1. Title
        2. URL (use real URLs for well-known platforms like Coursera, Udemy, Khan Academy, edX, etc.)
        3. Platform name (Coursera, Udemy, Khan Academy, edX, etc.)
        4. Duration (e.g., "4 weeks", "Self-paced", "20 hours")
        5. Level (Beginner, Intermediate, Advanced)
        6. Rating (e.g., "4.5+", "4.8")
        7. Brief description (1-2 sentences)
        8. Brief explanation of why this helps
        
        Format your response as a simple list:
        Title | URL | Platform | Duration | Level | Rating | Description | Why this helps
        
        Focus on practical, actionable resources that build a clear learning path from beginner to advanced.
        Include courses from different platforms like Coursera, Udemy, Khan Academy, edX, freeCodeCamp, etc.
        """
        
        response = prompt_llm(prompt)
        
        # Parse the LLM response into structured format
        recommendations = []
        lines = response.strip().split('\n')
        
        for line in lines:
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 8:
                    recommendations.append({
                        "title": parts[0],
                        "url": parts[1],
                        "platform": parts[2],
                        "duration": parts[3],
                        "level": parts[4],
                        "rating": parts[5],
                        "desc": parts[6],
                        "why": parts[7]
                    })
        
        # Fallback if parsing fails
        if not recommendations:
            return [
                {
                    "title": "Python for Everybody Specialization",
                    "url": "https://www.coursera.org/specializations/python",
                    "platform": "Coursera",
                    "duration": "8 months",
                    "level": "Beginner",
                    "rating": "4.8",
                    "desc": "Learn Python programming fundamentals with hands-on projects and real-world applications.",
                    "why": "Build essential programming skills for data science and AI."
                },
                {
                    "title": "Machine Learning Course",
                    "url": "https://www.coursera.org/learn/machine-learning",
                    "platform": "Coursera",
                    "duration": "11 weeks",
                    "level": "Intermediate",
                    "rating": "4.9",
                    "desc": "Comprehensive introduction to machine learning algorithms and applications.",
                    "why": "Master core ML concepts and practical implementation skills."
                },
                {
                    "title": "Deep Learning Specialization",
                    "url": "https://www.coursera.org/specializations/deep-learning",
                    "platform": "Coursera",
                    "duration": "5 months",
                    "level": "Advanced",
                    "rating": "4.8",
                    "desc": "Advanced neural networks, CNNs, RNNs, and deep learning applications.",
                    "why": "Develop expertise in cutting-edge AI technologies."
                },
                {
                    "title": "Statistics and Probability",
                    "url": "https://www.khanacademy.org/math/statistics-probability",
                    "platform": "Khan Academy",
                    "duration": "Self-paced",
                    "level": "Beginner",
                    "rating": "4.5+",
                    "desc": "Essential statistical concepts and probability theory for data analysis.",
                    "why": "Build mathematical foundation for machine learning."
                },
                {
                    "title": "Data Science Bootcamp",
                    "url": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/",
                    "platform": "Udemy",
                    "duration": "25 hours",
                    "level": "Intermediate",
                    "rating": "4.6",
                    "desc": "Complete data science workflow with Python, pandas, scikit-learn, and more.",
                    "why": "Apply programming skills to real data science projects."
                },
                {
                    "title": "Advanced Machine Learning",
                    "url": "https://www.edx.org/course/machine-learning-fundamentals",
                    "platform": "edX",
                    "duration": "6 weeks",
                    "level": "Advanced",
                    "rating": "4.7",
                    "desc": "Advanced ML techniques, model optimization, and production deployment.",
                    "why": "Master advanced ML concepts for professional applications."
                }
            ]
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Fallback to static recommendations
        return [
            {
                "title": "Python for Everybody Specialization",
                "url": "https://www.coursera.org/specializations/python",
                "platform": "Coursera",
                "duration": "8 months",
                "level": "Beginner",
                "rating": "4.8",
                "desc": "Learn Python programming fundamentals with hands-on projects and real-world applications.",
                "why": "Build essential programming skills for data science and AI."
            },
            {
                "title": "Machine Learning Course",
                "url": "https://www.coursera.org/learn/machine-learning",
                "platform": "Coursera",
                "duration": "11 weeks",
                "level": "Intermediate",
                "rating": "4.9",
                "desc": "Comprehensive introduction to machine learning algorithms and applications.",
                "why": "Master core ML concepts and practical implementation skills."
            },
            {
                "title": "Deep Learning Specialization",
                "url": "https://www.coursera.org/specializations/deep-learning",
                "platform": "Coursera",
                "duration": "5 months",
                "level": "Advanced",
                "rating": "4.8",
                "desc": "Advanced neural networks, CNNs, RNNs, and deep learning applications.",
                "why": "Develop expertise in cutting-edge AI technologies."
            },
            {
                "title": "Statistics and Probability",
                "url": "https://www.khanacademy.org/math/statistics-probability",
                "platform": "Khan Academy",
                "duration": "Self-paced",
                "level": "Beginner",
                "rating": "4.5+",
                "desc": "Essential statistical concepts and probability theory for data analysis.",
                "why": "Build mathematical foundation for machine learning."
            },
            {
                "title": "Data Science Bootcamp",
                "url": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/",
                "platform": "Udemy",
                "duration": "25 hours",
                "level": "Intermediate",
                "rating": "4.6",
                "desc": "Complete data science workflow with Python, pandas, scikit-learn, and more.",
                "why": "Apply programming skills to real data science projects."
            },
            {
                "title": "Advanced Machine Learning",
                "url": "https://www.edx.org/course/machine-learning-fundamentals",
                "platform": "edX",
                "duration": "6 weeks",
                "level": "Advanced",
                "rating": "4.7",
                "desc": "Advanced ML techniques, model optimization, and production deployment.",
                "why": "Master advanced ML concepts for professional applications."
            }
        ]


@app.route("/", methods=["GET"])
def landing():
    """Landing page matching the screenshot design."""
    return render_template("landing.html")


@app.route("/ai-skills-analysis")
def ai_skills_analysis():
    """AI Skills Analysis feature page."""
    return render_template("ai_skills_analysis.html")


@app.route("/personalized-learning-paths")
def personalized_learning_paths():
    """Personalized Learning Paths feature page."""
    return render_template("personalized_learning_paths.html")


@app.route("/structured-timeline")
def structured_timeline():
    """Structured Timeline feature page."""
    return render_template("structured_timeline.html")


@app.route("/career-guidance")
def career_guidance():
    """Career Guidance feature page."""
    return render_template("career_guidance.html")


@app.route("/quality-curation")
def quality_curation():
    """Quality Curation feature page."""
    return render_template("quality_curation.html")


@app.route("/project-recommendations")
def project_recommendations():
    """Project Recommendations feature page."""
    return render_template("project_recommendations.html")


@app.route("/mentor", methods=["GET"])
def mentor():
    """AI Mentor features page matching the screenshot design."""
    return render_template("mentor.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple login page - accepts any credentials for demo."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        # Simple demo login - accept any email/password
        if email and password:
            return redirect(url_for("dashboard_selection"))
        else:
            return render_template("login.html", error="Please enter both email and password")
    
    return render_template("login.html")


@app.route("/dashboard-selection")
def dashboard_selection():
    """Dashboard selection page after login."""
    return render_template("dashboard_selection.html")


@app.route("/study-dashboard")
def study_dashboard():
    """Study preparations dashboard matching the screenshot."""
    return render_template("study_dashboard.html")


@app.route("/career-dashboard")
def career_dashboard():
    """Career guidance dashboard."""
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


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Dashboard with the learning form and recommendations."""
    recommendations = []
    schedule = []
    user = {
        "name": "",
        "background": "",
        "goal": "",
    }

    if request.method == "POST":
        user["name"] = request.form.get("name", "").strip()
        user["background"] = request.form.get("background", "").strip()
        user["goal"] = request.form.get("goal", "").strip()
        
        # Ensure we always get lists, not functions
        try:
            recommendations = get_recommendations(user["background"], user["goal"])
            schedule = build_schedule(user["background"], user["goal"])
        except Exception as e:
            print(f"Error in AI generation: {e}")
            recommendations = []
            schedule = []
        
        # Ensure they are lists
        if not isinstance(recommendations, list):
            recommendations = []
        if not isinstance(schedule, list):
            schedule = [] 

    return render_template("index.html", user=user, recommendations=recommendations, schedule=schedule)


def build_schedule(background: str, goal: str, recommendations: list = None) -> list:
    """Generate AI-powered week-by-week schedule using LLM and recommendations."""
    try:
        # Create a more detailed prompt that considers the actual recommendations
        rec_info = ""
        if recommendations:
            rec_info = "\nRecommended courses:\n"
            for i, rec in enumerate(recommendations[:6], 1):
                rec_info += f"{i}. {rec['title']} ({rec['platform']}) - {rec['duration']}\n"
        
        prompt = f"""
        You are an expert learning mentor. Create a realistic 6-week learning schedule for someone with:
        - Background: {background}
        - Goal: {goal}
        {rec_info}
        
        Create a week-by-week plan with 2-4 specific, actionable tasks per week that build toward their goal.
        Each week should have concrete deliverables and learning objectives that align with the recommended courses.
        Make it realistic - consider that people have limited time (2-4 hours per week).
        
        Format your response as:
        Week 1: Task 1, Task 2, Task 3
        Week 2: Task 1, Task 2, Task 3
        Week 3: Task 1, Task 2, Task 3
        Week 4: Task 1, Task 2, Task 3
        Week 5: Task 1, Task 2, Task 3
        Week 6: Task 1, Task 2, Task 3
        
        Make it practical and achievable, with each week building on the previous one.
        Include specific course modules, practice exercises, and project milestones.
        """
        
        response = prompt_llm(prompt)
        
        # Parse the LLM response into structured format
        schedule = []
        lines = response.strip().split('\n')
        
        for line in lines:
            if line.startswith('Week '):
                # Extract week number and tasks
                parts = line.split(':', 1)
                if len(parts) == 2:
                    week_part = parts[0].strip()
                    tasks_part = parts[1].strip()
                    
                    # Extract week number
                    week_num = int(week_part.split()[1])
                    
                    # Split tasks
                    tasks = [task.strip() for task in tasks_part.split(',') if task.strip()]
                    
                    schedule.append({
                        "week": week_num,
                        "items": tasks,
                        "completed": False,
                        "progress": 0
                    })
        
        # Sort by week number and ensure we have 6 weeks
        schedule.sort(key=lambda x: x["week"])
        
        # Fallback if parsing fails
        if len(schedule) < 6:
            return [
                {"week": 1, "items": ["Complete Week 1 of Python course", "Set up development environment", "Complete 3 coding exercises"], "completed": False, "progress": 0},
                {"week": 2, "items": ["Finish Python fundamentals", "Start statistics course", "Build first small project"], "completed": False, "progress": 0},
                {"week": 3, "items": ["Complete statistics module", "Start machine learning basics", "Work on project documentation"], "completed": False, "progress": 0},
                {"week": 4, "items": ["Deep dive into ML algorithms", "Complete intermediate course", "Iterate on project"], "completed": False, "progress": 0},
                {"week": 5, "items": ["Share project for feedback", "Complete advanced topics", "Refine project based on feedback"], "completed": False, "progress": 0},
                {"week": 6, "items": ["Finalize portfolio project", "Complete final course modules", "Plan next learning steps"], "completed": False, "progress": 0},
            ]
        
        return schedule[:6]  # Ensure exactly 6 weeks
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        # Fallback to static schedule
        return [
            {"week": 1, "items": ["Complete Week 1 of Python course", "Set up development environment", "Complete 3 coding exercises"], "completed": False, "progress": 0},
            {"week": 2, "items": ["Finish Python fundamentals", "Start statistics course", "Build first small project"], "completed": False, "progress": 0},
            {"week": 3, "items": ["Complete statistics module", "Start machine learning basics", "Work on project documentation"], "completed": False, "progress": 0},
            {"week": 4, "items": ["Deep dive into ML algorithms", "Complete intermediate course", "Iterate on project"], "completed": False, "progress": 0},
            {"week": 5, "items": ["Share project for feedback", "Complete advanced topics", "Refine project based on feedback"], "completed": False, "progress": 0},
            {"week": 6, "items": ["Finalize portfolio project", "Complete final course modules", "Plan next learning steps"], "completed": False, "progress": 0},
        ]


## Chat endpoints removed for landing-page flow


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
    
    try:
        response = prompt_llm(prompt)
    except Exception as e:
        response = f"I'm having trouble connecting to the AI service right now. Please try again later. Error: {str(e)}"
    
    # Format the response for better display
    formatted_response = format_chatbot_response(response)
    
    return jsonify({"response": formatted_response})

if __name__ == "__main__":
    app.run(debug=True)


