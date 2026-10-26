import json
import os
import sys
import uuid
from pathlib import Path
import requests
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    url = os.getenv("LLM_BASE_URL")
    key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not url or not key or not model:
        raise ValueError("В .env не заданы нужные настройки")
    return url.rstrip("/"), key, model

def parse_and_validate(api_data):
    try:
        content = api_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ValueError("Неверная структура ответа API")

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("Модель вернула невалидный JSON")

    req = {"category", "priority", "summary", "tags", "requires_human"}
    if not req.issubset(data):
        raise ValueError("В JSON не хватает полей")
    if data["category"] not in {"billing", "bug", "account", "feature_request", "other"}:
        raise ValueError("Неверная category")
    if data["priority"] not in {"low", "medium", "high"}:
        raise ValueError("Неверная priority")
    if not isinstance(data["summary"], str) or not data["summary"].strip():
        raise ValueError("Неверный summary")
    if not isinstance(data["tags"], list) or not all(isinstance(t, str) for t in data["tags"]):
        raise ValueError("Неверные tags")
    if type(data["requires_human"]) is not bool:
        raise ValueError("Неверный requires_human")
    
    return data

def save_result(data):
    path = Path("output/result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    data["request_id"] = uuid.uuid4().hex
    data["status"] = "validated"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    args = [arg for arg in sys.argv[1:] if arg != "--mock"]
    text = args[0] if args else input("Текст обращения: ")
    
    try:
        if not text.strip(): raise ValueError("Пустой ввод")
        if len(text) > 4000: raise ValueError("Текст больше 4000 символов")

        if "--mock" in sys.argv:
            fake_content = '{"category":"billing","priority":"high","summary":"Списание","tags":["payment"],"requires_human":true}'
            data = parse_and_validate({"choices": [{"message": {"content": fake_content}}]})
        else:
            url, key, model = load_config()
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": [{"role": "user", "content": text}]}
            
            try:
                r = requests.post(url + "/chat/completions", headers=headers, json=payload, timeout=30)
                r.raise_for_status()
                data = parse_and_validate(r.json())
            except requests.Timeout:
                raise ValueError("Тайм-аут")
            except requests.HTTPError as e:
                raise ValueError(f"HTTP Ошибка: {e.response.status_code}")

        save_result(data)
        print("Успех! Сохранено в output/result.json")
        
    except Exception as e:
        print("Ошибка:", e)

if __name__ == "__main__":
    main()