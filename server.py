from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# File paths for data storage
RADICALS_DATA_FILE = 'radicals.json'
USER_DATA_FILE = 'user_data.json'

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
            return {
                "session_id": str(uuid.uuid4()),
                "start_time": None,
                "learning": [],
                "quiz_answers": [],
                "practice_answers": []
            }
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

# Home page route
@app.route('/', methods=['GET', 'POST'])
def home():
    user_data = load_user_data()
    user_data = reset_quiz_answers(user_data)
    user_data = reset_practice_answers(user_data)
    
    if request.method == 'POST':
        user_data['start_time'] = datetime.now().isoformat()
        save_user_data(user_data)
        return jsonify({"message": "Session started", "redirect": url_for('learn', lesson_id=1)})
    
    save_user_data(user_data)
    return render_template('home.html', session_id=user_data['session_id'])

# Learning route
@app.route('/learn/<int:lesson_id>', methods=['GET', 'POST'])
def learn(lesson_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data()

    num_lessons = len(radicals_data.get('radicals', []))

    if lesson_id < 1 or lesson_id > num_lessons:
        return "Invalid lesson ID", 404

    if request.method == 'POST':
        interaction = {
            "lesson_id": lesson_id,
            "event_type": "next_click",
            "timestamp": datetime.now().isoformat(),
            "selections": request.json.get('selections', {})
        }
        user_data.setdefault('learning', []).append(interaction)

        next_lesson = lesson_id + 1
        if next_lesson <= num_lessons:
            redirect_url = url_for('learn', lesson_id=next_lesson)
        else:
            redirect_url = url_for('practice', practice_id=1)

        save_user_data(user_data)
        return jsonify({"message": "Interaction recorded", "redirect": redirect_url})


    entry_event = {
        "lesson_id": lesson_id,
        "event_type": "entry",
        "timestamp": datetime.now().isoformat()
    }
    user_data.setdefault('learning', []).append(entry_event)
    save_user_data(user_data)

    lesson_data = radicals_data.get('radicals', [])[lesson_id - 1]
    radical = lesson_data['radical']  # Get the radical from the lesson data

    return render_template('learn.html', lesson_id=lesson_id, lesson=lesson_data, radical=radical)


# Practice route
@app.route('/practice/<int:practice_id>', methods=['GET', 'POST'])
def practice(practice_id):
    radicals_data = load_radicals_data()
    practice_data = radicals_data.get('practice', [])
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
        return f"Invalid practice ID: {practice_id}", 404

    practice_item = practice_data[practice_id - 1]

    if request.method == 'POST':
        user_data = load_user_data()
        user_answer = None
        is_correct = False

        if practice_item['type'] == 'recall':
            user_answer = request.json.get('answer', '').strip()
            correct_answer = practice_item.get('correct_answer', '')
            is_correct = user_answer.lower() == correct_answer.lower()

        elif practice_item['type'] == 'matching':
            user_answer = request.json.get('pairs', {})
            is_correct = user_answer == practice_item.get('correct_pairs', {})

        answer_data = {
            "practice_id": practice_id,
            "type": practice_item['type'],
            "user_answer": user_answer,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        user_data.setdefault('practice_answers', []).append(answer_data)
        save_user_data(user_data)

        return jsonify(
            {"message": "Answer recorded", "redirect": url_for('practice_feedback', practice_id=practice_id)})

    if practice_item['type'] == 'recall':
        return render_template('practice_recall.html', practice_id=practice_id, item=practice_item, total_items=num_practice)
    elif practice_item['type'] == 'matching':
        return render_template('practice_matching.html', practice_id=practice_id, item=practice_item, total_items=num_practice)
    else:
        return f"Unknown practice type '{practice_item['type']}' for ID {practice_id}", 500

# Practice feedback route
@app.route('/practice/feedback/<int:practice_id>')
def practice_feedback(practice_id):
    radicals_data = load_radicals_data()
    practice_data = radicals_data.get('practice', [])
    num_practice = len(practice_data)

    if practice_id < 1 or practice_id > num_practice:
        return f"Invalid practice ID for feedback: {practice_id}", 404

    user_data = load_user_data()
    user_answers = user_data.get('practice_answers', [])

    last_answer_data = None
    for answer in reversed(user_answers):
        if answer.get('practice_id') == practice_id:
            last_answer_data = answer
            break

    if not last_answer_data:
        return redirect(url_for('practice', practice_id=practice_id))

    practice_item = practice_data[practice_id - 1]
    correct_answer_details = practice_item.get('correct_answer') if practice_item['type'] == 'recall' else practice_item.get('correct_pairs')

    next_practice_id = practice_id + 1
    if next_practice_id > num_practice:
        next_url = url_for('quiz', question_id=1)
    else:
        next_url = url_for('practice', practice_id=next_practice_id)

    return render_template('practice_feedback.html',
                           practice_id=practice_id,
                           item=practice_item,
                           user_answer_data=last_answer_data,
                           correct_answer_details=correct_answer_details,
                           next_url=next_url,
                           total_items=num_practice)

# Quiz route
@app.route('/quiz/<int:question_id>', methods=['GET', 'POST'])
def quiz(question_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data()
    quiz_data = radicals_data.get('quiz', [])
    num_questions = len(quiz_data)

    if question_id == 1 and request.method == 'GET':
        user_data = reset_quiz_answers(user_data)
        save_user_data(user_data)

    if question_id < 1 or question_id > num_questions:
        return "Invalid question ID", 404

    quiz_question = quiz_data[question_id - 1]

    if request.method == 'POST':
        user_answer = request.json.get('answer')
        is_correct = user_answer == quiz_question['correct_answer']

        answer_data = {
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": quiz_question['correct_answer'],
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        user_data.setdefault('quiz_answers', []).append(answer_data)
        save_user_data(user_data)

        next_question = question_id + 1
        if next_question <= num_questions:
            return jsonify({"message": "Answer recorded", "redirect": url_for('quiz', question_id=next_question)})
        else:
            return jsonify({"message": "Quiz complete", "redirect": url_for('results')})

    return render_template('quiz.html', question_id=question_id, question=quiz_question, total_questions=num_questions)

# Results route
@app.route('/results', methods=['GET'])
def results():
    user_data = load_user_data()
    quiz_answers = user_data.get('quiz_answers', [])

    num_questions_in_quiz = 5
    current_attempt_answers = quiz_answers[-num_questions_in_quiz:] if len(quiz_answers) >= num_questions_in_quiz else quiz_answers

    correct_count = sum(1 for answer in current_attempt_answers if answer.get('is_correct'))
    total_questions_attempted = len(current_attempt_answers)
    score = (correct_count / total_questions_attempted * 100) if total_questions_attempted > 0 else 0

    return render_template('results.html',
                           score=score,
                           total_questions=total_questions_attempted,
                           correct_answers=correct_count,
                           answers=current_attempt_answers)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
