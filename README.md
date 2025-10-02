## AI Mentor Hub

Personal AI mentor that curates resources, plans learning paths, and guides careers from A to Z.

### Table of Contents
- [Overview](#overview)
- [Why Now](#why-now)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation (Clone & Setup)](#installation-clone--setup)
  - [Run the App](#run-the-app)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Tech Stack (Planned)](#tech-stack-planned)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

### Overview
When students or career-switchers want to learn something new—like AI, business, or law—they face a flood of online resources (YouTube tutorials, Udemy courses, blogs). Without prior background, it’s hard to judge which resource is best, in what order to learn topics, or how to connect courses to career goals. Many waste time doing multiple courses just to figure out which is good, or follow a trial-and-error path. People also often lack mentors who can guide them step-by-step through studies, projects, and career moves.

AI Mentor Hub acts as a personal mentor. It analyzes a user’s skills, background, and goals, then:

- **Recommends curated resources**: Filters the noise to suggest the best online courses and materials.
- **Guides learning order**: e.g., Python → Math → Data Analysis → Machine Learning → Deep Learning → NLP.
- **Builds custom study plans**: Generates a tailored plan and schedule.
- **Provides career guidance**: How to approach professors for higher studies, apply for jobs, or choose paths after a course.
- **Gives actionable examples**: e.g., “You want to move into AI policy? Start with this NLP crash course, then read these two blogs, and create a short policy-aware project.”

### Why Now
Traditional mentorship is expensive (platforms like Fearless Grad charge thousands of dollars), and not everyone has access to professors or mentors in their field. At the same time, online learning resources are growing fast but unstructured. Students need a free or affordable AI mentor that combines deep research + guidance + career navigation in one place.

### Features
- Curated resource recommendations
- Guided learning order
- Custom study plans and schedules
- Career guidance with actionable examples

### Getting Started
Follow these steps to run the project locally.

#### Prerequisites
- Python 3.10+
- Git

#### Installation (Clone & Setup)
Open PowerShell and run:

```bash
# 1) Clone the repository
git clone https://github.com/your-organization/AI-Mentor-hub.git

# 2) Move into the project directory
cd AI-Mentor-hub

# 3) (Optional) Create and activate a virtual environment
python -m venv .venv
. .venv/Scripts/Activate.ps1

# 4) Install dependencies (if a requirements.txt exists)
if (Test-Path requirements.txt) { pip install -r requirements.txt }
```

#### Run the App
```bash
python main.py
```

### Usage
- The current prototype prints a simple greeting via `main.py`.
- Future versions will expose a CLI and/or web UI to:
  - Input background, skills, and goals
  - Generate personalized learning paths and schedules
  - Receive curated resource recommendations
  - Get career guidance and actionable next steps

### Project Structure
```text
AI-Mentor-hub/
  ├─ main.py            # Entry point (prototype)
  └─ README.md          # Project overview & setup
```

### Configuration
- No configuration required for the current prototype.
- Planned: `.env` file for API keys (e.g., LLM providers), persistence, and feature flags.

### Tech Stack (Planned)
- Python backend (LLM orchestration, planning engine)
- Optional web frontend (React) or CLI interface
- Data storage for user profiles, goals, and progress

### Roadmap
- Collect user profile (skills, background, goals)
- Curriculum planner with prerequisite graphs
- Resource ranking and deduplication
- Study-plan generation and calendar export
- Career-coaching playbooks and templates
- Progress tracking and feedback loop

### Contributing
Contributions are welcome. Please open an issue to discuss your idea before submitting a PR.

### License
TBD
