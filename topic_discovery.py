__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class TopicManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)

    def discover_topics(self, username: str = None, session_id: str = None) -> List[str]:
        """
        Analyzes the documents to discover main topics or chapters.
        """
        # Retrieve chunks that might contain structural info
        # We search for terms likely to appear in introductions or table of contents
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
        
        docs = self.vector_store.similarity_search(
            "Table of Contents, Chapters, Overview, Syllabus, Introduction", 
            k=15,
            filter=filter_dict
        )
        
        if not docs:
            return ["General Knowledge"]

        text_sample = "\n\n".join([d.page_content[:500] for d in docs]) # Limit context size
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        
        prompt_template = """
        You are Knowval AI, an expert curriculum designer.
        Your task is to analyze the following text segments from a document and extract a list of 5 to 10 main chapters, topics, or skills covered.
        
        The topics should be distinct and cover the breadth of the content.
        Return ONLY a JSON array of strings.
        
        Text Segments:
        "{text_sample}"
        
        Output Format:
        ["Topic 1", "Topic 2", "Topic 3"]
        """
        
        prompt = PromptTemplate(
            input_variables=["text_sample"],
            template=prompt_template
        )
        
        chain = prompt | llm
        response = chain.invoke({"text_sample": text_sample})
        
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            topics = json.loads(content)
            if isinstance(topics, list):
                return topics
            return ["General Knowledge"]
        except Exception as e:
            print(f"Error discovering topics: {e}")
            return ["General Knowledge"]
