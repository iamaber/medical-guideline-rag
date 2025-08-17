import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL_NAME)


def summarizer(text: str) -> str:
    answer = model.generate_content(
        f"Summarize in 500 words:\n{text}",
        generation_config={"max_output_tokens": 500, "temperature": 0.3},
    )
    return answer.text
