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

from flask import Flask, render_template, request

app = Flask(__name__)


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


def get_recommendations(background: str, goal: str) -> list:
    """Generate AI-powered course/resource suggestions using LLM."""
    try:
        prompt = f"""
        You are an expert learning mentor. Based on this information:
        - Background: {background}
        - Goal: {goal}
        
        Recommend 4-5 specific online courses, resources, or learning materials that would help this person achieve their goal.
        
        For each recommendation, provide:
        1. Title
        2. URL (use real URLs for well-known platforms like Coursera, Udemy, Khan Academy, etc.)
        3. Brief explanation of why this helps
        
        Format your response as a simple list:
        Title | URL | Why this helps
        
        Focus on practical, actionable resources that build a clear learning path.
        """
        
        response = prompt_llm(prompt)
        
        # Parse the LLM response into structured format
        recommendations = []
        lines = response.strip().split('\n')
        
        for line in lines:
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    recommendations.append({
                        "title": parts[0],
                        "url": parts[1],
                        "why": parts[2]
                    })
        
        # Fallback if parsing fails
        if not recommendations:
            return [
                {
                    "title": "Intro to Python",
                    "url": "https://www.learnpython.org/",
                    "why": "Build fundamentals for automation, data and AI."
                },
                {
                    "title": "Khan Academy – Algebra & Statistics", 
                    "url": "https://www.khanacademy.org/math",
                    "why": "Strengthen the math base needed for analytics/ML."
                }
            ]
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Fallback to static recommendations
        return [
            {
                "title": "Intro to Python",
                "url": "https://www.learnpython.org/",
                "why": "Build fundamentals for automation, data and AI."
            },
            {
                "title": "Khan Academy – Algebra & Statistics",
                "url": "https://www.khanacademy.org/math", 
                "why": "Strengthen the math base needed for analytics/ML."
            }
        ]


@app.route("/", methods=["GET", "POST"])
def index():
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


def build_schedule(background: str, goal: str) -> list:
    """Generate AI-powered week-by-week schedule using LLM."""
    try:
        prompt = f"""
        You are an expert learning mentor. Create a 6-week learning schedule for someone with:
        - Background: {background}
        - Goal: {goal}
        
        Create a week-by-week plan with 2-3 specific, actionable tasks per week that build toward their goal.
        Each week should have concrete deliverables and learning objectives.
        
        Format your response as:
        Week 1: Task 1, Task 2, Task 3
        Week 2: Task 1, Task 2, Task 3
        Week 3: Task 1, Task 2, Task 3
        Week 4: Task 1, Task 2, Task 3
        Week 5: Task 1, Task 2, Task 3
        Week 6: Task 1, Task 2, Task 3
        
        Make it practical and achievable, with each week building on the previous one.
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
                        "items": tasks
                    })
        
        # Sort by week number and ensure we have 6 weeks
        schedule.sort(key=lambda x: x["week"])
        
        # Fallback if parsing fails
        if len(schedule) < 6:
            return [
                {"week": 1, "items": ["Establish baseline skills and pick a clear goal"]},
                {"week": 2, "items": ["Do 3 fundamentals tutorials relevant to your goal"]},
                {"week": 3, "items": ["Start a tiny project; document learnings"]},
                {"week": 4, "items": ["Study 2 deeper resources; iterate project"]},
                {"week": 5, "items": ["Share work for feedback; refine"]},
                {"week": 6, "items": ["Prepare a small portfolio artifact and next steps"]},
            ]
        
        return schedule[:6]  # Ensure exactly 6 weeks
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        # Fallback to static schedule
        return [
            {"week": 1, "items": ["Establish baseline skills and pick a clear goal"]},
            {"week": 2, "items": ["Do 3 fundamentals tutorials relevant to your goal"]},
            {"week": 3, "items": ["Start a tiny project; document learnings"]},
            {"week": 4, "items": ["Study 2 deeper resources; iterate project"]},
            {"week": 5, "items": ["Share work for feedback; refine"]},
            {"week": 6, "items": ["Prepare a small portfolio artifact and next steps"]},
        ]


## Chat endpoints removed for landing-page flow


if __name__ == "__main__":
    app.run(debug=True)


