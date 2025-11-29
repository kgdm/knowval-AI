__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class IngestionManager:
    def __init__(self, persist_directory: str = "./chroma_db", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = OpenAIEmbeddings()

    def load_documents(self, file_paths: List[str]) -> List[Document]:
        """Loads documents from the given paths (PDF or TXT)."""
        documents = []
        for path in file_paths:
            if path.endswith(".pdf"):
                loader = PyPDFLoader(path)
                documents.extend(loader.load())
            elif path.endswith(".txt"):
                loader = TextLoader(path)
                documents.extend(loader.load())
            else:
                print(f"Unsupported file type: {path}")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits documents into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
        )
        return text_splitter.split_documents(documents)

    def store_in_vector_db(self, chunks: List[Document]):
        """Stores chunks in ChromaDB."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        return vector_store

    def ingest_files(self, file_paths: List[str]):
        """Orchestrates the ingestion process."""
        print(f"Loading files: {file_paths}")
        docs = self.load_documents(file_paths)
        print(f"Loaded {len(docs)} documents")
        
        chunks = self.split_documents(docs)
        print(f"Split into {len(chunks)} chunks")
        
        vector_store = self.store_in_vector_db(chunks)
        print("Stored in Vector DB")
        return vector_store
