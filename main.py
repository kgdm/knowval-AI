__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import sys
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from ingestion import ingest_files
from generator import generate_quiz
from evaluator import evaluate_answer

def main():
    print("=== Knowval AI ===")
    
    # 1. Ingestion
    print("\n--- Step 1: Document Ingestion ---")
    file_input = input("Enter file paths (comma separated) or press Enter to skip if already ingested: ")
    if file_input.strip():
        file_paths = [f.strip() for f in file_input.split(",")]
        try:
            ingest_files(file_paths)
            print("Ingestion successful!")
        except Exception as e:
            print(f"Error during ingestion: {e}")
            return

    # 2. Quiz Generation
    print("\n--- Step 2: Quiz Generation ---")
    topic = input("Enter the topic/skill to evaluate: ")
    difficulty = input("Enter difficulty level (Easy, Medium, Hard) [Default: Medium]: ") or "Medium"
    
    print(f"Generating quiz for topic '{topic}' at '{difficulty}' level...")
    try:
        quiz = generate_quiz(topic, num_chunks=20, difficulty=difficulty)
        if not quiz:
            print("No questions generated. Please check your topic or documents.")
            return
        print(f"Generated {len(quiz)} chunks with questions.")
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return

    # 3. Evaluation Loop
    print("\n--- Step 3: Evaluation ---")
    total_score = 0
    max_score = 0
    results = []

    for i, item in enumerate(quiz):
        print(f"\n--- Question {i+1}/{len(quiz)} ---")
        
        question = item['question']
        options = item['options']
        correct_answer = item['correct_answer']
        explanation = item['explanation']
        keywords = item['keywords']
        
        print(f"\n{question}")
        for key, value in options.items():
            print(f"{key}) {value}")
            
        while True:
            user_answer = input("\nYour Answer (A/B/C/D): ").strip().upper()
            if user_answer in ['A', 'B', 'C', 'D']:
                break
            print("Invalid input. Please enter A, B, C, or D.")
            
        print("Evaluating...")
        
        score = 0
        feedback = ""
        
        if user_answer == correct_answer:
            score = 10
            feedback = "Correct!"
            print(f"✅ Correct! (+10 points)")
        else:
            score = 0
            feedback = f"Incorrect. The correct answer was {correct_answer}."
            print(f"❌ Incorrect. The correct answer was {correct_answer}.")
            
        print(f"Explanation: {explanation}")
        
        total_score += score
        max_score += 10
        
        results.append({
            "question": question,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "score": score,
            "feedback": feedback,
            "explanation": explanation
        })

    # 4. Final Report
    print("\n=== Final Report ===")
    print(f"Total Score: {total_score}/{max_score}")
    
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    print(f"Percentage: {percentage:.2f}%")
    
    if percentage >= 80:
        print("Performance: Excellent! You have a strong grasp of the material.")
    elif percentage >= 50:
        print("Performance: Good. You understand the basics but missed some details.")
    else:
        print("Performance: Needs Improvement. Review the material and try again.")
        
    print("\n--- Review ---")
    for res in results:
        if res['score'] == 0:
            print(f"\n- Question: {res['question']}")
            print(f"  Your Answer: {res['user_answer']}")
            print(f"  Correct Answer: {res['correct_answer']}")
            print(f"  Explanation: {res['explanation']}")

if __name__ == "__main__":
    main()
