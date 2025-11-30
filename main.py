__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from ingestion import IngestionManager
from generator import QuizGenerator
from evaluator import AnswerEvaluator
from topic_discovery import TopicManager

class KnowvalApp:
    def __init__(self):
        self.ingestion_manager = IngestionManager()
        self.quiz_generator = QuizGenerator()
        self.evaluator = AnswerEvaluator()
        self.topic_manager = TopicManager()

    def handle_ingestion(self):
        print("\n--- Step 1: Document Ingestion ---")
        file_input = input("Enter file paths (comma separated) or press Enter to skip if already ingested: ")
        if file_input.strip():
            file_paths = [f.strip() for f in file_input.split(",")]
            try:
                self.ingestion_manager.ingest_files(file_paths)
                print("Ingestion successful!")
            except Exception as e:
                print(f"Error during ingestion: {e}")
                return False
        return True

    def handle_quiz(self):
        print("\n--- Step 2: Quiz Generation ---")
        print("Select Quiz Mode:")
        print("1. Single Shot (Random Questions from entire content)")
        print("2. Multilevel (Chapter/Topic based)")
        
        mode = input("Enter choice (1 or 2): ").strip()
        
        topic = ""
        if mode == "2":
            print("Discovering topics from documents... Please wait.")
            try:
                topics = self.topic_manager.discover_topics()
                print("\nAvailable Topics:")
                for i, t in enumerate(topics):
                    print(f"{i+1}. {t}")
                
                while True:
                    try:
                        choice_input = input("Select a topic number: ")
                        choice = int(choice_input)
                        if 1 <= choice <= len(topics):
                            topic = topics[choice-1]
                            break
                        print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            except Exception as e:
                print(f"Error discovering topics: {e}. Falling back to General.")
                topic = "General Knowledge"
        else:
            topic = input("Enter the topic/skill to evaluate (or press Enter for General): ") or "General Knowledge"
            
        difficulty = input("Enter difficulty level (Easy, Medium, Hard) [Default: Medium]: ") or "Medium"
        
        print(f"Generating quiz for topic '{topic}' at '{difficulty}' level...")
        try:
            quiz = self.quiz_generator.generate_quiz(topic, num_chunks=20, difficulty=difficulty)
            if not quiz:
                print("No questions generated. Please check your topic or documents.")
                return None
            print(f"Generated {len(quiz)} chunks with questions.")
            return quiz
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return None

    def handle_evaluation(self, quiz):
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
                print(f"✅ Correct!")
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
            
        return total_score, max_score, results

    def run(self):
        print("=== Knowval AI ===")
        
        if not self.handle_ingestion():
            return

        quiz = self.handle_quiz()
        if not quiz:
            return

        total_score, max_score, results = self.handle_evaluation(quiz)

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
    app = KnowvalApp()
    app.run()
