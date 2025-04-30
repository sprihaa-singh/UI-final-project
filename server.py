from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# File paths for data storage
RADICALS_DATA_FILE = 'radicals.json'
USER_DATA_FILE = 'user_data.json'

# --- Helper Functions (Load/Save Data, Reset Answers) ---

# Load radicals data
def load_radicals_data():
    try:
        with open(RADICALS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {RADICALS_DATA_FILE} not found.")
        return {"radicals": [], "quiz": [], "practice": []}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {RADICALS_DATA_FILE}.")
        return {"radicals": [], "quiz": [], "practice": []}

# Load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {USER_DATA_FILE}. Starting fresh.")
            # Fallback to default structure
            pass
    # Default structure if file doesn't exist or is invalid
    return {
        "session_id": str(uuid.uuid4()),
        "start_time": None,
        "learning": [],
        "quiz_answers": [],
        "practice_answers": []
    }

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Reset quiz answers
def reset_quiz_answers(user_data):
    user_data['quiz_answers'] = []
    return user_data

# Reset practice answers
def reset_practice_answers(user_data):
    user_data['practice_answers'] = []
    return user_data

# --- Flask Routes ---

# Home page route
@app.route('/', methods=['GET', 'POST'])
def home():
    user_data = load_user_data()
    radicals_data = load_radicals_data() # Load radicals data
    radicals_list = radicals_data.get('radicals', []) # Get the list for the dropdown

    # Reset data on initial visit (GET) or explicit start (POST)
    user_data = reset_quiz_answers(user_data)
    user_data = reset_practice_answers(user_data)

    if request.method == 'POST':
        user_data['start_time'] = datetime.now().isoformat()
        save_user_data(user_data)
        # Redirect to the first learn page; 'learn' route will handle loading radicals_list
        return jsonify({"message": "Session started", "redirect": url_for('learn', lesson_id=1, part=0)})

    # Handle GET request (initial page load)
    save_user_data(user_data) # Save potentially reset data
    # Pass radicals_list needed by base.html
    return render_template('home.html',
                           session_id=user_data.get('session_id', ''),
                           radicals_list=radicals_list)

# Learning route
# Replace the existing '/learn/<int:lesson_id>' route
@app.route('/learn/<int:lesson_id>-<int:part>', methods=['GET', 'POST'])
def learn(lesson_id, part): # Add part parameter
    radicals_data = load_radicals_data()
    user_data = load_user_data()
    radicals_list = radicals_data.get('radicals', [])
    num_lessons = len(radicals_list)

    # Validate lesson_id and part
    if lesson_id < 1 or lesson_id > num_lessons or part not in [0, 1]:
        return "Invalid lesson ID or part", 404

    lesson_data = radicals_list[lesson_id - 1] # Get data for the radical

    # Handle POST request (clicking 'Next')
    if request.method == 'POST':
        interaction = {
            "lesson_id": lesson_id,
            "part": part, # Record which part was completed
            "event_type": "next_click",
            "timestamp": datetime.now().isoformat(),
            "selections": request.json.get('selections', {}) # Keep if tracing data is sent
        }
        user_data.setdefault('learning', []).append(interaction)
        save_user_data(user_data)

        # Determine the next URL based on current lesson_id and part
        redirect_url = None
        if part == 0:
            # Go from <n>-0 to <n>-1
            redirect_url = url_for('learn', lesson_id=lesson_id, part=1)
        elif part == 1:
            next_lesson_id = lesson_id + 1
            if next_lesson_id <= num_lessons:
                # Go from <n>-1 to <n+1>-0
                redirect_url = url_for('learn', lesson_id=next_lesson_id, part=0)
            else:
                # Go from last lesson's part 1 to practice
                redirect_url = url_for('practice', practice_id=1)

        return jsonify({"message": "Interaction recorded", "redirect": redirect_url})

    # Handle GET request (displaying the lesson page)
    entry_event = {
        "lesson_id": lesson_id,
        "part": part, # Record which part was viewed
        "event_type": "entry",
        "timestamp": datetime.now().isoformat()
    }
    user_data.setdefault('learning', []).append(entry_event)
    save_user_data(user_data)

    # Choose the correct template based on 'part'
    if part == 0:
        template_name = 'learn_part0.html'
    else: # part == 1
        template_name = 'learn_part1.html'

    return render_template(template_name,
                           lesson_id=lesson_id,
                           part=part,
                           lesson=lesson_data,
                           radicals_list=radicals_list) # Pass radicals_list for base.html

# Practice route
@app.route('/practice/<int:practice_id>', methods=['GET', 'POST'])
def practice(practice_id):
    radicals_data = load_radicals_data() # Load radicals data
    practice_data = radicals_data.get('practice', [])
    radicals_list = radicals_data.get('radicals', []) # Get the list for the dropdown
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
        return f"Invalid practice ID: {practice_id}", 404

    practice_item = practice_data[practice_id - 1]

    # Handle POST request (submitting an answer)
    if request.method == 'POST':
        user_data = load_user_data()
        user_answer = None
        is_correct = False

        try:
            if practice_item['type'] == 'recall':
                user_answer = request.json.get('answer', '').strip()
                correct_answer = practice_item.get('correct_answer', '')
                is_correct = user_answer.lower() == correct_answer.lower()

            elif practice_item['type'] == 'matching':
                user_answer = request.json.get('pairs', {}) # Expecting a dictionary
                correct_pairs = practice_item.get('correct_pairs', {})
                # Simple equality check for dictionaries
                is_correct = user_answer == correct_pairs
            else:
                 # Handle unknown type if necessary
                 print(f"Unknown practice type: {practice_item.get('type')}")

            answer_data = {
                "practice_id": practice_id,
                "type": practice_item.get('type'),
                "user_answer": user_answer,
                "is_correct": is_correct,
                "timestamp": datetime.now().isoformat()
            }
            user_data.setdefault('practice_answers', []).append(answer_data)
            save_user_data(user_data)

            # Redirect to feedback page for this practice item
            return jsonify(
                {"message": "Answer recorded", "redirect": url_for('practice_feedback', practice_id=practice_id)})

        except Exception as e:
            print(f"Error processing practice submission: {e}")
            # Return an error response if something goes wrong
            return jsonify({"message": f"Error processing answer: {e}"}), 500


    # Handle GET request (displaying the practice question)
    # Pass radicals_list needed by base.html
    template_name = f"practice_{practice_item.get('type', 'unknown')}.html"
    # Check if template exists for safety, or handle unknown type
    if practice_item.get('type') in ['recall', 'matching']:
        return render_template(template_name,
                           practice_id=practice_id,
                           item=practice_item,
                           total_items=num_practice,
                           radicals_list=radicals_list)
    else:
        return f"Unknown or unsupported practice type '{practice_item.get('type')}' for ID {practice_id}", 500


# Practice feedback route
@app.route('/practice/feedback/<int:practice_id>')
def practice_feedback(practice_id):
    radicals_data = load_radicals_data() # Load radicals data
    practice_data = radicals_data.get('practice', [])
    radicals_list = radicals_data.get('radicals', []) # Get the list for the dropdown
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
        return f"Invalid practice ID for feedback: {practice_id}", 404

    user_data = load_user_data()
    user_answers = user_data.get('practice_answers', [])

    # Find the most recent answer for this specific practice_id
    last_answer_data = None
    for answer in reversed(user_answers):
        if answer.get('practice_id') == practice_id:
            last_answer_data = answer
            break

    # If no answer found for this ID, redirect back to the question
    if not last_answer_data:
        return redirect(url_for('practice', practice_id=practice_id))

    practice_item = practice_data[practice_id - 1]
    correct_answer_details = None
    if practice_item.get('type') == 'recall':
        correct_answer_details = practice_item.get('correct_answer')
    elif practice_item.get('type') == 'matching':
         correct_answer_details = practice_item.get('correct_pairs')

    # Determine URL for the 'Next' button
    next_practice_id = practice_id + 1
    if next_practice_id > num_practice:
        # After last practice item, go to the first quiz question
        next_url = url_for('quiz', question_id=1)
    else:
        # Go to the next practice item
        next_url = url_for('practice', practice_id=next_practice_id)

    # Pass radicals_list needed by base.html
    return render_template('practice_feedback.html',
                           practice_id=practice_id,
                           item=practice_item,
                           user_answer_data=last_answer_data,
                           correct_answer_details=correct_answer_details,
                           next_url=next_url,
                           total_items=num_practice,
                           radicals_list=radicals_list)


# Quiz route
@app.route('/quiz/<int:question_id>', methods=['GET', 'POST'])
def quiz(question_id):
    radicals_data = load_radicals_data() # Load radicals data
    user_data = load_user_data()
    quiz_data = radicals_data.get('quiz', [])
    radicals_list = radicals_data.get('radicals', []) # Get the list for the dropdown
    num_questions = len(quiz_data)

    # Reset answers only when starting the quiz (GET request for question 1)
    if question_id == 1 and request.method == 'GET':
        user_data = reset_quiz_answers(user_data)
        save_user_data(user_data) # Save the reset state

    if question_id < 1 or question_id > num_questions:
        return "Invalid question ID", 404

    quiz_question = quiz_data[question_id - 1]

    # Handle POST request (submitting an answer)
    if request.method == 'POST':
        user_answer = request.json.get('answer')
        is_correct = False
        # Ensure correct_answer exists before comparing
        if 'correct_answer' in quiz_question:
            is_correct = (user_answer == quiz_question['correct_answer'])

        answer_data = {
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": quiz_question.get('correct_answer', 'N/A'), # Handle missing key
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        user_data.setdefault('quiz_answers', []).append(answer_data)
        save_user_data(user_data)

        next_question = question_id + 1
        if next_question <= num_questions:
            redirect_url = url_for('quiz', question_id=next_question)
        else:
            # End of quiz, go to results
            redirect_url = url_for('results')

        return jsonify({"message": "Answer recorded", "redirect": redirect_url})

    # Handle GET request (displaying the quiz question)
    # Pass radicals_list needed by base.html
    return render_template('quiz.html',
                           question_id=question_id,
                           question=quiz_question,
                           total_questions=num_questions,
                           radicals_list=radicals_list)


# Results route
@app.route('/results', methods=['GET'])
def results():
    user_data = load_user_data()
    radicals_data = load_radicals_data() # Load radicals data
    radicals_list = radicals_data.get('radicals', []) # Get the list for the dropdown
    quiz_answers = user_data.get('quiz_answers', [])
    quiz_data = radicals_data.get('quiz', [])
    num_questions_in_quiz = len(quiz_data) # Use actual number of quiz questions

    # Ensure we only consider the answers from the most recent attempt
    # (Handles cases where user might go back and retake the quiz without resetting via home)
    current_attempt_answers = []
    if len(quiz_answers) >= num_questions_in_quiz:
        current_attempt_answers = quiz_answers[-num_questions_in_quiz:]
    else:
         # If fewer answers than questions, consider all recorded answers for this session
         current_attempt_answers = quiz_answers

    correct_count = sum(1 for answer in current_attempt_answers if answer.get('is_correct'))
    total_questions_attempted = len(current_attempt_answers)
    score = (correct_count / total_questions_attempted * 100) if total_questions_attempted > 0 else 0

    # Pass radicals_list needed by base.html
    return render_template('results.html',
                           score=score,
                           total_questions=total_questions_attempted, # Show questions answered in this attempt
                           correct_answers=correct_count,
                           answers=current_attempt_answers,
                           radicals_list=radicals_list)

# --- Main Execution Guard ---
if __name__ == '__main__':
    # Use a port other than the default 5000 if needed
    app.run(debug=True, port=5001)
