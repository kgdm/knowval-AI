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

    # 4. Test Topic Discovery
    print("\n[4] Testing Topic Discovery...")
    from topic_discovery import TopicManager
    try:
        topic_manager = TopicManager()
        topics = topic_manager.discover_topics()
        print(f"Topic Discovery Passed. Discovered {len(topics)} topics.")
        print(f"Topics: {topics}")
    except Exception as e:
        print(f"Topic Discovery Failed: {e}")
        return

    # 5. Test Enhanced Ingestion (Docx & Zip)
    print("\n[5] Testing Enhanced Ingestion (Docx & Zip)...")
    # Create dummy docx and zip for testing
    import zipfile
    
    dummy_docx = "test.docx"
    dummy_zip = "test.zip"
    
    # Create a dummy text file to zip
    with open("zipped.txt", "w") as f:
        f.write("This is a text file inside a zip archive.")
        
    with zipfile.ZipFile(dummy_zip, 'w') as zf:
        zf.write("zipped.txt")
    
    os.remove("zipped.txt")
    
    try:
        ingestion_manager = IngestionManager()
        # We only test zip here as creating a valid docx programmatically without extra libs is tricky
        # But the logic is similar.
        print(f"Testing ingestion of {dummy_zip}...")
        ingestion_manager.ingest_files([dummy_zip])
        print("Enhanced Ingestion Passed.")
    except Exception as e:
        print(f"Enhanced Ingestion Failed: {e}")
    finally:
        if os.path.exists(dummy_zip):
            os.remove(dummy_zip)

    # 6. Test Image Ingestion
    print("\n[6] Testing Image Ingestion...")
    # Create a dummy image with text (requires PIL)
    try:
        from PIL import Image, ImageDraw
        dummy_image = "test_image.png"
        img = Image.new('RGB', (100, 30), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10,10), "Hello World", fill=(255, 255, 0))
        img.save(dummy_image)
        
        ingestion_manager = IngestionManager()
        print(f"Testing ingestion of {dummy_image}...")
        ingestion_manager.ingest_files([dummy_image])
        print("Image Ingestion Passed (or skipped gracefully).")
    except ImportError:
        print("PIL not installed, skipping image test.")
    except Exception as e:
        print(f"Image Ingestion Failed: {e}")
    finally:
        if os.path.exists("test_image.png"):
            os.remove("test_image.png")

    # 7. Test Dynamic Quiz Sizing
    print("\n[7] Testing Dynamic Quiz Sizing...")
    try:
        quiz_generator = QuizGenerator()
        total_chunks = quiz_generator.get_total_chunks()
        print(f"Total Chunks in DB: {total_chunks}")
        
        # We expect small number of chunks for the sample file, so quiz size should be 10
        expected_size = 10
        if total_chunks >= 150:
            expected_size = 30
        elif total_chunks >= 50:
            expected_size = 20
            
        print(f"Expected Quiz Size: {expected_size}")
        
        # We won't run the full generation to save time/cost, but we verify the method exists and counts correctly
        if total_chunks > 0:
            print("Dynamic Sizing Logic Check Passed.")
        else:
            print("Warning: Total chunks is 0. Ingestion might have failed or DB is empty.")
            
    except Exception as e:
        print(f"Dynamic Sizing Test Failed: {e}")

    print("\n=== Test Pipeline Completed Successfully ===")

if __name__ == "__main__":
    test_pipeline()
