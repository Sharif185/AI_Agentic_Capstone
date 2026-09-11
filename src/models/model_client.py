import os
from dotenv import load_dotenv

load_dotenv()


class ModelClient:
    """
    Wrapper for foundation model API calls.

    Supports two providers, auto-selected from MODEL_NAME in .env:
      - OpenAI  (e.g. gpt-4o-mini)              -> requires OPENAI_API_KEY
      - Gemini  (any model_name starting "gemini") -> requires GEMINI_API_KEY

    This lets the app fall back to Gemini's free tier (per the Model
    Selection Note) without changing any calling code in main.py.
    """

    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.temperature = float(os.getenv("TEMPERATURE", 0.1))
        self.max_tokens = int(os.getenv("MAX_TOKENS", 500))
        self.provider = "gemini" if self.model_name.lower().startswith("gemini") else "openai"

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            from google import genai
            self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            self._genai_types = __import__("google.genai.types", fromlist=["types"])

    def generate(self, system_prompt, user_message, temperature=None):
        """
        Generate a response from the model.

        Args:
            system_prompt: The system instruction
            user_message: The user's question
            temperature: Optional override for temperature

        Returns:
            dict with 'response', 'model', 'usage'
        """
        temp = temperature if temperature is not None else self.temperature

        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temp,
                max_tokens=self.max_tokens
            )
            return {
                "response": response.choices[0].message.content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        # Gemini path
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=self._genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temp,
                max_output_tokens=self.max_tokens
            )
        )

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return {
            "response": response.text,
            "model": self.model_name,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }

    def test_connection(self):
        """Test that the API works."""
        try:
            result = self.generate(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'Connection successful' and nothing else."
            )
            return result["response"]
        except Exception as e:
            return f"Connection failed: {str(e)}"
