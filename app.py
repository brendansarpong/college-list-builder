import os
import re
from flask import Flask, render_template, request, send_file, jsonify
from dotenv import load_dotenv

load_dotenv()

from llm_client import extract_profile, generate_blurbs
from matching import build_list
from pdf_generator import build_pdf

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    description = request.form.get("description", "").strip()
    if not description:
        return jsonify({"error": "please enter a student description"}), 400

    profile = extract_profile(description)

    college_list = build_list(profile)

    # flatten for the blurb call, only send the fields the llm actually needs
    all_colleges = college_list["reach"] + college_list["target"] + college_list["safety"]
    colleges_with_facts = [
        {
            "name": c["name"],
            "facts": {
                "state": c["state"], "climate": c["climate"], "setting": c["setting"],
                "strengths": c["strengths"], "vibe": c["vibe"],
            },
        }
        for c in all_colleges
    ]
    blurbs = generate_blurbs(profile, colleges_with_facts)

    student_name = profile.get("student_name") or "Student"
    pdf_buffer = build_pdf(student_name, college_list, blurbs)

    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", student_name)
    filename = f"college_list_{safe_name}.pdf"

    return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
