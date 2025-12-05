import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generator import QuizGenerator

class TestQuizGeneratorBatch(unittest.TestCase):
    def setUp(self):
        # Mock Chroma and OpenAIEmbeddings to avoid actual DB/API calls during init
        with patch('generator.Chroma'), patch('generator.OpenAIEmbeddings'):
            self.generator = QuizGenerator()

    def test_methods_exist(self):
        """Verify that all critical methods exist."""
        self.assertTrue(hasattr(self.generator, 'generate_batch_questions'))
        self.assertTrue(hasattr(self.generator, 'get_total_chunks'))
        self.assertTrue(hasattr(self.generator, '_expand_topic'))
        self.assertTrue(hasattr(self.generator, '_is_chunk_relevant'))
        self.assertTrue(hasattr(self.generator, 'generate_quiz'))

    @patch('generator.ChatOpenAI')
    def test_expand_topic(self, MockChatOpenAI):
        """Test _expand_topic method."""
        # Mock the chain execution
        mock_llm = MockChatOpenAI.return_value
        # When chain = prompt | llm, chain.invoke() calls llm.invoke() which returns a message
        # We need to mock the chain construction or the llm response
        
        # In the code: chain = prompt | llm; response = chain.invoke(...)
        # The result of chain.invoke() has a .content attribute
        mock_response = MagicMock()
        mock_response.content = "expanded query terms"
        
        # Mocking the pipe operator is tricky, simpler to mock the chain directly if possible
        # or mock what the chain returns. 
        # Since we can't easily mock the pipe, let's rely on the fact that 
        # prompt | llm returns a RunnableSequence.
        # A simpler approach for unit testing this specific logic without deep framework mocking:
        # We can mock the invoke method of the LLM if the chain just passes through.
        
        # However, let's try to mock the invoke return value on the LLM instance, 
        # assuming the chain delegates to it.
        mock_llm.invoke.return_value = mock_response
        
        # But wait, the code uses `chain = prompt | llm`. 
        # `chain.invoke` will eventually call `llm.invoke` (or similar).
        # Let's mock the return value of the chain.
        
        with patch('generator.PromptTemplate') as MockPrompt:
            # Mock the chain object returned by prompt | llm
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_response
            
            # Make the prompt | llm expression return our mock_chain
            # This requires mocking the __or__ method of the prompt instance
            mock_prompt_instance = MockPrompt.return_value
            mock_prompt_instance.__or__.return_value = mock_chain
            
            result = self.generator._expand_topic("test topic")
            self.assertEqual(result, "expanded query terms")

    @patch('generator.ChatOpenAI')
    def test_generate_batch_questions_parsing(self, MockChatOpenAI):
        """Test that batch questions are parsed correctly."""
        mock_response_content = """
        [
            {
                "chunk_index": 0,
                "question": "Test Question 1",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "correct_answer": "A",
                "explanation": "Exp 1",
                "keywords": ["k1"]
            }
        ]
        """
        mock_response = MagicMock()
        mock_response.content = mock_response_content
        
        with patch('generator.PromptTemplate') as MockPrompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_response
            
            mock_prompt_instance = MockPrompt.return_value
            mock_prompt_instance.__or__.return_value = mock_chain
            
            chunks = ["chunk1"]
            results = self.generator.generate_batch_questions(chunks, "topic", "Medium")
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['question'], "Test Question 1")

if __name__ == '__main__':
    unittest.main()
