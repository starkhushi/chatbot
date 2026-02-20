import json
import requests

url = "http://0.0.0.0:8000/chat-stream"
headers = {"Content-Type": "application/json"}

chat_history = []
session_id = "test_session"

while True:
    user_input = input("You: ")

    if user_input.strip().lower() == "exit":
        break

    chat_history.append({"role": "user", "content": user_input})
    payload = json.dumps({"user_text": user_input, "chat": chat_history, "session_id": session_id})

    print("-" * 50, flush=True)
    print("Bot: ", end="", flush=True)

    try:
        with requests.post(url, headers=headers, data=payload, stream=True) as response:
            response.raise_for_status()
            assistant_message = []
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    text = chunk.decode("utf-8")
                    print(text, end="", flush=True)
                    assistant_message.append(text)

        assistant_text = "".join(assistant_message)
        chat_history.append({"role": "assistant", "content": assistant_text})
        print("\n" + "-" * 50, flush=True)
    except Exception as e:
        print(f"\nError: {e}", flush=True)

