__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import tempfile
from auth import AuthManager
from ingestion import IngestionManager
from generator import QuizGenerator
from evaluator import AnswerEvaluator
from topic_discovery import TopicManager

# Initialize Managers
auth_manager = AuthManager()
ingestion_manager = IngestionManager()
quiz_generator = QuizGenerator()
evaluator = AnswerEvaluator()
topic_manager = TopicManager()

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = "login"
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = []
if 'current_question_index' not in st.session_state:
    st.session_state['current_question_index'] = 0
if 'user_answers' not in st.session_state:
    st.session_state['user_answers'] = {}
if 'score' not in st.session_state:
    st.session_state['score'] = 0

def login_page():
    st.title("Knowval AI - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if auth_manager.login_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['page'] = "dashboard"
                st.rerun()
            else:
                st.error("Invalid credentials")
                
    with tab2:
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            if auth_manager.register_user(new_user, new_pass):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists")

def dashboard_page():
    st.title(f"Welcome, {st.session_state['username']}!")
    
    # Sidebar for Logout
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['page'] = "login"
        st.rerun()
        
    st.header("1. Upload Documents")
    uploaded_files = st.file_uploader("Upload PDF, TXT, DOCX, ZIP", accept_multiple_files=True)
    
    if st.button("Ingest Files"):
        if uploaded_files:
            file_paths = []
            with st.spinner("Ingesting documents..."):
                # Save uploaded files to temp directory
                temp_dir = tempfile.mkdtemp()
                for uploaded_file in uploaded_files:
                    path = os.path.join(temp_dir, uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(path)
                
                ingestion_manager.ingest_files(file_paths)
                st.success("Ingestion successful!")
        else:
            st.warning("Please upload files first.")

    st.header("2. Quiz Configuration")
    
    mode = st.radio("Select Mode", ["Single Shot", "Multilevel"])
    
    topic = "General Knowledge"
    if mode == "Multilevel":
        if st.button("Discover Topics"):
            with st.spinner("Discovering topics..."):
                topics = topic_manager.discover_topics()
                st.session_state['discovered_topics'] = topics
        
        if 'discovered_topics' in st.session_state:
            topic = st.selectbox("Select Topic", st.session_state['discovered_topics'])
    else:
        topic = st.text_input("Enter Topic", "General Knowledge")
        
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    
    if st.button("Start Quiz"):
        with st.spinner("Generating Quiz..."):
            # Pass num_chunks=None for dynamic sizing
            quiz = quiz_generator.generate_quiz(topic, num_chunks=None, difficulty=difficulty)
            if quiz:
                st.session_state['quiz_data'] = quiz
                st.session_state['current_question_index'] = 0
                st.session_state['user_answers'] = {}
                st.session_state['score'] = 0
                st.session_state['answer_submitted'] = False
                st.session_state['page'] = "quiz"
                st.rerun()
            else:
                st.error("Failed to generate quiz. Try a different topic.")

def quiz_page():
    st.title("Knowval AI - Quiz")
    
    quiz = st.session_state['quiz_data']
    idx = st.session_state['current_question_index']
    
    # Initialize answer_submitted state for the current question
    if 'answer_submitted' not in st.session_state:
        st.session_state['answer_submitted'] = False
    
    if idx < len(quiz):
        question_data = quiz[idx]
        st.subheader(f"Question {idx + 1}/{len(quiz)}")
        st.write(question_data['question'])
        
        options = question_data['options']
        # Disable radio button if answer is already submitted
        choice = st.radio(
            "Choose an option:", 
            list(options.keys()), 
            format_func=lambda x: f"{x}) {options[x]}", 
            key=f"q_{idx}",
            disabled=st.session_state['answer_submitted']
        )
        
        # Show Submit button only if not submitted yet
        if not st.session_state['answer_submitted']:
            if st.button("Submit Answer"):
                correct_answer = question_data['correct_answer']
                explanation = question_data['explanation']
                
                # Store result
                st.session_state['user_answers'][idx] = {
                    "question": question_data['question'],
                    "user_choice": choice,
                    "correct_choice": correct_answer,
                    "is_correct": choice == correct_answer,
                    "explanation": explanation
                }
                
                if choice == correct_answer:
                    st.session_state['score'] += 10
                
                st.session_state['answer_submitted'] = True
                st.rerun()
        
        # If submitted, show feedback and Next button
        if st.session_state['answer_submitted']:
            result = st.session_state['user_answers'][idx]
            if result['is_correct']:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. The correct answer was {result['correct_choice']}.")
            
            st.info(f"Explanation: {result['explanation']}")
            
            if st.button("Next Question"):
                st.session_state['current_question_index'] += 1
                st.session_state['answer_submitted'] = False
                st.rerun()
    else:
        st.session_state['page'] = "results"
        st.rerun()

def results_page():
    st.title("Quiz Results")
    
    total_score = st.session_state['score']
    max_score = len(st.session_state['quiz_data']) * 10
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    st.metric("Total Score", f"{total_score}/{max_score}", f"{percentage:.1f}%")
    
    if percentage >= 80:
        st.success("Performance: Excellent!")
    elif percentage >= 50:
        st.warning("Performance: Good.")
    else:
        st.error("Performance: Needs Improvement.")
        
    st.subheader("Review")
    for idx, res in st.session_state['user_answers'].items():
        with st.expander(f"Q{idx+1}: {res['question']} ({'Correct' if res['is_correct'] else 'Incorrect'})"):
            st.write(f"**Your Answer:** {res['user_choice']}")
            st.write(f"**Correct Answer:** {res['correct_choice']}")
            st.write(f"**Explanation:** {res['explanation']}")
            
    if st.button("Back to Dashboard"):
        st.session_state['page'] = "dashboard"
        st.rerun()

# Main App Logic
if st.session_state['page'] == "login":
    login_page()
elif st.session_state['page'] == "dashboard":
    dashboard_page()
elif st.session_state['page'] == "quiz":
    quiz_page()
elif st.session_state['page'] == "results":
    results_page()
