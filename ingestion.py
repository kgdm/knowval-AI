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

def load_documents(file_paths: List[str]) -> List[Document]:
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

def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """Splits documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    return text_splitter.split_documents(documents)

def store_in_vector_db(chunks: List[Document], persist_directory: str = "./chroma_db"):
    """Stores chunks in ChromaDB."""
    # Ensure OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    embeddings = OpenAIEmbeddings()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    return vector_store

def ingest_files(file_paths: List[str]):
    """Orchestrates the ingestion process."""
    print(f"Loading files: {file_paths}")
    docs = load_documents(file_paths)
    print(f"Loaded {len(docs)} documents")
    
    chunks = split_documents(docs)
    print(f"Split into {len(chunks)} chunks")
    
    vector_store = store_in_vector_db(chunks)
    print("Stored in Vector DB")
    return vector_store
