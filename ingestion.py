import os
import zipfile
import tarfile
import tempfile
import shutil
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
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
        """Loads documents from the given paths (PDF, TXT, DOCX, ZIP, TAR)."""
        documents = []
        for path in file_paths:
            if not os.path.exists(path):
                print(f"File not found: {path}")
                continue

            if path.endswith(".pdf"):
                loader = PyPDFLoader(path)
                documents.extend(loader.load())
            elif path.endswith(".txt"):
                loader = TextLoader(path)
                documents.extend(loader.load())
            elif path.endswith(".docx"):
                try:
                    loader = Docx2txtLoader(path)
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading DOCX {path}: {e}")
            elif path.endswith((".zip", ".tar", ".tar.gz", ".tgz")):
                documents.extend(self._process_archive(path))
            elif path.endswith((".png", ".jpg", ".jpeg")):
                try:
                    import pytesseract
                    from PIL import Image
                    text = pytesseract.image_to_string(Image.open(path))
                    if text.strip():
                        documents.append(Document(page_content=text, metadata={"source": path}))
                    else:
                        print(f"No text found in image: {path}")
                except ImportError:
                    print("Pytesseract or Pillow not installed. Skipping image.")
                except Exception as e:
                    print(f"Error processing image {path}: {e}")
                    print("Ensure Tesseract-OCR is installed on your system.")
            else:
                print(f"Unsupported file type: {path}")
        return documents

    def _process_archive(self, archive_path: str) -> List[Document]:
        """Extracts archive and loads supported files recursively."""
        documents = []
        temp_dir = tempfile.mkdtemp()
        print(f"Extracting {archive_path} to {temp_dir}...")
        
        try:
            if archive_path.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif archive_path.endswith((".tar", ".tar.gz", ".tgz")):
                with tarfile.open(archive_path, 'r') as tar_ref:
                    tar_ref.extractall(temp_dir)
            
            # Recursively find and load files
            extracted_files = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    extracted_files.append(full_path)
            
            documents.extend(self.load_documents(extracted_files))
            
        except Exception as e:
            print(f"Error processing archive {archive_path}: {e}")
        finally:
            shutil.rmtree(temp_dir)
            
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits documents into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
        )
        return text_splitter.split_documents(documents)

    def store_in_vector_db(self, chunks: List[Document], username: str = None, session_id: str = None):
        """Stores chunks in ChromaDB with user and session metadata."""
        if not chunks:
            print("No chunks to store.")
            return None
            
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Add metadata
        for chunk in chunks:
            if username:
                chunk.metadata['user_id'] = username
            if session_id:
                chunk.metadata['session_id'] = session_id

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        return vector_store

    def ingest_files(self, file_paths: List[str], username: str = None, session_id: str = None):
        """Orchestrates the ingestion process."""
        print(f"Loading files: {file_paths}")
        docs = self.load_documents(file_paths)
        print(f"Loaded {len(docs)} documents")
        
        chunks = self.split_documents(docs)
        print(f"Split into {len(chunks)} chunks")
        
        vector_store = self.store_in_vector_db(chunks, username, session_id)
        print("Stored in Vector DB")
        return vector_store
