import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "colleges.json")

with open(DATA_PATH) as f:
    COLLEGES = json.load(f)


def load_colleges():
    return COLLEGES


def academic_fit(college, profile):
    """returns ('reach'|'target'|'safety', fit_score 0-1)"""
    sat = profile.get("sat")
    gpa = profile.get("gpa")

    lo, hi = college["sat_range"]
    mid = (lo + hi) / 2

    # if we don't have test scores just fall back on gpa, and if we have neither
    # treat everything as a target so the list isn't empty
    if sat is None and gpa is None:
        return "target", 0.5

    if sat is not None:
        if sat < lo - 40:
            category = "reach"
        elif sat > hi + 20:
            category = "safety"
        else:
            category = "target"
        # score is just how close the student is to the middle of the range
        fit_score = 1 - min(abs(sat - mid) / 300, 1)
        return category, fit_score

    # gpa-only fallback
    glo, ghi = college["gpa_range"]
    if gpa < glo - 0.15:
        category = "reach"
    elif gpa > ghi + 0.1:
        category = "safety"
    else:
        category = "target"
    return category, 1 - min(abs(gpa - (glo + ghi) / 2) / 1.2, 1)


INTEREST_KEYWORDS = {
    "programming": "computer_science", "coding": "computer_science", "software": "computer_science",
    "computer science": "computer_science", "cs": "computer_science",
    "marine biology": "marine_biology", "ocean": "marine_biology", "marine": "marine_biology",
    "engineering": "engineering", "robotics": "engineering",
    "business": "business", "entrepreneur": "business",
    "biology": "biology", "environmental": "environmental_science",
    "research": "research",
}


def interests_to_strengths(interests):
    out = set()
    for i in interests:
        i_lower = i.lower()
        for kw, strength in INTEREST_KEYWORDS.items():
            if kw in i_lower:
                out.add(strength)
    return out


def interest_score(college, profile):
    wanted = interests_to_strengths(profile.get("interests", []) or [])
    if not wanted:
        return 0.3  # neutral-ish, no strong signal either way
    overlap = wanted & set(college["strengths"])
    return min(len(overlap) / len(wanted), 1)


def geography_score(college, profile):
    score = 0.5
    climate_pref = profile.get("preferred_climate")
    if climate_pref and climate_pref != "no_preference":
        score += 0.3 if college["climate"] == climate_pref else -0.2

    home_state = profile.get("home_state")
    close = profile.get("wants_close_to_home")
    far = profile.get("wants_far_from_home")
    if home_state and close:
        # crude, just checks same state or same broad region -- good enough for v1
        same_region = _state_to_region(home_state) == college["region"]
        score += 0.2 if same_region else -0.15
    if home_state and far:
        same_region = _state_to_region(home_state) == college["region"]
        score += 0.15 if not same_region else -0.15

    return max(0, min(score, 1))


REGION_MAP = {
    "PA": "Northeast", "NY": "Northeast", "NJ": "Northeast", "MA": "Northeast", "CT": "Northeast",
    "RI": "Northeast", "DE": "Northeast", "MD": "Northeast", "NH": "Northeast", "VT": "Northeast", "ME": "Northeast",
    "OH": "Midwest", "IN": "Midwest", "IL": "Midwest", "MI": "Midwest", "WI": "Midwest", "MN": "Midwest",
    "GA": "South", "FL": "South", "NC": "South", "SC": "South", "TX": "South", "VA": "South", "TN": "South",
    "CA": "West", "OR": "West", "WA": "West", "AZ": "West", "HI": "West", "NV": "West", "CO": "West",
}


def _state_to_region(state):
    if not state:
        return None
    return REGION_MAP.get(state.upper()[:2], None)


def vibe_score(college, profile):
    wanted = set(v.lower() for v in (profile.get("vibe_keywords") or []))
    if not wanted:
        return 0.3
    overlap = wanted & set(college["vibe"])
    return min(len(overlap) / max(len(wanted), 1), 1)


def aid_score(college, profile):
    if not profile.get("needs_financial_aid"):
        return 0.5
    return college["aid_generosity"] / 5


def score_college(college, profile):
    _, fit = academic_fit(college, profile)
    i_score = interest_score(college, profile)
    g_score = geography_score(college, profile)
    v_score = vibe_score(college, profile)
    a_score = aid_score(college, profile)

    # weights -- tuned by eyeballing outputs, not scientific
    total = (fit * 0.25) + (i_score * 0.3) + (g_score * 0.15) + (v_score * 0.15) + (a_score * 0.15)
    return total


def build_list(profile, n_reach=3, n_target=4, n_safety=3):
    buckets = {"reach": [], "target": [], "safety": []}

    for college in COLLEGES:
        category, _ = academic_fit(college, profile)
        overall_score = score_college(college, profile)
        buckets[category].append((overall_score, college))

    for cat in buckets:
        buckets[cat].sort(key=lambda pair: pair[0], reverse=True)

    result = {
        "reach": [c for _, c in buckets["reach"][:n_reach]],
        "target": [c for _, c in buckets["target"][:n_target]],
        "safety": [c for _, c in buckets["safety"][:n_safety]],
    }

    used_names = {c["name"] for cat in result for c in result[cat]}

    # if a bucket came up empty (e.g. no safeties matched), backfill from target
    # so the counselor never gets handed a half-empty list -- pull from whatever's
    # left over in target[n_target:] first so we don't duplicate a school
    for cat in ["reach", "safety"]:
        if len(result[cat]) == 0:
            leftovers = [c for _, c in buckets["target"] if c["name"] not in used_names]
            fallback = leftovers[:2]
            result[cat] = fallback
            used_names.update(c["name"] for c in fallback)

    return result
