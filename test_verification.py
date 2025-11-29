__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import sys
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from ingestion import IngestionManager
from generator import QuizGenerator
from evaluator import AnswerEvaluator

def test_pipeline():
    print("=== Starting Knowval AI Test Pipeline ===")
    
    # 1. Test Ingestion
    print("\n[1] Testing Ingestion...")
    sample_file = "/home/dev/knowlEval/sample.txt"
    if not os.path.exists(sample_file):
        print(f"Error: {sample_file} not found.")
        return
    
    try:
        ingestion_manager = IngestionManager()
        ingestion_manager.ingest_files([sample_file])
        print("Ingestion Passed.")
    except Exception as e:
        print(f"Ingestion Failed: {e}")
        return

    # 2. Test Generator
    print("\n[2] Testing Generator...")
    topic = "Python"
    quiz = []
    try:
        quiz_generator = QuizGenerator()
        quiz = quiz_generator.generate_quiz(topic, num_chunks=1, difficulty="Easy")
        if not quiz:
            print("Generator Failed: No quiz generated.")
            return
        print(f"Generator Passed. Generated {len(quiz)} chunks.")
        print(f"Sample Question: {quiz[0]['question']}")
        print(f"Sample Keywords: {quiz[0]['keywords']}")
    except Exception as e:
        print(f"Generator Failed: {e}")
        return

    # 3. Test Evaluator
    print("\n[3] Testing Evaluator...")
    try:
        question = quiz[0]['question']
        keywords = quiz[0]['keywords']
        chunk_content = quiz[0]['chunk_content']
        user_answer = "Python is a high-level programming language created by Guido van Rossum."
        
        evaluator = AnswerEvaluator()
        evaluation = evaluator.evaluate_answer(question, user_answer, chunk_content, keywords)
        print(f"Evaluator Passed. Score: {evaluation.get('score')}")
        print(f"Feedback: {evaluation.get('feedback')}")
    except Exception as e:
        print(f"Evaluator Failed: {e}")
        return

    print("\n=== Test Pipeline Completed Successfully ===")

if __name__ == "__main__":
    test_pipeline()
