import requests
from config import settings

def test_groq():
    key = settings.groq_api_key
    base_url = settings.llm_base_url
    model = settings.llm_model
    
    print(f"Testing Groq Integration...")
    print(f"URL: {base_url}")
    print(f"Key length: {len(key)}")
    print(f"Model: {model}")
    
    if not key or "gsk_" not in key:
        print("Error: No has configurado una GROQ_API_KEY válida en .env")
        return

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model, 
        "messages": [{"role": "user", "content": "Hola, responde brevemente."}]
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(f"Response: {response.json()['choices'][0]['message']['content']}")
        else:
            print(f"Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_groq()
