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

    def generate_batch_questions(self, chunks: List[str], topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """
        Generates MCQs for a batch of chunks.
        """
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        
        prompt_template = """
        You are Knowval AI, an expert Knowledge Evaluator.
        Your task is to generate 1 {difficulty} level multiple-choice question (MCQ) for EACH of the provided text chunks.
        
        Topic: {topic}
        
        CRITICAL GUIDELINES:
        1. **One Question Per Chunk**: Generate exactly one question for each chunk provided below.
        2. **Relevance Check**: If a chunk is NOT substantively relevant to the Topic or is just noise/preface, return null for that chunk.
        3. **Conceptual Focus**: The question MUST test the user's understanding of the *concepts*, *principles*, or *mechanisms* discussed in the text.
        4. **Avoid Trivial Details**: DO NOT ask about specific dates, minor names, specific book titles mentioned in passing, or "what does the text say about X".
        5. **Generalizability**: The question should be answerable by someone who knows the subject well, even if they haven't read this specific text chunk. The text chunk is just the source of truth.
        6. **No "According to the text"**: Avoid phrasing like "According to the passage..." or "In this text...". Make it a general subject question.
        7. **Distractors**: Ensure the wrong options (distractors) are plausible but clearly incorrect to a knowledgeable person.
        8. **Noise**: Avoid any noise or irrelevant information in the question. 
        9. **Silliness**: Avoid any silly or illogical questions like context about the book or author or documentation team whatsoever. instead only focus on the core contents of the data and the topics.
        10. **Output Format**: Return a JSON LIST of objects.
        
        Input Chunks:
        {formatted_chunks}
        
        Output Format (JSON List):
        [
            {{
                "chunk_index": 0,
                "question": "Question text...",
                "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
                "correct_answer": "A",
                "explanation": "...",
                "keywords": ["..."]
            }},
            ...
        ]
        """
        
        formatted_chunks = "\n\n".join([f"--- CHUNK {i} ---\n{chunk}" for i, chunk in enumerate(chunks)])
        
        prompt = PromptTemplate(
            input_variables=["difficulty", "topic", "formatted_chunks"],
            template=prompt_template
        )
        
        chain = prompt | llm
        try:
            response = chain.invoke({
                "difficulty": difficulty,
                "topic": topic,
                "formatted_chunks": formatted_chunks
            })
            
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            print(f"Error parsing batch LLM response: {e}")
            return []

    def _expand_topic(self, topic: str) -> str:
        """Expands the topic into a conceptual search query."""
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        prompt = PromptTemplate(
            input_variables=["topic"],
            template="""You are an expert educational assistant. The user wants a quiz on the topic: '{topic}'.
            Generate a search query that lists the core concepts, principles, and key terms related to this topic.
            The query should be a single string of keywords and phrases.
            Output only the query."""
        )
        chain = prompt | llm
        try:
            return chain.invoke({"topic": topic}).content.strip()
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return topic

    def _is_chunk_relevant(self, chunk: str, topic: str) -> bool:
        """Checks if the chunk contains substantive information about the topic."""
        # NOTE: This method is kept for backward compatibility or individual checks if needed,
        # but batch generation now handles relevance internally.
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        prompt = PromptTemplate(
            input_variables=["topic", "chunk"],
            template="""You are an expert evaluator.
            Topic: {topic}
            Text Chunk:
            "{chunk}"
            Does this text chunk contain substantive information, explanations, or definitions related to the topic?
            Answer 'YES' if it contains useful information for a quiz question.
            Answer 'NO' if it is just a passing mention, a table of contents, a preface, or irrelevant noise.
            Output only YES or NO."""
        )
        chain = prompt | llm
        try:
            response = chain.invoke({"topic": topic, "chunk": chunk}).content.strip().upper()
            return "YES" in response
        except Exception as e:
            print(f"Relevance check failed: {e}")
            return True

    def get_total_chunks(self, username: str = None, session_id: str = None) -> int:
        """Returns the total number of chunks in the vector store, filtered by user/session."""
        try:
            # Prepare filter
            filters = []
            if username:
                filters.append({"user_id": username})
            if session_id:
                filters.append({"session_id": session_id})
            
            if len(filters) > 1:
                filter_dict = {"$and": filters}
            elif len(filters) == 1:
                filter_dict = filters[0]
            else:
                filter_dict = None

            # Chroma's count() doesn't support filter in all versions, but get() does.
            # Using get(where=...) to count.
            if filter_dict:
                return len(self.vector_store.get(where=filter_dict)['ids'])
            else:
                return self.vector_store._collection.count()
        except Exception as e:
            print(f"Error counting chunks: {e}")
            return 0

    def generate_quiz(self, topic: str, num_chunks: int = None, difficulty: str = "Medium", username: str = None, session_id: str = None):
        """
        Generates a quiz by retrieving chunks related to the topic.
        Uses batch processing for speed.
        """
        if num_chunks is None:
            total_chunks = self.get_total_chunks(username, session_id)
            if total_chunks < 50:
                num_chunks = 10
            elif total_chunks < 150:
                num_chunks = 20
            else:
                num_chunks = 30
            print(f"Dynamic Quiz Size: {num_chunks} questions (Total Chunks: {total_chunks})")

        # 1. Query Expansion
        print(f"Expanding topic '{topic}'...")
        search_query = self._expand_topic(topic)
        print(f"Expanded Query: {search_query}")

        # Prepare filter
        filters = []
        if username:
            filters.append({"user_id": username})
        if session_id:
            filters.append({"session_id": session_id})
        
        if len(filters) > 1:
            filter_dict = {"$and": filters}
        elif len(filters) == 1:
            filter_dict = filters[0]
        else:
            filter_dict = None

        # Fetch more chunks to allow for filtering
        try:
            docs = self.vector_store.max_marginal_relevance_search(
                search_query, 
                k=num_chunks * 2,
                fetch_k=num_chunks * 5, 
                lambda_mult=0.5,
                filter=filter_dict
            )
        except Exception as e:
            print(f"MMR Search failed ({e}), falling back to similarity search.")
            docs = self.vector_store.similarity_search(search_query, k=num_chunks * 2, filter=filter_dict)
        
        # Shuffle documents
        random.shuffle(docs)
        
        quiz_data = []
        seen_questions = []
        seen_chunk_contents = set()
        
        # Process in batches of 5
        batch_size = 5
        
        # Filter duplicates first
        unique_docs = []
        for doc in docs:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_chunk_contents:
                seen_chunk_contents.add(content_hash)
                unique_docs.append(doc)
                
        for i in range(0, len(unique_docs), batch_size):
            if len(quiz_data) >= num_chunks:
                break
                
            batch_docs = unique_docs[i:i+batch_size]
            batch_chunks = [doc.page_content for doc in batch_docs]
            
            print(f"Processing batch {i//batch_size + 1} ({len(batch_chunks)} chunks)...")
            
            results = self.generate_batch_questions(batch_chunks, topic, difficulty)
            
            for res in results:
                if len(quiz_data) >= num_chunks:
                    break
                    
                if not res or not res.get("question"):
                    continue
                
                # Extra safety check for string "null" or "None"
                q_text = str(res.get("question")).strip().lower()
                if q_text in ["null", "none", ""]:
                    continue
                    
                question_text = res.get("question")
                
                # Question Deduplication
                is_duplicate = False
                for seen_q in seen_questions:
                    if SequenceMatcher(None, question_text, seen_q).ratio() > 0.85:
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue
                    
                seen_questions.append(question_text)
                
                # Shuffle options
                options_dict = res.get("options", {})
                correct_option_key = res.get("correct_answer")
                correct_option_text = options_dict.get(correct_option_key)
                
                items = list(options_dict.values())
                random.shuffle(items)
                
                new_options = {}
                new_correct_key = ""
                keys = ["A", "B", "C", "D"]
                
                for idx, text in enumerate(items):
                    if idx < len(keys):
                        key = keys[idx]
                        new_options[key] = text
                        if text == correct_option_text:
                            new_correct_key = key
                
                # Find original doc content (approximate mapping by index if needed, but here we just use the chunk content from result or map back)
                # Since we passed a list, we can map back by index if the LLM respects it.
                # The prompt asks for "chunk_index".
                chunk_idx = res.get("chunk_index", 0)
                if 0 <= chunk_idx < len(batch_docs):
                    original_doc = batch_docs[chunk_idx]
                    
                    quiz_data.append({
                        "chunk_id": len(quiz_data) + 1,
                        "chunk_content": original_doc.page_content,
                        "question": question_text,
                        "options": new_options,
                        "correct_answer": new_correct_key,
                        "explanation": res.get("explanation"),
                        "keywords": res.get("keywords", [])
                    })
            
        return quiz_data
