# test_groq.py - Run this to test your Groq API setup
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq_setup():
    print("=== Groq API Setup Test ===")
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    print(f"1. API Key present: {bool(api_key)}")
    if api_key:
        print(f"   Key starts with 'gsk_': {api_key.startswith('gsk_')}")
        print(f"   Key length: {len(api_key)}")
    else:
        print("   ERROR: No GROQ_API_KEY found!")
        return False
    
    # Test import
    try:
        from groq import Groq
        print("2. Groq package import: SUCCESS")
    except ImportError as e:
        print(f"2. Groq package import: FAILED - {e}")
        print("   Run: pip install groq")
        return False
    
    # Test client initialization
    try:
        client = Groq(api_key=api_key)
        print("3. Client initialization: SUCCESS")
    except Exception as e:
        print(f"3. Client initialization: FAILED - {e}")
        return False
    
    # Test API call
    try:
        print("4. Testing API call...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=50,
            timeout=30
        )
        print("4. API call: SUCCESS")
        print(f"   Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"4. API call: FAILED - {e}")
        return False

if __name__ == "__main__":
    if test_groq_setup():
        print("\n✅ All tests passed! Your Groq setup is working.")
    else:
        print("\n❌ Setup issues found. Fix the errors above.")