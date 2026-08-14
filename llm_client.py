import os
import json
import re
from openai import OpenAI

# groq's api is openai-compatible, so we just point the openai client at their
# endpoint instead of anthropic's -- free tier, no card required
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "llama-3.3-70b-versatile"

# json can be found wrapped in code fences sometimes, this strips that
def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text)
        text = re.sub(r"```$", "", text)
    return json.loads(text.strip())


EXTRACTION_PROMPT = """You are helping a college counselor turn a free-form note about a student into structured data.

Read the note below and return ONLY a JSON object (no prose, no markdown fences) with this shape:

{{
  "student_name": string,
  "interests": [string, ...],
  "gpa": number or null,
  "sat": number or null,
  "act": number or null,
  "ap_scores": [{{"subject": string, "score": number}}, ...],
  "home_state": string or null,
  "wants_close_to_home": true/false/null,
  "wants_far_from_home": true/false/null,
  "preferred_climate": "warm" | "cold" | "no_preference",
  "needs_financial_aid": true/false/null,
  "vibe_keywords": [string, ...],
  "notes": string
}}

vibe_keywords should be pulled from things like: practical, hands_on, research, small_classes, big_school,
coastal, outdoorsy, artsy, athletics, quirky, intense, co_op -- only include ones actually implied by the note.
If something isn't mentioned, use null (or empty list). Don't make stuff up.

Student note:
\"\"\"{note}\"\"\"
"""


def extract_profile(free_text):
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(note=free_text)}],
    )
    raw = resp.choices[0].message.content
    try:
        return _extract_json(raw)
    except Exception:
        # fallback so a weird llm response doesn't 500 the whole request
        return {
            "student_name": "Student",
            "interests": [],
            "gpa": None, "sat": None, "act": None,
            "ap_scores": [], "home_state": None,
            "wants_close_to_home": None, "wants_far_from_home": None,
            "preferred_climate": "no_preference",
            "needs_financial_aid": None,
            "vibe_keywords": [],
            "notes": free_text[:300],
        }


BLURB_PROMPT = """You are a college counselor writing a short, warm note explaining why each school below is a good
fit for a specific student. Use ONLY the facts provided about the student and about each college -- do not invent
facts, rankings, or statistics that aren't given to you.

Student profile:
{profile}

Colleges to write about (use the "facts" field, don't add outside facts):
{colleges}

Return ONLY a JSON object mapping college name -> a 2-3 sentence blurb. No markdown fences, no extra keys.
"""


def generate_blurbs(profile, colleges_with_facts):
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": BLURB_PROMPT.format(
                profile=json.dumps(profile),
                colleges=json.dumps(colleges_with_facts),
            ),
        }],
    )
    raw = resp.choices[0].message.content
    try:
        return _extract_json(raw)
    except Exception:
        # if this fails just give every school a generic blurb, better than crashing
        return {c["name"]: "A strong fit based on the student's profile and interests." for c in colleges_with_facts}
