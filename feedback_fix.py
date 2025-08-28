# Feedback Evaluation Fix for TruLens
# This file contains the fixes for the "No feedback scores found, only cost information" issue

import os
import openai
from trulens.core import Feedback, Select, TruSession
from trulens.providers.openai import OpenAI as TruOpenAI
import time

# Initialize TruSession
tru = TruSession()

# Set OpenAI API key
if hasattr(openai, 'api_key'):
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI provider
provider = TruOpenAI()

print("🔧 Fixing feedback evaluation issues...")

# 1. Fix the feedback function definitions to ensure they work properly
try:
    # Recreate feedback functions with better error handling
    f_groundedness_fixed = (
        Feedback(
            provider.groundedness_measure_with_cot_reasons, 
            name="Groundedness_Fixed"
        )
        .on(Select.RecordCalls.retrieve_context.rets.collect())
        .on_output()
    )
    
    f_answer_relevance_fixed = (
        Feedback(
            provider.relevance_with_cot_reasons, 
            name="Answer_Relevance_Fixed"
        )
        .on_input()
        .on_output()
    )
    
    f_context_relevance_fixed = (
        Feedback(
            provider.context_relevance_with_cot_reasons, 
            name="Context_Relevance_Fixed"
        )
        .on_input()
        .on(Select.RecordCalls.retrieve_context.rets.collect())
    )
    
    # Fix the completeness feedback to avoid serialization issues
    def completeness_feedback_fixed(input_text: str, output_text: str) -> float:
        """measures if answer addresses question"""
        try:
            question_words = set(input_text.lower().split())
            answer_words = set(output_text.lower().split())
            
            # Remove common stop words
            stop_words = {'what', 'is', 'the', 'how', 'why', 'when', 'where', 'a', 'an', 'and', 'or', 'but'}
            question_words = question_words - stop_words
            
            if not question_words:
                return 0.5
            
            overlap = len(question_words.intersection(answer_words))
            return min(1.0, overlap / len(question_words))
        except Exception as e:
            print(f"Completeness feedback error: {e}")
            return 0.5
    
    f_completeness_fixed = Feedback(completeness_feedback_fixed, name="Completeness_Fixed").on_input().on_output()
    
    print("✅ Fixed feedback functions created")
    
except Exception as e:
    print(f"❌ Failed to create fixed feedback functions: {e}")

# 2. Test feedback functions individually
print("\n🧪 Testing feedback functions individually...")

test_question = "What is machine learning?"
test_answer = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."

print(f"Test question: {test_question}")
print(f"Test answer: {test_answer[:100]}...")

# Test each feedback function
try:
    print("\nTesting Groundedness...")
    groundedness_result = f_groundedness_fixed.run(
        input=test_question,
        output=test_answer,
        context=["Machine learning is a subset of artificial intelligence."]
    )
    print(f"✅ Groundedness score: {groundedness_result}")
except Exception as e:
    print(f"❌ Groundedness failed: {e}")

try:
    print("\nTesting Answer Relevance...")
    relevance_result = f_answer_relevance_fixed.run(
        input=test_question,
        output=test_answer
    )
    print(f"✅ Answer Relevance score: {relevance_result}")
except Exception as e:
    print(f"❌ Answer Relevance failed: {e}")

try:
    print("\nTesting Context Relevance...")
    context_result = f_context_relevance_fixed.run(
        input=test_question,
        context=["Machine learning is a subset of artificial intelligence."]
    )
    print(f"✅ Context Relevance score: {context_result}")
except Exception as e:
    print(f"❌ Context Relevance failed: {e}")

try:
    print("\nTesting Completeness...")
    completeness_result = f_completeness_fixed.run(
        input_text=test_question,
        output_text=test_answer
    )
    print(f"✅ Completeness score: {completeness_result}")
except Exception as e:
    print(f"❌ Completeness failed: {e}")

print("\n🔧 Feedback evaluation fixes completed!")

# 3. Instructions for fixing the notebook
print("\n" + "="*60)
print("📋 INSTRUCTIONS TO FIX YOUR NOTEBOOK:")
print("="*60)
print("""
1. Replace your existing feedback function definitions with these fixed versions:

# Replace the existing feedback functions with:
f_groundedness = (
    Feedback(
        provider.groundedness_measure_with_cot_reasons, 
        name="Groundedness"
    )
    .on(Select.RecordCalls.retrieve_context.rets.collect())
    .on_output()
)

f_answer_relevance = (
    Feedback(
        provider.relevance_with_cot_reasons, 
        name="Answer_Relevance"
    )
    .on_input()
    .on_output()
)

f_context_relevance = (
    Feedback(
        provider.context_relevance_with_cot_reasons, 
        name="Context_Relevance"
    )
    .on_input()
    .on(Select.RecordCalls.retrieve_context.rets.collect())
)

# Fix the completeness feedback function:
def completeness_feedback(input_text: str, output_text: str) -> float:
    try:
        question_words = set(input_text.lower().split())
        answer_words = set(output_text.lower().split())
        
        stop_words = {'what', 'is', 'the', 'how', 'why', 'when', 'where', 'a', 'an', 'and', 'or', 'but'}
        question_words = question_words - stop_words
        
        if not question_words:
            return 0.5
        
        overlap = len(question_words.intersection(answer_words))
        return min(1.0, overlap / len(question_words))
    except Exception as e:
        print(f"Completeness feedback error: {e}")
        return 0.5

f_completeness = Feedback(completeness_feedback, name="Completeness").on_input().on_output()

2. After creating the TruApp, add this test to verify feedback works:

# Test feedback functions individually
test_question = "What is machine learning?"
test_answer = "Machine learning is a subset of artificial intelligence."

print("Testing feedback functions...")
try:
    groundedness_score = f_groundedness.run(
        input=test_question,
        output=test_answer,
        context=["Machine learning is a subset of AI."]
    )
    print(f"Groundedness: {groundedness_score}")
except Exception as e:
    print(f"Groundedness failed: {e}")

3. Make sure to wait for feedback evaluation:
import time
time.sleep(5)  # Wait for feedback to complete

4. Check records again:
records, feedback_results = tru.get_records_and_feedback()
feedback_cols = [col for col in records.columns if any(name in col for name in ['Groundedness', 'Relevance', 'Completeness']) and 'cost' not in col.lower()]
print(f"Feedback columns: {feedback_cols}")
""")
