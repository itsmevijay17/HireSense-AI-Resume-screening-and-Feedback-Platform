# groq_model_test.py - Test the updated model
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("No GROQ_API_KEY found")
    exit()

client = Groq(api_key=api_key)

print("Testing Groq with updated model...")

try:
    # Test with the new model
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user", 
                "content": "Analyze this resume for a Software Engineer position. Return JSON with ats_score (0-100), reasoning, feedback, improvements. Resume: John Doe, Python developer with 2 years Flask experience. Job: Looking for Python developer with web framework experience."
            }
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    print("✅ SUCCESS! Model working properly")
    print("Response:", response.choices[0].message.content)
    
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Try alternative models
    alternative_models = [
        "llama-3.2-70b-versatile",
        "llama-3.2-11b-text-preview", 
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    
    print(f"\nTrying alternative models...")
    for model in alternative_models:
        try:
            print(f"Testing {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Model working'"}],
                max_tokens=10
            )
            print(f"✅ {model} is working!")
            print(f"Use this model in your code: {model}")
            break
        except Exception as e:
            print(f"❌ {model} failed: {e}")
            continue