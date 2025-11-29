__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import json
import random
from typing import List, Dict, Any
from difflib import SequenceMatcher
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class QuizGenerator:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
        # Initialize LLM lazily or here if preferred, but keeping it per method for safety as per previous fix
        # self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7) 

    def get_retriever(self):
        return self.vector_store.as_retriever()

    def generate_question(self, chunk: str, difficulty: str) -> Dict[str, Any]:
        """
        Generates a single MCQ question and keywords for a given chunk and difficulty.
        """
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        
        prompt_template = """
        You are Knowval AI, an expert Knowledge Evaluator.
        Your task is to generate exactly 1 {difficulty} level multiple-choice question (MCQ) based on the following text chunk.
        
        CRITICAL GUIDELINES FOR QUESTION GENERATION:
        1. **Conceptual Focus**: The question MUST test the user's understanding of the *concepts*, *principles*, or *mechanisms* discussed in the text.
        2. **Avoid Trivial Details**: DO NOT ask about specific dates, minor names, specific book titles mentioned in passing, or "what does the text say about X".
        3. **Generalizability**: The question should be answerable by someone who knows the subject well, even if they haven't read this specific text chunk. The text chunk is just the source of truth.
        4. **No "According to the text"**: Avoid phrasing like "According to the passage..." or "In this text...". Make it a general subject question.
        5. **Distractors**: Ensure the wrong options (distractors) are plausible but clearly incorrect to a knowledgeable person.
        6. **Noise**: Avoid any noise or irrelevant information in the question. 
        7. **Silliness**: Avoid any silly or illogical questions like context about the book or author or documentation team whatsoever. instead only focus on the core contents of the data and the topics.
        
        Text Chunk:
        "{chunk}"
        
        Output Format (JSON):
        {{
            "question": "The question text here?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "A",
            "explanation": "Explanation here.",
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """
        
        prompt = PromptTemplate(
            input_variables=["difficulty", "chunk"],
            template=prompt_template
        )
        
        chain = prompt | llm
        response = chain.invoke({
            "difficulty": difficulty,
            "chunk": chunk
        })
        
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {}

    def generate_quiz(self, topic: str, num_chunks: int = 20, difficulty: str = "Medium"):
        """
        Generates a quiz by retrieving chunks related to the topic.
        Ensures questions are unique.
        """
        # Fetch more chunks to allow for skipping duplicates
        docs = self.vector_store.similarity_search(topic, k=num_chunks * 3)
        
        # Shuffle documents to ensure diverse content coverage
        random.shuffle(docs)
        
        quiz_data = []
        seen_questions = []
        seen_chunk_contents = set()
        
        for i, doc in enumerate(docs):
            if len(quiz_data) >= num_chunks:
                break
                
            # Chunk Deduplication (Exact Match)
            content_hash = hash(doc.page_content)
            if content_hash in seen_chunk_contents:
                continue
            seen_chunk_contents.add(content_hash)
                
            print(f"Processing chunk {len(quiz_data)+1}...")
            result = self.generate_question(doc.page_content, difficulty)
            
            question_text = result.get("question")
            
            if not question_text:
                continue
                
            # Question Deduplication (Fuzzy Match)
            is_duplicate = False
            for seen_q in seen_questions:
                if SequenceMatcher(None, question_text, seen_q).ratio() > 0.85:
                    is_duplicate = True
                    print(f"Skipping similar question: {question_text[:50]}...")
                    break
            
            if is_duplicate:
                continue
                
            seen_questions.append(question_text)
            
            # Shuffle options to ensure randomness
            options_dict = result.get("options", {})
            correct_option_key = result.get("correct_answer")
            correct_option_text = options_dict.get(correct_option_key)
            
            # Create a list of (key, value) pairs and shuffle them
            items = list(options_dict.values())
            random.shuffle(items)
            
            # Reassign keys A, B, C, D
            new_options = {}
            new_correct_key = ""
            keys = ["A", "B", "C", "D"]
            
            for idx, text in enumerate(items):
                if idx < len(keys):
                    key = keys[idx]
                    new_options[key] = text
                    if text == correct_option_text:
                        new_correct_key = key
            
            quiz_data.append({
                "chunk_id": len(quiz_data) + 1,
                "chunk_content": doc.page_content,
                "question": question_text,
                "options": new_options,
                "correct_answer": new_correct_key,
                "explanation": result.get("explanation"),
                "keywords": result.get("keywords", [])
            })
            
        return quiz_data
