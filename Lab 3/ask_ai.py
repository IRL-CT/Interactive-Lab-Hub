import requests

def ask_ai(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi3:mini", "prompt": question, "stream": False}
    )
    return response.json().get('response', 'No response')

if __name__ == "__main__":
    answer = ask_ai("How should I greet users?")
    print("AI says:", answer)
