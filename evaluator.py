import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Initialize LLM inside functions
# llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

def evaluate_answer(question: str, user_answer: str, chunk_content: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Evaluates the user's answer against the chunk content and keywords.
    Returns a score out of 10 and feedback.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    prompt_template = """
    You are Knowval AI, an expert Knowledge Evaluator using Bloom's Taxonomy.
    
    Context (Chunk):
    "{chunk_content}"
    
    Question:
    "{question}"
    
    User's Answer:
    "{user_answer}"
    
    Required Keywords/Phrases:
    {keywords}
    
    Task:
    1. Check if the user's answer is contextually relevant to the provided chunk.
    2. Check if the required keywords (or their semantic equivalents) are present.
    3. Evaluate the depth of understanding based on Bloom's Taxonomy.
    4. Assign a score out of 10 (0 = completely wrong/irrelevant, 10 = perfect).
    5. Provide constructive feedback and suggestions for improvement.
    
    Output Format (JSON):
    {{
        "score": 8,
        "feedback": "Good answer, but you missed the concept of...",
        "keywords_present": ["keyword1"],
        "keywords_missing": ["keyword2", "keyword3"]
    }}
    """
    
    prompt = PromptTemplate(
        input_variables=["chunk_content", "question", "user_answer", "keywords"],
        template=prompt_template
    )
    
    chain = prompt | llm
    response = chain.invoke({
        "chunk_content": chunk_content,
        "question": question,
        "user_answer": user_answer,
        "keywords": keywords
    })
    
    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing Evaluation response: {e}")
        return {
            "score": 0, 
            "feedback": "Error evaluating answer.", 
            "keywords_present": [], 
            "keywords_missing": keywords
        }
