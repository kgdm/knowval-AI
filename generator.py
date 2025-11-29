__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import json
from typing import List, Dict, Any
from difflib import SequenceMatcher
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize LLM inside functions to ensure env vars are loaded
# llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def get_retriever(persist_directory: str = "./chroma_db"):
    embeddings = OpenAIEmbeddings()
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return vector_store.as_retriever()

def generate_questions_and_keywords(chunk: str, difficulty: str) -> Dict[str, Any]:
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

def generate_quiz(topic: str, num_chunks: int = 20, difficulty: str = "Medium"):
    """
    Generates a quiz by retrieving chunks related to the topic.
    Ensures questions are unique.
    """
    retriever = get_retriever()
    # Retrieve more docs than needed to filter for quality if necessary
    # docs = retriever.invoke(topic) 
    
    # Re-initialize vector store to access search directly for k control
    embeddings = OpenAIEmbeddings()
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    # Fetch more chunks to allow for skipping duplicates
    docs = vector_store.similarity_search(topic, k=num_chunks * 2)
    
    quiz_data = []
    seen_questions = []
    seen_chunk_contents = set()
    
    for i, doc in enumerate(docs):
        if len(quiz_data) >= num_chunks:
            break
            
        # Chunk Deduplication (Exact Match)
        # Using content length and a snippet for a quick check, or full content hash
        content_hash = hash(doc.page_content)
        if content_hash in seen_chunk_contents:
            continue
        seen_chunk_contents.add(content_hash)
            
        print(f"Processing chunk {len(quiz_data)+1}...")
        result = generate_questions_and_keywords(doc.page_content, difficulty)
        
        question_text = result.get("question")
        
        if not question_text:
            continue
            
        # Question Deduplication (Fuzzy Match)
        is_duplicate = False
        for seen_q in seen_questions:
            # Check similarity. 0.85 means 85% similar.
            if SequenceMatcher(None, question_text, seen_q).ratio() > 0.85:
                is_duplicate = True
                print(f"Skipping similar question: {question_text[:50]}...")
                break
        
        if is_duplicate:
            continue
            
        seen_questions.append(question_text)
        
        quiz_data.append({
            "chunk_id": len(quiz_data) + 1,
            "chunk_content": doc.page_content,
            "question": question_text,
            "options": result.get("options", {}),
            "correct_answer": result.get("correct_answer"),
            "explanation": result.get("explanation"),
            "keywords": result.get("keywords", [])
        })
        
    return quiz_data
