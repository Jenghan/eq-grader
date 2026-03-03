import httpx


class GeminiClient:
    """Google Gemini API client for generating natural text (Stage 3 feedback)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def generate_text(self, prompt: str, system: str = "") -> str:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        contents = []
        if system:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[System Instructions]\n{system}\n\n[User Request]\n{prompt}"}],
            })
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}],
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 512,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Extract text from Gemini response
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"Gemini returned no candidates: {data}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        return text.strip()

    async def health_check(self) -> bool:
        try:
            url = f"{self.base_url}/models/{self.model}?key={self.api_key}"
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False
