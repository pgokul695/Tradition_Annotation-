import json
from pathlib import Path
from ..db import settings

SCHEMA = {
 "type":"object", "properties": {**{k:{"type":"array","items":{"type":"string"}} for k in ["objects","animals","people","colors","patterns","religious_elements"]}, "scene":{"type":"string"}, "caption":{"type":"string"}, "description":{"type":"string"}, "confidence":{"type":"number"}},
 "required":["objects","animals","people","colors","patterns","religious_elements","scene","caption","description","confidence"]
}
def annotate_file(path: Path, style: str):
    if not settings.gemini_api_key: raise RuntimeError("GEMINI_API_KEY is not configured")
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("Install dependencies from backend/requirements.txt (google-genai is required)") from exc
    prompt = f'''You are annotating Indian traditional paintings for a research dataset on tradition-sensitive visual assessment. You are told the tradition's name in advance ({style}) — use that knowledge to describe what makes this image characteristic (or atypical) of that tradition. Return JSON matching the supplied schema. scene is one literal sentence; caption is one publishable sentence; description is 4-8 sentences covering composition, technique, palette, subject, symbolism and visual markers of {style}; confidence is 0-1.'''
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=[prompt, types.Part.from_bytes(data=path.read_bytes(), mime_type="image/jpeg")], config=types.GenerateContentConfig(response_mime_type="application/json", response_json_schema=SCHEMA))
    return json.loads(response.text)
