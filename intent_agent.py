import os
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

class IntentAgent:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model_name = "deepseek-v4.1-flash"

        # Từ khóa Local
        self.delete_keywords = [
            'delete', 'erase', 'remove', 'gdpr', 'forget', 'right to be forgotten',
            'close account', 'clear my data', 'purge', 'wipe', 'privacy request',
            'destroy', 'pii', 'anonymize', 'terminate account'
        ]
        
        self.non_delete_keywords = [
            'reset password', 'change password', 'forgot password', 'order status',
            'track order', 'cancel order', 'refund', 'shipping', 'discount', 'payment',
            'how to', 'how can i', 'invoice', 'login', 'support', 'help'
        ]

    def _call_deepseek_api(self, prompt: str) -> str:
        if not self.api_key:
            return "NO"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 10
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.api_url, data=data, headers=headers, method='POST')

        # Thử tối đa 2 lần với timeout ngắn (4 giây)
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=4) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result['choices'][0]['message']['content'].strip()
            except Exception:
                continue
        return "NO"

    def is_deletion_request(self, request_text: str) -> bool:
        if not request_text or not str(request_text).strip():
            return False

        text_lower = str(request_text).lower()

        negation_patterns = ["not delete", "don't delete", "dont delete", "never delete", "not erase", "don't erase"]
        has_negation = any(pattern in text_lower for pattern in negation_patterns)

        if not has_negation and any(kw in text_lower for kw in self.delete_keywords):
            return True

        if any(kw in text_lower for kw in self.non_delete_keywords) and not any(kw in text_lower for kw in self.delete_keywords):
            return False

        prompt = f"""Analyze the following customer message and determine if the user is requesting to DELETE, ERASE, or REMOVE their account, personal data, or profile (GDPR right to be forgotten).

Message: "{request_text}"

Respond with ONLY one word: YES or NO."""
        ans = self._call_deepseek_api(prompt)
        return "YES" in ans.upper()

    def classify_batch(self, request_texts: list[str]) -> list[bool]:
        """Xử lý phân loại song song 20 luồng cùng lúc."""
        with ThreadPoolExecutor(max_workers=20) as executor:
            return list(executor.map(self.is_deletion_request, request_texts))