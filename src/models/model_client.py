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

    def generate(self, system_prompt, user_message, temperature=None, tools=None, disable_thinking=False):
        """
        Generate a response from the model, optionally offering it tools
        (Week 4 function calling).

        Args:
            system_prompt: The system instruction
            user_message: The user's question
            temperature: Optional override for temperature
            tools: Optional list of tool schemas in OpenAI function-calling
                   format (see BaseTool.to_openai_schema()). Translated to
                   Gemini's format internally when needed.
            disable_thinking: Gemini-only. Gemini 3.x "thinking" models can
                   spend most of max_output_tokens on internal reasoning
                   tokens before writing any visible text, cutting the
                   actual answer off mid-output (this is exactly what was
                   happening to the Week 5 Planner's JSON responses — a
                   61-character response was getting truncated because
                   thinking ate the rest of the 500-token budget). Pass
                   True for short, low-latency structured-output calls
                   (like planning) where you don't need the model to
                   "think" first; leave False (default) for normal
                   conversational responses. No-op for OpenAI.

        Returns:
            dict with 'response' (str or None), 'tool_calls' (list of
            {"id", "name", "arguments"} -- empty if the model answered
            directly), 'model', 'usage'.
        """
        temp = temperature if temperature is not None else self.temperature

        if self.provider == "openai":
            kwargs = dict(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temp,
                max_tokens=self.max_tokens
            )
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,  # JSON string
                    })

            return {
                "response": message.content,
                "tool_calls": tool_calls,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        # Gemini path
        config_kwargs = dict(
            system_instruction=system_prompt,
            temperature=temp,
            max_output_tokens=self.max_tokens
        )
        if tools:
            config_kwargs["tools"] = self._to_gemini_tools(tools)
        if disable_thinking:
            config_kwargs["thinking_config"] = self._genai_types.ThinkingConfig(thinking_budget=0)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=self._genai_types.GenerateContentConfig(**config_kwargs)
        )

        tool_calls = []
        for i, fc in enumerate(response.function_calls or []):
            tool_calls.append({
                "id": fc.id or f"call_{i}",
                "name": fc.name,
                "arguments": fc.args or {},  # already a dict
            })

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        # response.text raises if the response has no text part (e.g. it's
        # purely a function call) -- fall back to None in that case.
        try:
            response_text = response.text if not tool_calls else None
        except (ValueError, AttributeError):
            response_text = None

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "model": self.model_name,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }

    def generate_with_tool_result(self, system_prompt, user_message, tool_call, tool_result, temperature=None):
        """
        Second half of a tool-calling turn: send the executed tool's result
        back to the model and get its final natural-language response.

        Args:
            system_prompt: The same system instruction used in generate()
            user_message: The original user question
            tool_call: One entry from generate()'s 'tool_calls' list
                       ({"id", "name", "arguments"})
            tool_result: The dict returned by ToolExecutor.execute()
            temperature: Optional override for temperature

        Returns:
            dict with 'response', 'model', 'usage' (same shape as generate(),
            with tool_calls always empty here since this call doesn't offer
            tools again -- Week 4 is one tool call per turn).
        """
        import json
        temp = temperature if temperature is not None else self.temperature

        if self.provider == "openai":
            raw_args = tool_call["arguments"]
            args_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {"name": tool_call["name"], "arguments": args_str}
                    }]
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result)
                }
            ]
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=self.max_tokens
            )
            return {
                "response": response.choices[0].message.content,
                "tool_calls": [],
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        # Gemini path
        raw_args = tool_call["arguments"]
        args_dict = raw_args if isinstance(raw_args, dict) else json.loads(raw_args)

        function_call_part = self._genai_types.Part.from_function_call(
            name=tool_call["name"], args=args_dict
        )
        function_response_part = self._genai_types.Part.from_function_response(
            name=tool_call["name"], response=tool_result
        )
        contents = [
            self._genai_types.Content(role="user", parts=[self._genai_types.Part.from_text(text=user_message)]),
            self._genai_types.Content(role="model", parts=[function_call_part]),
            self._genai_types.Content(role="user", parts=[function_response_part]),
        ]
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
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
            "tool_calls": [],
            "model": self.model_name,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }

    def _to_gemini_tools(self, openai_tools):
        """Translate OpenAI-format tool schemas (BaseTool.to_openai_schema())
        into Gemini's Tool/FunctionDeclaration format."""
        declarations = []
        for t in openai_tools:
            fn = t["function"]
            declarations.append(self._genai_types.FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=fn.get("parameters", {})
            ))
        return [self._genai_types.Tool(function_declarations=declarations)]

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
