import json
import re


class JsonModelGateway:
    """Production JSON gateway. Imports model dependencies only when invoked."""

    def generate(self, *, system: str, payload: dict) -> dict:
        from langchain_openai import ChatOpenAI
        from cs_career_guide.ai_config import get_llm_kwargs
        from openai import APITimeoutError

        model = ChatOpenAI(temperature=0, max_retries=0, **get_llm_kwargs())
        try:
            response = model.invoke([
                ('system', system),
                ('human', json.dumps(payload, ensure_ascii=False)),
            ])
        except APITimeoutError:
            raise TimeoutError('Model request exceeded the configured timeout') from None
        text = response.content if isinstance(response.content, str) else str(response.content)
        return self._parse(text)

    @staticmethod
    def _parse(text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            fenced = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if fenced:
                return json.loads(fenced.group(1))
            start, end = text.find('{'), text.rfind('}')
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise ValueError('model response is not valid JSON')
