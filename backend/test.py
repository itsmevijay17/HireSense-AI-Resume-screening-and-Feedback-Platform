import requests
import json
import time

# Your API key
api_key = "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"

def test_model(model_name, inputs, task_type="embedding"):
    """Test if a Hugging Face model works via API"""
    
    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if task_type == "embedding":
        data = {"inputs": inputs}
    elif task_type == "feature-extraction":
        data = {"inputs": inputs, "options": {"wait_for_model": True}}
    else:  # generation/reranking
        data = {"inputs": inputs}
    
    print(f"\n🧪 Testing: {model_name}")
    print(f"   Task: {task_type}")
    print(f"   Input: {inputs[:100]}..." if len(inputs) > 100 else f"   Input: {inputs}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS!")
            
            if task_type in ["embedding", "feature-extraction"]:
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list):
                        print(f"   📊 Embedding dimension: {len(result[0])}")
                        print(f"   🎯 Perfect for resume matching!")
                    elif isinstance(result[0], dict) and 'embedding' in str(result[0]):
                        print(f"   📊 Embedding format: {type(result[0])}")
                        print(f"   🎯 Good for resume matching!")
                else:
                    print(f"   📝 Result type: {type(result)}")
            else:
                print(f"   📝 Generated: {str(result)[:200]}...")
            return True
            
        elif response.status_code == 404:
            print(f"   ❌ Model not found (404)")
            return False
            
        elif response.status_code == 503:
            print(f"   ⏳ Model loading (503) - will retry in 10 seconds")
            time.sleep(10)
            return test_model(model_name, inputs, task_type)  # Retry once
            
        elif response.status_code == 400:
            print(f"   ⚠️  Bad request (400): {response.text[:200]}...")
            return False
            
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

# Sample resume and job description for realistic testing
sample_resume = """
Senior Software Engineer with 5+ years experience in Python, JavaScript, and cloud technologies. 
Expert in machine learning, data analysis, and web development. Strong background in agile methodologies, 
team leadership, and project management. Proficient in AWS, Docker, and microservices architecture.
"""

sample_job_description = """
We are seeking a Senior Software Engineer with expertise in Python, machine learning, and cloud platforms. 
The ideal candidate will have experience with AWS, containerization, and leading development teams. 
Strong analytical skills and agile development experience required.
"""

working_models = []
failed_models = []

print("=" * 80)
print("🎯 COMPREHENSIVE RESUME MATCHING MODEL TESTING")
print("=" * 80)
print("Testing models with realistic resume/job description content...")

# ==============================================================================
# SENTENCE TRANSFORMERS - BEST FOR RESUME MATCHING
# ==============================================================================
print("\n" + "🔥 SENTENCE TRANSFORMERS (Optimized for Text Similarity)")
print("=" * 80)

sentence_transformer_models = [
    # General purpose - excellent for resumes
    "sentence-transformers/all-MiniLM-L6-v2",           # Fast, good performance
    "sentence-transformers/all-MiniLM-L12-v2",          # Better performance, slower
    "sentence-transformers/all-mpnet-base-v2",          # Best performance, slowest
    "sentence-transformers/all-distilroberta-v1",       # Good speed/performance balance
    
    # Paraphrase detection - great for resume matching
    "sentence-transformers/paraphrase-MiniLM-L6-v2",    # Your original model
    "sentence-transformers/paraphrase-MiniLM-L12-v2",   # Better quality
    "sentence-transformers/paraphrase-mpnet-base-v2",   # Highest quality
    "sentence-transformers/paraphrase-distilroberta-base-v2", # Fast alternative
    
    # Multilingual (if needed for international resumes)
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/distiluse-base-multilingual-cased",
    
    # Domain-specific
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",  # Question-answer matching
    "sentence-transformers/multi-qa-mpnet-base-cos-v1", # Better QA matching
    
    # Newer models
    "sentence-transformers/gtr-t5-base",                # T5-based, very good
    "sentence-transformers/gtr-t5-large",               # Larger T5 model
]

for model in sentence_transformer_models:
    success = test_model(model, sample_resume, "feature-extraction")
    if success:
        working_models.append(("sentence-transformer", model))
    else:
        failed_models.append(model)
    time.sleep(1)  # Rate limiting

# ==============================================================================
# BERT-BASED MODELS - GOOD FOR TEXT UNDERSTANDING
# ==============================================================================
print("\n" + "🤖 BERT-BASED MODELS (Feature Extraction)")
print("=" * 80)

bert_models = [
    "bert-base-uncased",
    "bert-large-uncased", 
    "distilbert-base-uncased",
    "roberta-base",
    "distilroberta-base",
    "microsoft/DialoGPT-medium",
    "microsoft/codebert-base",
    "google/electra-small-discriminator",
    "google/electra-base-discriminator",
]

for model in bert_models:
    success = test_model(model, sample_resume, "feature-extraction")
    if success:
        working_models.append(("bert-based", model))
    else:
        failed_models.append(model)
    time.sleep(1)

# ==============================================================================
# SPECIALIZED EMBEDDING MODELS
# ==============================================================================
print("\n" + "🎯 SPECIALIZED EMBEDDING MODELS")
print("=" * 80)

embedding_models = [
    # OpenAI-style models
    "thenlper/gte-small",
    "thenlper/gte-base", 
    "thenlper/gte-large",
    
    # Instruct-based embeddings
    "hkunlp/instructor-base",
    "hkunlp/instructor-large",
    "hkunlp/instructor-xl",
    
    # E5 models (multilingual)
    "intfloat/e5-small-v2",
    "intfloat/e5-base-v2", 
    "intfloat/e5-large-v2",
    
    # BGE models (very good performance)
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "BAAI/bge-large-en-v1.5",
]

for model in embedding_models:
    success = test_model(model, sample_resume, "feature-extraction")
    if success:
        working_models.append(("specialized-embedding", model))
    else:
        failed_models.append(model)
    time.sleep(1)

# ==============================================================================
# RERANKING/SCORING MODELS (For Final Ranking)
# ==============================================================================
print("\n" + "🏆 RERANKING MODELS (For Final Resume Scoring)")
print("=" * 80)

# Test with query format for reranking
rerank_input = f"Query: {sample_job_description}\nDocument: {sample_resume}"

reranking_models = [
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "cross-encoder/ms-marco-MiniLM-L-12-v2", 
    "cross-encoder/ms-marco-electra-base",
    "sentence-transformers/ce-ms-marco-MiniLM-L6-v2",
]

for model in reranking_models:
    success = test_model(model, rerank_input, "text-classification")
    if success:
        working_models.append(("reranker", model))
    else:
        failed_models.append(model)
    time.sleep(1)

# ==============================================================================
# TEXT GENERATION MODELS (For Resume Analysis/Summary)
# ==============================================================================
print("\n" + "📝 TEXT GENERATION MODELS (For Resume Analysis)")
print("=" * 80)

generation_prompt = f"Analyze this resume and job match:\nJob: {sample_job_description}\nResume: {sample_resume}\nMatch score:"

generation_models = [
    "google/flan-t5-base",
    "google/flan-t5-small",
    "google/flan-t5-large",
    "microsoft/DialoGPT-medium",
    "facebook/bart-base",
    "t5-base",
    "t5-small",
]

for model in generation_models:
    success = test_model(model, generation_prompt, "text-generation")
    if success:
        working_models.append(("text-generation", model))
    else:
        failed_models.append(model)
    time.sleep(1)

# ==============================================================================
# SUMMARY REPORT
# ==============================================================================
print("\n" + "=" * 80)
print("📊 FINAL SUMMARY REPORT")
print("=" * 80)

print(f"\n✅ WORKING MODELS ({len(working_models)}):")
print("-" * 40)

categories = {}
for category, model in working_models:
    if category not in categories:
        categories[category] = []
    categories[category].append(model)

for category, models in categories.items():
    print(f"\n🔹 {category.upper().replace('-', ' ')} ({len(models)} models):")
    for model in models:
        print(f"   ✓ {model}")

print(f"\n❌ FAILED MODELS ({len(failed_models)}):")
print("-" * 40)
for model in failed_models:
    print(f"   ✗ {model}")

print(f"\n🎯 RECOMMENDATIONS FOR RESUME MATCHING:")
print("-" * 50)
print("1. PRIMARY EMBEDDING MODEL:")
if any("sentence-transformers/all-mpnet-base-v2" in model for _, model in working_models):
    print("   🥇 sentence-transformers/all-mpnet-base-v2 (Best quality)")
elif any("sentence-transformers/all-MiniLM-L6-v2" in model for _, model in working_models):
    print("   🥇 sentence-transformers/all-MiniLM-L6-v2 (Best speed/quality balance)")
else:
    print("   ⚠️  Check working sentence-transformer models above")

print("\n2. BACKUP/ALTERNATIVE MODELS:")
for category, models in categories.items():
    if category == "sentence-transformer" and len(models) > 1:
        print(f"   🥈 {models[1] if len(models) > 1 else models[0]}")
        break

print("\n3. UPDATE YOUR .env FILE:")
print("   EMBEDDING_MODEL=<choose_from_working_models_above>")
print("   GENERATION_MODEL=<choose_from_working_generation_models>")

print(f"\n🚀 Ready to update your resume matching system!")
print("=" * 80)