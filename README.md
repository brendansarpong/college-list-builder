# College List Builder!

A counselor pastes in a free-form description of a student, and the app spits out a
college list as a downloadable PDF. Built for a take-home, but hopefully useful beyond that.

## How it works

There are three steps, and only two of them touch an LLM on purpose:

1. The free text goes to an LLM, which pulls out a structured student profile: GPA, SAT,
   interests, preferences, that kind of thing — as JSON.
2. A plain Python scoring function (`matching.py`) matches that profile against a curated
   list of colleges (`data/colleges.json`) and sorts them into reach/target/safety.
   No LLM involved here. This is deliberate — it means the app can't recommend a school
   that doesn't exist or make up stats about a real one.
3. The LLM writes a short blurb for each school that's already been picked, using only the
   facts it's handed. Same idea... it can describe, but it can't invent.

Then `pdf_generator.py` turns all of that into the PDF and the Flask route sends it back
as a download.

## Running it locally

1. `python -m venv venv`
2. Activate it — `venv\Scripts\Activate.ps1` on Windows, `source venv/bin/activate` on Mac/Linux
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and drop in a Groq API key (`GROQ_API_KEY=...`)
5. `python app.py`
6. Open `http://localhost:5000`

Not super necessary since I got it running on Render

Get a key at console.groq.com. This is the free tier, so no card needed. Each generation is two short
API calls, so you'll get a lot of runs out of it before you'd hit any type of limit.

## Deploying

This repo is set up to deploy on Render's free tier:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variable: `GROQ_API_KEY`

## Extending it

- **Add a school:** just add an entry to `data/colleges.json`, no code changes needed.
- **Change how many reach/target/safety schools show up:** `build_list()` in `matching.py`
  takes `n_reach`, `n_target`, `n_safety` as arguments.
- **Tune the matching logic:** weights live in `score_college()` in `matching.py`.
- **Change the PDF layout:** `pdf_generator.py`, all the styling is in the `ParagraphStyle`
  objects near the top of the file.

The college dataset right now is a curated set of about 50 or so well-known schools rather than
every accredited college in the US. This was intentional. I wanted a small pool of schools that could 
be expanded in the future.
