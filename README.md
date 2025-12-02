# Knowval AI

Knowval AI is an intelligent Knowledge Evaluator Agent designed to assess a user's understanding of specific topics using RAG (Retrieval-Augmented Generation). It ingests educational materials, generates dynamic quizzes, and evaluates answers using Bloom's Taxonomy.

## Features

-   **RAG-based Knowledge Retrieval**: Ingests documents to create a knowledge base using ChromaDB.
-   **Enhanced Ingestion Support**:
    -   **Formats**: PDF, TXT, DOCX, ZIP, TAR, TAR.GZ.
    -   **Images**: PNG, JPG, JPEG (requires Tesseract OCR).
-   **Multilevel Quiz Modes**:
    -   **Single Shot**: Random questions from the entire document.
    -   **Multilevel**: Discovers topics/chapters and generates focused quizzes.
-   **Dynamic Question Generation**:
    -   **Smart Deduplication**: Uses fuzzy matching and MMR (Max Marginal Relevance) for diverse, non-repetitive questions.
    -   **Dynamic Sizing**: Automatically adjusts quiz length (10/20/30 questions) based on document size.
    -   **Difficulty Levels**: Supports Easy, Medium, and Hard difficulty settings.
-   **Intelligent Evaluation**:
    -   **Bloom's Taxonomy**: Evaluates answers based on cognitive depth.
    -   **Context Awareness**: Checks relevance to the source material.
    -   **Keyword Matching**: Verifies the presence of essential concepts.
-   **Interactive Chatbot**: A CLI-based interactive loop for taking quizzes and receiving immediate feedback.
-   **Performance Reporting**: Provides a final score and detailed review of incorrect answers.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/knowlEval.git
    cd knowlEval
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up Environment Variables**:
    -   Create a `.env` file in the root directory.
    -   Add your OpenAI API Key:
        ```env
        OPENAI_API_KEY=your_api_key_here
        ```

## Usage

1.  **Start the Agent**:
    ```bash
    python main.py
    ```

2.  **Ingest Documents**:
    -   Enter the file paths of your study materials when prompted.
    -   Supports: `.pdf`, `.txt`, `.docx`, `.zip`, `.tar`, `.png`, `.jpg`, etc.
    -   Example: `/path/to/docs.zip` or `/path/to/notes.docx`

3.  **Select Quiz Mode**:
    -   **Single Shot**: For a general assessment of the entire content.
    -   **Multilevel**: To discover topics and focus on specific chapters.

4.  **Take the Quiz**:
    -   Answer the generated MCQs.
    -   Receive real-time scoring and feedback.

5.  **Review**:
    -   Get a comprehensive report at the end of the session.

## Deployment

### Streamlit Community Cloud (Recommended)
1.  Push this repository to GitHub.
2.  Go to [Streamlit Community Cloud](https://streamlit.io/cloud).
3.  Connect your GitHub account and select this repository.
4.  Set the **Main file path** to `app.py`.
5.  **Advanced Settings**:
    -   Add your `OPENAI_API_KEY` in the "Secrets" section.
    -   *Note*: The repository includes `packages.txt` to automatically install Tesseract OCR.

## Project Structure

-   `main.py`: Entry point for the interactive chatbot loop.
-   `ingestion.py`: Handles document loading (including archives/images), chunking, and vector storage.
-   `generator.py`: Generates unique questions using LLMs with MMR search and dynamic sizing.
-   `topic_discovery.py`: Identifies topics for Multilevel quizzes.
-   `evaluator.py`: Evaluates user answers and provides feedback.
-   `test_verification.py`: Automated script to verify the pipeline.

## Technologies Used

-   **Python 3.11+**
-   **LangChain**: For orchestration and RAG flows.
-   **ChromaDB**: Vector database for document storage.
-   **OpenAI GPT-4o**: LLM for generation and evaluation.
-   **Tesseract OCR**: For extracting text from images.
