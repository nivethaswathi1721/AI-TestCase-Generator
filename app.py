from openpyxl import Workbook
from io import BytesIO
from flask import send_file
from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai
from datetime import datetime
import os
import markdown
from zoneinfo import ZoneInfo


# Load environment variables
load_dotenv()

# Read API key
api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Create Flask app
app = Flask(__name__)

generated_markdown = ""
generated_html = ""

# Home Page
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Generate Test Cases
@app.route("/generate", methods=["POST"])
def generate():

    requirement = request.form["requirement"]

    prompt = f"""
You are a Senior QA Automation Engineer with over 10 years of experience.

Generate a professional QA Test Case document in MARKDOWN.

Follow the format EXACTLY.

# Assumptions & Preconditions

Generate ONLY FIVE assumptions that are directly related to the given software requirement.

Rules:
- Generate exactly 5 bullet points.
- Keep each assumption short.
- Make them feature-specific.
- Do NOT generate generic assumptions.
- Use professional QA language.

Example (for Login):

- Minimum Password Length: 8 characters.
- Maximum Password Length: 64 characters.
- Account Lockout Threshold: 5 consecutive failed login attempts.
- Standard Email Format (RFC): Maximum 254 characters.
- Password field is masked by default.

For other modules (Registration, Payment, Search, etc.), generate relevant assumptions instead of login assumptions.

---

# Test Cases

Generate a markdown table with these columns exactly.

| Test Case ID | Category | Test Scenario | Test Steps | Test Data | Expected Result | Priority |

Generate at least 15 test cases including:

- Functional
- Positive
- Negative
- Boundary Value Analysis (BVA)
- Edge Cases

Rules:

- Test Case IDs should be like TC_001, TC_002...
- Test Steps should contain ONLY 3 concise numbered steps.
- Keep each step under 8 words.
- Avoid unnecessary explanations.
- Test Data should contain only Email and Password.
- Expected Results should be clear and concise.
- Priority should be High, Medium or Low.

---

# QA Execution Notes

Generate only 5 important QA execution notes related to the given feature.

Use bullet points.

---

# Summary

At the end provide:

- Total Test Cases Generated
- Functional Test Cases
- Positive Test Cases
- Negative Test Cases
- BVA Test Cases
- Edge Test Cases

Software Requirement:

{requirement}

Return ONLY markdown.
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )

    result = markdown.markdown(
        response.text,
        extensions=["tables"]
    )

    global generated_markdown
    global generated_html

    generated_markdown = response.text
    generated_html = result
    

    # Current Date & Time
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    generation_date = now.strftime("%d-%m-%Y")
    generation_time = now.strftime("%I:%M %p")

    return render_template(
          "result.html",
          result=result,
        generation_date=generation_date,
        generation_time=generation_time
    )

@app.route("/export_excel")
def export_excel():

    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"

    # Header
    ws.append([
        "Test Case ID",
        "Category",
        "Test Scenario",
        "Test Steps",
        "Test Data",
        "Expected Result",
        "Priority"
    ])

    global generated_markdown

    lines = generated_markdown.split("\n")

    for line in lines:
      if line.startswith("| TC_"):

           cols = [c.strip() for c in line.split("|")[1:-1]]

           if len(cols) >= 7:
               ws.append(cols[:7])

    

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="AI_Test_Cases.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))