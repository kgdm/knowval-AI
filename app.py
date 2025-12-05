__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import extra_streamlit_components as stx
import os
import tempfile
import uuid
import datetime
from auth import AuthManager
from ingestion import IngestionManager
from generator import QuizGenerator
from evaluator import AnswerEvaluator
from topic_discovery import TopicManager

from session_manager import SessionManager

# Initialize Managers
auth_manager = AuthManager()
ingestion_manager = IngestionManager()
quiz_generator = QuizGenerator()
evaluator = AnswerEvaluator()
topic_manager = TopicManager()
session_manager = SessionManager()

# Initialize Cookie Manager
cookie_manager = stx.CookieManager()

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    
# Check for auth cookie (Auto-login)
if not st.session_state['logged_in']:
    try:
        auth_token = cookie_manager.get(cookie="auth_token")
        if auth_token:
            st.session_state['logged_in'] = True
            st.session_state['username'] = auth_token
            st.session_state['page'] = "dashboard"
            # No rerun here to avoid infinite loops if cookie reading is delayed, 
            # but usually rerun is needed to update UI. 
            # Let's rely on the main logic flow or force a rerun if needed.
            st.rerun()
    except Exception as e:
        print(f"Cookie read error: {e}")

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
if 'current_session_id' not in st.session_state:
    st.session_state['current_session_id'] = None

def login_page():
    st.title("Knowval AI - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Email", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if auth_manager.login_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['page'] = "dashboard"
                # Set cookie (expires in 30 days)
                cookie_manager.set("auth_token", username, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("---")
        if st.button("Login with Google"):
            auth_url, error = auth_manager.google_login()
            if auth_url:
                st.link_button("Continue to Google", auth_url)
            else:
                st.error(f"Google Login Error: {error}")
                st.info("Ensure 'client_secret.json' is in the root directory.")

    with tab2:
        new_user = st.text_input("Email", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            result = auth_manager.register_user(new_user, new_pass)
            if result is True:
                st.success("Registration successful! Please login.")
            elif isinstance(result, str):
                st.error(result)
            else:
                st.error("Registration failed.")

def dashboard_page():
    st.title(f"Welcome, {st.session_state['username']}!")
    
    # Sidebar for Session Management
    st.sidebar.header("Chat Sessions")
    
    # Create New Session (Deferred)
    if st.sidebar.button("New Quiz Session"):
        st.session_state['current_session_id'] = str(uuid.uuid4())
        st.session_state['session_saved'] = False
        st.session_state['quiz_data'] = []
        st.rerun()
            
    # List Existing Sessions
    user_sessions = session_manager.get_user_sessions(st.session_state['username'])
    session_options = {s['id']: f"{s['name']} ({s['created_at'][:10]})" for s in user_sessions}
    
    # Auto-select most recent if none selected
    if not st.session_state['current_session_id'] and user_sessions:
        st.session_state['current_session_id'] = user_sessions[0]['id']
        st.session_state['session_saved'] = True
        
    if user_sessions:
        # Filter out current session if it's not saved yet (so it doesn't appear in list)
        display_options = list(session_options.keys())
        
        # If current session is saved, ensure it's in the list
        if st.session_state.get('session_saved') and st.session_state['current_session_id'] in session_options:
             pass
        # If current session is NOT saved, it won't be in user_sessions yet, which is correct.
        
        selected_session_id = st.sidebar.selectbox(
            "Select Session", 
            options=display_options, 
            format_func=lambda x: session_options[x],
            index=display_options.index(st.session_state['current_session_id']) if st.session_state['current_session_id'] in display_options else 0
        )
        
        if selected_session_id != st.session_state['current_session_id']:
            st.session_state['current_session_id'] = selected_session_id
            st.session_state['session_saved'] = True
            
            # Load quiz state for the selected session
            saved_state = session_manager.load_quiz_state(selected_session_id)
            if saved_state:
                st.session_state['quiz_data'] = saved_state['quiz_data']
                st.session_state['current_question_index'] = saved_state['current_index']
                st.session_state['user_answers'] = saved_state['user_answers']
                st.session_state['score'] = saved_state['score']
                st.session_state['answer_submitted'] = saved_state['answer_submitted']
                st.session_state['page'] = "quiz"
            else:
                st.session_state['quiz_data'] = [] # Clear quiz data if no state found
                st.session_state['page'] = "dashboard"
                
            st.rerun()
    else:
        if not st.session_state['current_session_id']:
             # Create default session ID (deferred)
            st.session_state['current_session_id'] = str(uuid.uuid4())
            st.session_state['session_saved'] = False
            st.rerun()

    current_session_name = session_options.get(st.session_state['current_session_id'], "New Quiz Session (Unsaved)")
    st.markdown(f"**Current Session:** {current_session_name}")

    # Sidebar for Logout
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['page'] = "login"
        st.session_state['current_session_id'] = None
        # Delete cookie
        cookie_manager.delete("auth_token")
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
                
                # Save session if not saved
                if not st.session_state.get('session_saved'):
                    session_name = f"Quiz: {uploaded_files[0].name}"
                    session_manager.create_session(
                        st.session_state['username'], 
                        name=session_name,
                        session_id=st.session_state['current_session_id']
                    )
                    st.session_state['session_saved'] = True

                ingestion_manager.ingest_files(
                    file_paths, 
                    username=st.session_state['username'],
                    session_id=st.session_state['current_session_id']
                )
                st.success("Ingestion successful!")
                st.rerun() # Rerun to update session list name
        else:
            st.warning("Please upload files first.")

    st.header("2. Quiz Configuration")
    
    mode = st.radio("Select Mode", ["Single Shot", "Multilevel"])
    
    topic = "General Knowledge"
    if mode == "Multilevel":
        if st.button("Discover Topics"):
            with st.spinner("Discovering topics..."):
                topics = topic_manager.discover_topics(
                    username=st.session_state['username'],
                    session_id=st.session_state['current_session_id']
                )
                st.session_state['discovered_topics'] = topics
        
        if 'discovered_topics' in st.session_state:
            topic = st.selectbox("Select Topic", st.session_state['discovered_topics'])
            # Auto-rename session based on topic
            if st.session_state.get('session_saved'):
                 session_manager.update_session_name(st.session_state['current_session_id'], topic)
    else:
        topic = st.text_input("Enter Topic", "General Knowledge")
        # Auto-rename session based on topic input (if changed from default)
        if topic != "General Knowledge" and st.session_state.get('session_saved'):
             session_manager.update_session_name(st.session_state['current_session_id'], topic)
        
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    
    if st.button("Start Quiz"):
        with st.spinner("Generating Quiz..."):
            # Pass num_chunks=None for dynamic sizing
            quiz = quiz_generator.generate_quiz(
                topic, 
                num_chunks=None, 
                difficulty=difficulty, 
                username=st.session_state['username'],
                session_id=st.session_state['current_session_id']
            )
            if quiz:
                st.session_state['quiz_data'] = quiz
                st.session_state['current_question_index'] = 0
                st.session_state['user_answers'] = {}
                st.session_state['score'] = 0
                st.session_state['answer_submitted'] = False
                st.session_state['page'] = "quiz"
                
                # Save initial state
                if st.session_state.get('session_saved'):
                    session_manager.save_quiz_state(
                        st.session_state['current_session_id'],
                        st.session_state['quiz_data'],
                        st.session_state['current_question_index'],
                        st.session_state['user_answers'],
                        st.session_state['score'],
                        st.session_state['answer_submitted']
                    )
                
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
                
                # Save state after answer submission
                if st.session_state.get('session_saved'):
                    session_manager.save_quiz_state(
                        st.session_state['current_session_id'],
                        st.session_state['quiz_data'],
                        st.session_state['current_question_index'],
                        st.session_state['user_answers'],
                        st.session_state['score'],
                        st.session_state['answer_submitted']
                    )
                
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
                
                # Save state
                if st.session_state.get('session_saved'):
                    session_manager.save_quiz_state(
                        st.session_state['current_session_id'],
                        st.session_state['quiz_data'],
                        st.session_state['current_question_index'],
                        st.session_state['user_answers'],
                        st.session_state['score'],
                        st.session_state['answer_submitted']
                    )
                
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
