# College List Builder

Counselor pastes in a free-form description of a student, app generates a college list and
hands back a downloadable PDF.

## How it works

1. Free text goes to Claude, which extracts a structured student profile (GPA, SAT, interests, preferences, etc.) as JSON.
2. A plain Python scoring function (`matching.py`) matches that profile against a small curated dataset of colleges (`data/colleges.json`) and buckets them into reach / target / safety. No LLM involved in this step on purpose -- it means the app can't hallucinate a college that doesn't exist or make up stats.
3. Claude writes a short blurb for each *already-selected* school, using only the facts we hand it (so it can't invent facts about a real school either).
4. `pdf_generator.py` renders the final list with reportlab and the Flask route streams it back as a file download.

## Running it locally

1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and drop in a Groq API key (`GROQ_API_KEY=...`)
4. `python app.py`
5. Open `http://localhost:5000`

Getting a key: console.groq.com, sign up, generate a key. New accounts generally come with
some starter credit, which is more than enough for this (each generation is 2 short API calls).
If you'd rather not touch a paid provider at all, `llm_client.py` is small enough to point at
Groq's API instead (they have a genuinely free tier) -- same `messages.create`-style call, just
swap the client and model name.

## Deploying so it's not just localhost

Easiest free path: push this to a GitHub repo, then deploy on Render.com's free web service tier
(or Railway, both have no-spend tiers for something this small):

1. Push repo to GitHub.
2. On Render: New -> Web Service -> connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (add `gunicorn` to requirements.txt for production)
5. Add `GROQ_API_KEY` as an environment variable in the Render dashboard.
6. Deploy -- you'll get a public URL.

For the interview itself, running it locally and screen-sharing is completely fine too, they
said they'll extend the code live with you, so a local dev server is actually the more natural
setup for that part.

## Extending it

- Add more schools: just append to `data/colleges.json`, no code changes needed.
- Change how many reach/target/safety schools show up: `build_list()` in `matching.py` takes
  `n_reach`, `n_target`, `n_safety` as arguments.
- Tune the matching logic: the weights are in `score_college()` in `matching.py`.
- Change the PDF layout/branding: `pdf_generator.py`, all reportlab `ParagraphStyle` objects at the top.
