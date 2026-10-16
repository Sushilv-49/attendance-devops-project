import os
import sqlite3
from datetime import date

from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "data/attendance.db")
REQUIRED_PERCENT = 75


def get_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS subjects ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attendance ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER NOT NULL, "
        "att_date TEXT NOT NULL, status TEXT NOT NULL, "
        "UNIQUE(subject_id, att_date))"
    )
    return conn


def calculate_percentage(attended, total):
    if total == 0:
        return 0.0
    return round(attended * 100 / total, 1)


def get_status(percentage, total):
    if total == 0:
        return "No classes yet"
    if percentage >= REQUIRED_PERCENT:
        return "Safe"
    return "Low attendance"


def get_summary():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT s.id, s.name,
               COUNT(a.id) AS total,
               COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) AS attended
        FROM subjects s
        LEFT JOIN attendance a ON a.subject_id = s.id
        GROUP BY s.id, s.name
        ORDER BY s.name
        """
    ).fetchall()
    conn.close()

    summary = []
    for r in rows:
        pct = calculate_percentage(r["attended"], r["total"])
        summary.append(
            {
                "id": r["id"],
                "name": r["name"],
                "total": r["total"],
                "attended": r["attended"],
                "percentage": pct,
                "status": get_status(pct, r["total"]),
            }
        )
    return summary


PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Attendance Tracker</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 0 15px; }
    table { border-collapse: collapse; width: 100%; margin-top: 15px; }
    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
    th { background: #f0f0f0; }
    .safe { color: green; font-weight: bold; }
    .low { color: red; font-weight: bold; }
    .box { border: 1px solid #ddd; padding: 12px; margin-top: 15px; border-radius: 6px; }
  </style>
</head>
<body>
  <h2>Personal Attendance Tracker v2</h2>
  <p>DevOps Pipeline Successfully Executed</p>

  <div class="box">
    <h3>1. Add a Subject</h3>
    <form method="post" action="/add_subject">
      <input name="name" placeholder="e.g. Mathematics" required>
      <button type="submit">Add Subject</button>
    </form>
  </div>

  <div class="box">
    <h3>2. Mark Attendance</h3>
    {% if summary %}
    <form method="post" action="/mark">
      <select name="subject_id">
        {% for s in summary %}<option value="{{ s.id }}">{{ s.name }}</option>{% endfor %}
      </select>
      <input type="date" id="att_date" name="att_date" value="{{ today }}" required>
      <select name="status">
        <option>Present</option>
        <option>Absent</option>
      </select>
      <button type="submit">Save</button>
    </form>
    {% else %}
    <p>Add a subject first.</p>
    {% endif %}
  </div>

  <h3>3. Attendance Summary (required: {{ required }}%)</h3>
  <table>
    <tr>
      <th>Subject</th><th>Attended</th><th>Total Classes</th><th>Percentage</th><th>Status</th>
    </tr>
    {% for s in summary %}
    <tr>
      <td>{{ s.name }}</td>
      <td>{{ s.attended }}</td>
      <td>{{ s.total }}</td>
      <td>{{ s.percentage }}%</td>
      <td class="{{ 'low' if s.status == 'Low attendance' else 'safe' }}">{{ s.status }}</td>
    </tr>
    {% endfor %}
  </table>

  <script>
    var d = document.getElementById("att_date");
    if (d) { d.value = new Date().toLocaleDateString("en-CA"); }
  </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(
        PAGE,
        summary=get_summary(),
        today=date.today().isoformat(),
        required=REQUIRED_PERCENT,
    )


@app.route("/add_subject", methods=["POST"])
def add_subject():
    name = request.form.get("name", "").strip()
    if name:
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    return redirect("/")


@app.route("/mark", methods=["POST"])
def mark():
    subject_id = request.form.get("subject_id")
    att_date = request.form.get("att_date", "")
    status = request.form.get("status", "")
    try:
        date.fromisoformat(att_date)
    except ValueError:
        return redirect("/")
    if subject_id and status in ("Present", "Absent"):
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO attendance (subject_id, att_date, status) VALUES (?, ?, ?)",
            (subject_id, att_date, status),
        )
        conn.commit()
        conn.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)