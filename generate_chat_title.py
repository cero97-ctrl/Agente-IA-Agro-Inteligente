import argparse
import json
import os
import sys

import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Configure the generative AI model
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except KeyError as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(json.dumps({"error": f"Failed to configure Gemini API: {e}"}), file=sys.stderr)
    sys.exit(1)


def generate_title(chat_content: str) -> str:
    """
    Generates a concise title for a given chat history using an LLM.

    Args:
        chat_content: The full text of the chat conversation.

    Returns:
        A short, descriptive title.
    """
    if not chat_content or len(chat_content.split()) < 5:
        return "Nuevo Chat"

    prompt = f"""
    Tu tarea es generar un título corto y descriptivo para el siguiente historial de chat.
    El título debe resumir el tema principal de la conversación en no más de 10 palabras.
    Debe estar en el mismo idioma que la conversación.

    Historial de Chat:
    ---
    {chat_content}
    ---

    Título Sugerido:
    """

    try:
        response = model.generate_content(prompt)
        # Clean up the title, remove quotes or extra formatting
        title = response.text.strip().replace('"', '').replace("Título: ", "")
        return title
    except Exception as e:
        # Use a generic error message for security and simplicity
        print(json.dumps({"error": "Error generating title with LLM."}), file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to parse arguments and generate the chat title.
    """
    parser = argparse.ArgumentParser(description="Generate a title for a chat history.")
    parser.add_argument("--chat_content", type=str, required=True, help="The full content of the chat history.")

    args = parser.parse_args()

    title = generate_title(args.chat_content)
    print(json.dumps({"title": title}))
    sys.exit(0)

if __name__ == "__main__":
    main()