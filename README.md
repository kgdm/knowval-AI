# Knowval AI

Knowval AI is an intelligent Knowledge Evaluator Agent designed to assess a user's understanding of specific topics using RAG (Retrieval-Augmented Generation). It ingests educational materials, generates dynamic quizzes, and evaluates answers using Bloom's Taxonomy.

## Features

-   **RAG-based Knowledge Retrieval**: Ingests PDF and Text documents to create a knowledge base using ChromaDB.
-   **Dynamic Question Generation**: Generates multiple-choice questions (MCQs) tailored to the content.
    -   **Smart Deduplication**: Uses fuzzy matching to ensure unique and diverse questions.
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
    -   Enter the file paths of your study materials (PDF or TXT) when prompted.
    -   Example: `/path/to/document.pdf`

3.  **Generate a Quiz**:
    -   Specify the topic you want to be tested on.
    -   Choose a difficulty level (Easy, Medium, Hard).

4.  **Take the Quiz**:
    -   Answer the generated MCQs.
    -   Receive real-time scoring and feedback.

5.  **Review**:
    -   Get a comprehensive report at the end of the session.

## Project Structure

-   `main.py`: Entry point for the interactive chatbot loop.
-   `ingestion.py`: Handles document loading, chunking, and vector storage.
-   `generator.py`: Generates unique questions and keywords using LLMs.
-   `evaluator.py`: Evaluates user answers and provides feedback.
-   `test_verification.py`: Automated script to verify the pipeline.

## Technologies Used

-   **Python 3.11+**
-   **LangChain**: For orchestration and RAG flows.
-   **ChromaDB**: Vector database for document storage.
-   **OpenAI GPT-4o**: LLM for generation and evaluation.
