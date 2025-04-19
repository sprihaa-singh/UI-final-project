from flask import Flask, render_template, request, jsonify
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
    with open(RADICALS_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "session_id": str(uuid.uuid4()),
        "start_time": None,
        "learning": [],
        "quiz_answers": []
    }

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Reset quiz answers
def reset_quiz_answers(user_data):
    user_data['quiz_answers'] = []
    return user_data

# Home page route
@app.route('/', methods=['GET', 'POST'])
def home():
    user_data = load_user_data()
    # Reset quiz answers when the user navigates to the home page
    user_data = reset_quiz_answers(user_data)
    if request.method == 'POST':
        # Record start time when user clicks "start"
        user_data['start_time'] = datetime.now().isoformat()
        save_user_data(user_data)
        return jsonify({"message": "Session started", "redirect": "/learn/1"})
    save_user_data(user_data)
    return render_template('home.html', session_id=user_data['session_id'])

# Learning route
@app.route('/learn/<int:lesson_id>', methods=['GET', 'POST'])
def learn(lesson_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data()
    
    # Reset quiz answers when the user navigates to a learning page
    user_data = reset_quiz_answers(user_data)
    
    # Validate lesson_id
    if lesson_id < 1 or lesson_id > len(radicals_data['radicals']):
        return "Invalid lesson ID", 404
    
    if request.method == 'POST':
        # Store user interaction (e.g., time entered, selections)
        interaction = {
            "lesson_id": lesson_id,
            "timestamp": datetime.now().isoformat(),
            "selections": request.json.get('selections', {})
        }
        user_data['learning'].append(interaction)
        save_user_data(user_data)
        
        # Determine next page
        next_lesson = lesson_id + 1
        if next_lesson <= len(radicals_data['radicals']):
            return jsonify({"message": "Interaction recorded", "redirect": f"/learn/{next_lesson}"})
        else:
            return jsonify({"message": "Lesson complete", "redirect": "/quiz/1"})
    
    save_user_data(user_data)
    # GET: Render lesson page
    lesson_data = radicals_data['radicals'][lesson_id - 1]
    return render_template('learn.html', lesson_id=lesson_id, lesson=lesson_data)

# Quiz route
@app.route('/quiz/<int:question_id>', methods=['GET', 'POST'])
def quiz(question_id):
    radicals_data = load_radicals_data()
    user_data = load_user_data()
    
    # Reset quiz answers when starting the quiz (question_id == 1)
    if question_id == 1:
        user_data = reset_quiz_answers(user_data)
        save_user_data(user_data)
    
    # Validate question_id
    if question_id < 1 or question_id > len(radicals_data['quiz']):
        return "Invalid question ID", 404
    
    if request.method == 'POST':
        # Store quiz answer
        user_answer = request.json.get('answer')
        quiz_question = radicals_data['quiz'][question_id - 1]
        is_correct = user_answer == quiz_question['correct_answer']
        
        answer_data = {
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": quiz_question['correct_answer'],
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat()
        }
        user_data['quiz_answers'].append(answer_data)
        save_user_data(user_data)
        
        # Determine next page
        next_question = question_id + 1
        if next_question <= len(radicals_data['quiz']):
            return jsonify({"message": "Answer recorded", "redirect": f"/quiz/{next_question}"})
        else:
            return jsonify({"message": "Quiz complete", "redirect": "/results"})
    
    # GET: Render quiz question
    quiz_question = radicals_data['quiz'][question_id - 1]
    return render_template('quiz.html', question_id=question_id, question=quiz_question)

# Results route
@app.route('/results', methods=['GET'])
def results():
    user_data = load_user_data()
    quiz_answers = user_data.get('quiz_answers', [])
    
    # Calculate score for the current attempt (last 5 answers, since there are 5 questions)
    current_attempt_answers = quiz_answers[-5:] if len(quiz_answers) >= 5 else quiz_answers
    correct_count = sum(1 for answer in current_attempt_answers if answer['is_correct'])
    total_questions = len(current_attempt_answers)
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    return render_template('results.html', score=score, total_questions=total_questions, correct_answers=correct_count, answers=current_attempt_answers)

if __name__ == '__main__':
    app.run(debug=True, port=5001)