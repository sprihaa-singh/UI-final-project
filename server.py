from flask import Flask, render_template, request, jsonify, redirect, url_for # Added redirect, url_for
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
# NOTE: Using session requires a secret key. If you add session logic back, uncomment this.
# app.secret_key = os.urandom(24)

# File paths for data storage
RADICALS_DATA_FILE = 'radicals.json'
USER_DATA_FILE = 'user_data.json' # Original file path used

# Load radicals data
def load_radicals_data():
    # Added basic error handling from Step 3 suggestion
    try:
        with open(RADICALS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {RADICALS_DATA_FILE} not found.")
        return {"radicals": [], "quiz": [], "practice": []}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {RADICALS_DATA_FILE}.")
        return {"radicals": [], "quiz": [], "practice": []}


# Load user data (Original function)
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try: # Added basic error handling
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
             print(f"Error decoding {USER_DATA_FILE}. Starting fresh.")
             # Fallback to creating a new structure if file is corrupt
             return {
                "session_id": str(uuid.uuid4()),
                "start_time": None,
                "learning": [],
                "quiz_answers": [],
                "practice_answers": [] # Added practice answers list
            }
    return {
        "session_id": str(uuid.uuid4()),
        "start_time": None,
        "learning": [],
        "quiz_answers": [],
        "practice_answers": [] # Added practice answers list
    }

# Save user data (Original function)
def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Reset quiz answers (Original function)
def reset_quiz_answers(user_data):
    user_data['quiz_answers'] = []
    return user_data

# ADDED: Reset practice answers function (from Step 3 logic, integrated here)
def reset_practice_answers(user_data):
    user_data['practice_answers'] = []
    return user_data

# Home page route (Integrated reset logic)
@app.route('/', methods=['GET', 'POST'])
def home():
    user_data = load_user_data()
    # Reset quiz and practice answers when the user navigates to the home page
    user_data = reset_quiz_answers(user_data)
    user_data = reset_practice_answers(user_data) # Reset practice
    if request.method == 'POST':
        # Record start time when user clicks "start"
        user_data['start_time'] = datetime.now().isoformat()
        save_user_data(user_data)
        # Redirect to the first lesson using url_for
        return jsonify({"message": "Session started", "redirect": url_for('learn', lesson_id=1)})
    save_user_data(user_data)
    # Pass session_id (or relevant data) to template if needed
    return render_template('home.html', session_id=user_data['session_id'])

# Learning route (MODIFIED GET and POST logic for logging)
@app.route('/learn/<int:lesson_id>', methods=['GET', 'POST'])
def learn(lesson_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data() # Load user data at the start

    num_lessons = len(radicals_data.get('radicals', []))

    if lesson_id < 1 or lesson_id > num_lessons:
        return "Invalid lesson ID", 404

    if request.method == 'POST':
        # --- POST: Log interaction/exit ---
        interaction = {
            "lesson_id": lesson_id,
            "event_type": "next_click", # Clarify event type
            "timestamp": datetime.now().isoformat(),
            "selections": request.json.get('selections', {}) # Still captures selections if implemented
        }
        user_data.setdefault('learning', []).append(interaction)
        # Note: Saving happens once before returning the JSON response below
        print(f"Logged learning event (POST): {interaction}") # Debug print

        # Determine next page
        next_lesson = lesson_id + 1
        if next_lesson <= num_lessons:
            redirect_url = url_for('learn', lesson_id=next_lesson)
        else:
            redirect_url = url_for('practice', practice_id=1)

        save_user_data(user_data) # Save before redirecting
        return jsonify({"message": "Interaction recorded", "redirect": redirect_url})

    # --- GET: Log page entry and render page ---
    # Log the entry event
    entry_event = {
        "lesson_id": lesson_id,
        "event_type": "entry", # Mark this as a page entry event
        "timestamp": datetime.now().isoformat() # Record entry time
    }
    user_data.setdefault('learning', []).append(entry_event)
    save_user_data(user_data) # Save data after logging entry
    print(f"Logged learning event (GET): {entry_event}") # Debug print

    # Get lesson data for rendering
    lesson_data = radicals_data.get('radicals', [])[lesson_id - 1]
    # Render the lesson page
    return render_template('learn.html', lesson_id=lesson_id, lesson=lesson_data)

# --- Practice Routes ---
@app.route('/practice/<int:practice_id>', methods=['GET', 'POST'])
def practice(practice_id):
    radicals_data = load_radicals_data()
    practice_data = radicals_data.get('practice', []) # Get the practice list
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
         return f"Invalid practice ID: {practice_id}", 404

    # Get the specific practice item for this ID
    # (Remember list index is 0-based, practice_id is 1-based)
    practice_item = practice_data[practice_id - 1]

    # Add user data handling later (placeholder)
    # user_data = load_user_data()
    # ... reset logic ...

    # Inside the practice(practice_id) function...
    if request.method == 'POST':
        # --- UPDATED POST Logic ---
        user_data = load_user_data()  # Load user data to save answer
        user_answer = None
        is_correct = False

        if practice_item['type'] == 'recall':
            # Get answer from JSON payload sent by JavaScript
            user_answer = request.json.get('answer', '').strip()
            # Case-insensitive comparison for recall meaning
            correct_answer = practice_item.get('correct_answer', '')
            is_correct = user_answer.lower() == correct_answer.lower()
            print(
                f"Practice ID {practice_id} (Recall): User Answer='{user_answer}', Correct='{correct_answer}', Match={is_correct}")  # Debug print

        elif practice_item['type'] == 'matching':
            # Placeholder for matching logic (Step for later)
            user_answer = request.json.get('pairs', {})  # Expecting {'radical': 'character', ...}
            is_correct = user_answer == practice_item.get('correct_pairs', {})
            print(
                f"Practice ID {practice_id} (Matching): User Answer='{user_answer}', Correct Pairs='{practice_item.get('correct_pairs')}', Match={is_correct}")  # Debug print

        else:
            print(f"Unknown practice type '{practice_item['type']}' received in POST for ID {practice_id}")
            user_answer = "N/A (Unknown Type)"
            is_correct = False

        # Store the result in user_data
        answer_data = {
            "practice_id": practice_id,
            "type": practice_item['type'],
            "user_answer": user_answer,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        # Ensure 'practice_answers' list exists
        user_data.setdefault('practice_answers', []).append(answer_data)
        save_user_data(user_data)  # Save the updated user data

        # Redirect to the feedback page (still using placeholder feedback for now)
        return jsonify(
            {"message": "Answer recorded", "redirect": url_for('practice_feedback', practice_id=practice_id)})
        # --- End UPDATED POST Logic ---


    # --- MODIFIED GET Request Logic ---
    # Render the appropriate template based on the practice item type
    if practice_item['type'] == 'recall':
        # Render the new recall template
        return render_template('practice_recall.html',
                               practice_id=practice_id,
                               item=practice_item,
                               total_items=num_practice)
    # --- MODIFIED ELIF Block ---
    elif practice_item['type'] == 'matching':
        # Render the new matching template
        # Make sure to pass the necessary item data (radicals, characters)
        return render_template('practice_matching.html',
                               practice_id=practice_id,
                               item=practice_item, # Contains radicals, characters list
                               total_items=num_practice)
    # --- End MODIFIED ELIF Block ---
    else:
        # Fallback for unknown types
        return f"Unknown practice type '{practice_item['type']}' for ID {practice_id}", 500


@app.route('/practice/feedback/<int:practice_id>')
def practice_feedback(practice_id):
    # --- UPDATED Feedback Logic ---
    radicals_data = load_radicals_data()
    practice_data = radicals_data.get('practice', [])
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
         return f"Invalid practice ID for feedback: {practice_id}", 404

    # Load user data to find the submitted answer
    user_data = load_user_data()
    user_answers = user_data.get('practice_answers', [])

    # Find the LAST answer submitted for this specific practice_id
    last_answer_data = None
    for answer in reversed(user_answers):
        # Use .get() for safer access, comparing practice_id
        if answer.get('practice_id') == practice_id:
            last_answer_data = answer
            break # Found the most recent answer for this ID

    if not last_answer_data:
        # Handle case where feedback page is accessed directly without an answer
        # Or if practice_answers hasn't been populated correctly yet
        print(f"Warning: No answer found for practice_id {practice_id} in user_data.")
        # Redirect back to the question page as a fallback
        return redirect(url_for('practice', practice_id=practice_id))

    # Get the corresponding practice item details from radicals.json
    practice_item = practice_data[practice_id - 1]

    # Get the correct answer details for display
    correct_answer_details = None
    if practice_item['type'] == 'recall':
        correct_answer_details = practice_item.get('correct_answer')
    elif practice_item['type'] == 'matching':
        correct_answer_details = practice_item.get('correct_pairs')

    # Calculate next URL (same logic as before)
    next_practice_id = practice_id + 1
    if next_practice_id > num_practice:
        next_url = url_for('quiz', question_id=1) # Go to quiz after last practice item
    else:
        next_url = url_for('practice', practice_id=next_practice_id)

    # Render the new feedback template with all necessary data
    return render_template('practice_feedback.html',
                           practice_id=practice_id,
                           item=practice_item,                 # Pass the practice item data (radical, examples, type)
                           user_answer_data=last_answer_data,  # Pass the user's specific answer details (answer, is_correct)
                           correct_answer_details=correct_answer_details, # Pass the correct answer string or dict
                           next_url=next_url,                  # Pass the URL for the 'Next' button
                           total_items=num_practice)           # Pass the total number of practice items
    # --- End UPDATED Feedback Logic ---

# Quiz route (Original logic, added url_for)
@app.route('/quiz/<int:question_id>', methods=['GET', 'POST'])
def quiz(question_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data()
    quiz_data = radicals_data.get('quiz', []) # Use .get for safety
    num_questions = len(quiz_data)

    # Original reset logic
    if question_id == 1 and request.method == 'GET': # Simplified original check
        user_data = reset_quiz_answers(user_data)
        save_user_data(user_data)

    # Validate question_id
    if question_id < 1 or question_id > num_questions:
        return "Invalid question ID", 404

    quiz_question = quiz_data[question_id - 1]

    if request.method == 'POST':
        # Store quiz answer
        user_answer = request.json.get('answer')
        is_correct = user_answer == quiz_question['correct_answer']

        answer_data = {
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": quiz_question['correct_answer'],
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        # Ensure 'quiz_answers' list exists
        user_data.setdefault('quiz_answers', []).append(answer_data)
        save_user_data(user_data)

        # Determine next page
        next_question = question_id + 1
        if next_question <= num_questions:
            # Use url_for
            return jsonify({"message": "Answer recorded", "redirect": url_for('quiz', question_id=next_question)})
        else:
             # Use url_for
            return jsonify({"message": "Quiz complete", "redirect": url_for('results')})

    # GET: Render quiz question
    # Pass total_questions to template if needed
    return render_template('quiz.html', question_id=question_id, question=quiz_question, total_questions=num_questions)

# Results route (Original logic, added data loading safety)
@app.route('/results', methods=['GET'])
def results():
    user_data = load_user_data()
    quiz_answers = user_data.get('quiz_answers', [])

    # Calculate score for the current attempt (using original logic)
    # Assuming 5 questions based on original code
    num_questions_in_quiz = 5 # Make this dynamic if quiz length changes
    current_attempt_answers = quiz_answers[-num_questions_in_quiz:] if len(quiz_answers) >= num_questions_in_quiz else quiz_answers

    correct_count = sum(1 for answer in current_attempt_answers if answer.get('is_correct')) # Use .get for safety
    total_questions_attempted = len(current_attempt_answers) # Use attempted count
    score = (correct_count / total_questions_attempted * 100) if total_questions_attempted > 0 else 0

    return render_template('results.html',
                           score=score,
                           total_questions=total_questions_attempted, # Use attempted count
                           correct_answers=correct_count,
                           answers=current_attempt_answers)

if __name__ == '__main__':
    # Remember to set debug=False for production
    app.run(debug=True, port=5001)