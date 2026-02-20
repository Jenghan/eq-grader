import json
import httpx


class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(180.0, connect=10.0)

    async def generate(self, prompt: str, system: str = "") -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2048},
        }
        for attempt in range(3):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                raw = resp.json().get("response", "")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                if attempt == 2:
                    raise ValueError(f"LLM returned invalid JSON after 3 attempts: {raw[:200]}")
        return {}

    async def generate_text(self, prompt: str, system: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.6, "num_predict": 512},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
