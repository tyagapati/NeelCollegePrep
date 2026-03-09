# ============================================================
# College Prep Command Center — app.py
# Stack: Flask + SQLite + Jinja2 (zero cost deployment)
# Deploy free on: Render.com, PythonAnywhere, or Railway
# ============================================================

import os, json, sqlite3, secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, session, flash, make_response, g)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DATABASE = os.path.join(os.path.dirname(__file__), "tracker.db")

# ── Pillar & Metric Definitions ─────────────────────────────
PILLARS = [
    {"id":"creativity","icon":"🎵","label":"Creativity","color":"#3B82F6","desc":"Music creation, production, performance"},
    {"id":"communication","icon":"⚖️","label":"Communication","color":"#8B5CF6","desc":"Youth & Gov, oratory, advocacy"},
    {"id":"leadership","icon":"👑","label":"Leadership","color":"#F59E0B","desc":"Y&G leadership, mentoring, organizing"},
    {"id":"impact","icon":"💛","label":"Social Impact","color":"#EC4899","desc":"Band fundraising, instrument donations"},
    {"id":"entrepreneurship","icon":"🚀","label":"Entrepreneurship","color":"#10B981","desc":"Music marketing app"},
]

METRICS = {
    "creativity": [
        {"id":"monthly_listeners","label":"Monthly Listeners","start":20,"target":3000,"unit":"","type":"number"},
        {"id":"total_streams","label":"Total Streams","start":1000,"target":30000,"unit":"","type":"number"},
        {"id":"published_tracks","label":"Published Tracks","start":3,"target":12,"unit":"","type":"number"},
        {"id":"music_revenue","label":"Music Revenue ($)","start":0,"target":500,"unit":"$","type":"number"},
        {"id":"competitions","label":"Competitions Entered","start":0,"target":2,"unit":"","type":"number"},
        {"id":"performances","label":"Live Performances","start":2,"target":15,"unit":"","type":"number"},
        {"id":"collabs","label":"Artist Collaborations","start":0,"target":4,"unit":"","type":"number"},
        {"id":"press_features","label":"Press/Blog Features","start":0,"target":2,"unit":"","type":"number"},
    ],
    "communication": [
        {"id":"yg_placement","label":"Y&G Best Placement","start":2,"target":6,"unit":"","type":"milestone",
         "milestones":["3rd Districts","2nd Districts","1st Districts","State Top 5","State Winner","Nationals"]},
        {"id":"speeches","label":"Speeches Given","start":2,"target":10,"unit":"","type":"number"},
        {"id":"opeds","label":"Op-Eds Published","start":0,"target":4,"unit":"","type":"number"},
        {"id":"debate_comps","label":"Oratory Competitions","start":0,"target":3,"unit":"","type":"number"},
    ],
    "leadership": [
        {"id":"leadership_titles","label":"Leadership Titles","start":0,"target":2,"unit":"","type":"number"},
        {"id":"mentees","label":"Mentees","start":0,"target":3,"unit":"","type":"number"},
        {"id":"events_organized","label":"Events Organized","start":0,"target":3,"unit":"","type":"number"},
        {"id":"team_meetings","label":"Team Meetings Led","start":0,"target":20,"unit":"","type":"number"},
    ],
    "impact": [
        {"id":"band_revenue","label":"Band Revenue ($)","start":500,"target":10000,"unit":"$","type":"number"},
        {"id":"instruments_donated","label":"Instruments Donated","start":0,"target":20,"unit":"","type":"number"},
        {"id":"gigs_played","label":"Gigs Played","start":3,"target":35,"unit":"","type":"number"},
        {"id":"families_helped","label":"Families Impacted","start":0,"target":20,"unit":"","type":"number"},
        {"id":"testimonials","label":"Testimonials Collected","start":0,"target":5,"unit":"","type":"number"},
    ],
    "entrepreneurship": [
        {"id":"app_users","label":"App Users","start":0,"target":250,"unit":"","type":"number"},
        {"id":"app_testimonials","label":"User Testimonials","start":0,"target":10,"unit":"","type":"number"},
        {"id":"app_revenue","label":"App Revenue ($)","start":0,"target":50,"unit":"$","type":"number"},
        {"id":"comp_entries","label":"Competition Entries","start":0,"target":2,"unit":"","type":"number"},
        {"id":"app_milestone","label":"App Stage","start":1,"target":6,"unit":"","type":"milestone",
         "milestones":["Idea","Building MVP","MVP Done","Beta Launch","Public Launch","Growing"]},
    ],
}

WEEKLY_TASKS = {
    "creativity": [
        "Work on current single (production/recording)",
        "Create 3 short-form videos (TikTok/Reels/Shorts)",
        "Submit to 2+ playlist curators via SubmitHub",
        "Reach out to 1 artist for collaboration",
        "Update Spotify for Artists & track stats",
        "Practice instrument/vocals (2+ hours)",
    ],
    "communication": [
        "Research/outline Y&G case or bill",
        "Practice speech delivery (30 min)",
        "Watch 2 winning debate performances",
        "Draft or edit op-ed / blog post",
    ],
    "leadership": [
        "Reach out to / mentor an underclassman",
        "Plan or lead a Y&G practice session",
        "Write leadership journal entry (5 min)",
    ],
    "impact": [
        "Send 3 gig booking inquiries",
        "Rehearse with band",
        "Post about mission on social media",
        "Reach out to 1 community organization",
    ],
    "entrepreneurship": [
        "Code / build app features (3+ hours)",
        "Talk to 1 potential user for feedback",
        "Record app progress (screenshot/video)",
    ],
}

ESSAY_ANGLES = [
    {"id":"common","label":"Common App — Personal Essay","prompt":"The moment music became more than a hobby","pillars":["creativity","impact"]},
    {"id":"whylaw","label":"Why Pre-Law / PoliSci","prompt":"How advocacy taught you systems matter","pillars":["communication","leadership"]},
    {"id":"community","label":"Community Essay","prompt":"Instrument donations & access/equity","pillars":["impact","leadership"]},
    {"id":"challenge","label":"Challenge Essay","prompt":"Building from scratch as first-gen","pillars":["creativity","entrepreneurship"]},
    {"id":"curiosity","label":"Intellectual Curiosity","prompt":"Building the app — your problem → everyone's solution","pillars":["entrepreneurship","creativity"]},
]

# ── Database ─────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS metrics (
        id TEXT PRIMARY KEY,
        pillar TEXT NOT NULL,
        current_value REAL NOT NULL,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS metric_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_id TEXT NOT NULL,
        value REAL NOT NULL,
        recorded_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS weekly_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_id TEXT NOT NULL UNIQUE,
        logged_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS essay_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        angle_id TEXT NOT NULL,
        pillar TEXT,
        note TEXT NOT NULL,
        source_task TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS custom_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pillar TEXT NOT NULL,
        label TEXT NOT NULL,
        active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    # seed metrics if empty
    cur = db.execute("SELECT COUNT(*) FROM metrics")
    if cur.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        for pid, ms in METRICS.items():
            for m in ms:
                db.execute("INSERT INTO metrics (id, pillar, current_value, updated_at) VALUES (?,?,?,?)",
                           (f"{pid}.{m['id']}", pid, m["start"], now))
    db.commit()
    db.close()

# ── Helpers ──────────────────────────────────────────────────
def get_week_id(d=None):
    d = d or datetime.now()
    return d.strftime("%Y-W%U")

def get_metric_val(db, metric_id):
    r = db.execute("SELECT current_value FROM metrics WHERE id=?", (metric_id,)).fetchone()
    return r["current_value"] if r else 0

def pct(cur, target):
    if target == 0: return 100
    return min(100, round((cur / target) * 100))

def pillar_progress(db, pid):
    ms = METRICS.get(pid, [])
    if not ms: return 0
    total = sum(pct(get_metric_val(db, f"{pid}.{m['id']}"), m["target"]) for m in ms)
    return round(total / len(ms))

def momentum_score(db):
    all_p = [pillar_progress(db, p["id"]) for p in PILLARS]
    return round(sum(all_p) / len(all_p)) if all_p else 0

def generate_nudges(db):
    nudges = []
    for p in PILLARS:
        pid = p["id"]
        prog = pillar_progress(db, pid)
        for m in METRICS[pid]:
            mid = f"{pid}.{m['id']}"
            cur = get_metric_val(db, mid)
            progress = pct(cur, m["target"])
            if progress < 15 and m["target"] > 0 and m["type"] == "number":
                remaining = m["target"] - cur
                nudges.append({
                    "pillar": p["icon"], "type": "behind",
                    "msg": f"{m['label']}: {int(cur)}/{m['target']} ({progress}%). "
                           f"You need ~{max(1, round(remaining/15))} more per month to hit target."
                })
        # check recent weekly completion for this pillar
        recent = db.execute(
            "SELECT data FROM weekly_logs ORDER BY logged_at DESC LIMIT 2"
        ).fetchall()
        if recent:
            done = skip = 0
            for r in recent:
                d = json.loads(r["data"])
                for t in d.get("tasks", []):
                    if t.get("pillar") == pid:
                        if t.get("status") == "done": done += 1
                        else: skip += 1
            total = done + skip
            if total > 0 and done / total < 0.4:
                nudges.append({
                    "pillar": p["icon"], "type": "activity",
                    "msg": f"{p['label']}: Only {done}/{total} tasks done recently. Block more time for this."
                })

    # specific nudges
    band_rev = get_metric_val(db, "impact.band_revenue")
    if band_rev < 5000:
        gigs = max(1, round((10000 - band_rev) / 300))
        nudges.append({"pillar": "💛", "type": "tip",
                       "msg": f"At $300/gig avg, you need ~{gigs} more gigs for $10K. Book wedding season now!"})

    app_users = get_metric_val(db, "entrepreneurship.app_users")
    if app_users < 20:
        nudges.append({"pillar": "🚀", "type": "tip",
                       "msg": "Ship your MVP first — even if it's rough. 20 real users with feedback beats a perfect app nobody's tried."})

    listeners = get_metric_val(db, "creativity.monthly_listeners")
    if listeners < 200:
        nudges.append({"pillar": "🎵", "type": "tip",
                       "msg": "Focus on 3 short videos/week on TikTok & Reels. Consistency compounds — most artists see a spike around month 3-4."})

    return nudges[:8]

# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def dashboard():
    db = get_db()
    mom = momentum_score(db)
    pillar_data = []
    for p in PILLARS:
        prog = pillar_progress(db, p["id"])
        metrics_list = []
        for m in METRICS[p["id"]]:
            cur = get_metric_val(db, f"{p['id']}.{m['id']}")
            metrics_list.append({**m, "current": cur, "pct": pct(cur, m["target"])})
        pillar_data.append({**p, "progress": prog, "metrics": metrics_list})
    nudges = generate_nudges(db)
    cur_week = get_week_id()
    has_log = db.execute("SELECT 1 FROM weekly_logs WHERE week_id=?", (cur_week,)).fetchone()
    return render_template("dashboard.html",
        momentum=mom, pillars=pillar_data, nudges=nudges,
        cur_week=cur_week, has_log=bool(has_log), essays=ESSAY_ANGLES)

@app.route("/pillars")
@app.route("/pillars/<pillar_id>")
def pillars(pillar_id=None):
    db = get_db()
    pillar_data = []
    for p in PILLARS:
        prog = pillar_progress(db, p["id"])
        metrics_list = []
        for m in METRICS[p["id"]]:
            mid = f"{p['id']}.{m['id']}"
            cur = get_metric_val(db, mid)
            hist = db.execute(
                "SELECT value, recorded_at FROM metric_history WHERE metric_id=? ORDER BY recorded_at DESC LIMIT 12",
                (mid,)
            ).fetchall()
            metrics_list.append({**m, "current": cur, "pct": pct(cur, m["target"]),
                                 "history": [{"v": h["value"], "d": h["recorded_at"][:10]} for h in reversed(hist)]})
        pillar_data.append({**p, "progress": prog, "metrics": metrics_list})
    return render_template("pillars.html", pillars=pillar_data, active=pillar_id or PILLARS[0]["id"])

@app.route("/api/metric", methods=["POST"])
def update_metric():
    db = get_db()
    data = request.json
    mid = data["id"]
    val = float(data["value"])
    now = datetime.now().isoformat()
    db.execute("UPDATE metrics SET current_value=?, updated_at=? WHERE id=?", (val, now, mid))
    db.execute("INSERT INTO metric_history (metric_id, value, recorded_at) VALUES (?,?,?)", (mid, val, now))
    db.commit()
    return jsonify({"ok": True, "value": val})

@app.route("/weekly")
def weekly():
    db = get_db()
    cur_week = get_week_id()
    existing = db.execute("SELECT data FROM weekly_logs WHERE week_id=?", (cur_week,)).fetchone()
    existing_data = json.loads(existing["data"]) if existing else None
    tasks_by_pillar = {}
    for p in PILLARS:
        pid = p["id"]
        tasks = []
        for t in WEEKLY_TASKS.get(pid, []):
            status = "pending"
            note = ""
            if existing_data:
                for et in existing_data.get("tasks", []):
                    if et.get("label") == t:
                        status = et.get("status", "pending")
                        note = et.get("note", "")
            tasks.append({"label": t, "pillar": pid, "status": status, "note": note})
        # add custom tasks
        custom = db.execute("SELECT label FROM custom_tasks WHERE pillar=? AND active=1", (pid,)).fetchall()
        for c in custom:
            status = "pending"
            note = ""
            if existing_data:
                for et in existing_data.get("tasks", []):
                    if et.get("label") == c["label"]:
                        status = et.get("status", "pending")
                        note = et.get("note", "")
            tasks.append({"label": c["label"], "pillar": pid, "status": status, "note": note, "custom": True})
        tasks_by_pillar[pid] = tasks
    past_logs = db.execute("SELECT week_id, data FROM weekly_logs ORDER BY logged_at DESC LIMIT 8").fetchall()
    past = []
    for l in past_logs:
        d = json.loads(l["data"])
        done = sum(1 for t in d.get("tasks",[]) if t.get("status")=="done")
        total = len(d.get("tasks",[]))
        past.append({"week": l["week_id"], "done": done, "total": total, "reflection": d.get("reflection","")})
    return render_template("weekly.html", pillars=PILLARS, tasks=tasks_by_pillar,
                           cur_week=cur_week, has_existing=bool(existing_data), past_logs=past)

@app.route("/api/weekly", methods=["POST"])
def save_weekly():
    db = get_db()
    data = request.json
    wid = get_week_id()
    now = datetime.now().isoformat()
    payload = json.dumps(data)
    existing = db.execute("SELECT 1 FROM weekly_logs WHERE week_id=?", (wid,)).fetchone()
    if existing:
        db.execute("UPDATE weekly_logs SET data=?, logged_at=? WHERE week_id=?", (payload, now, wid))
    else:
        db.execute("INSERT INTO weekly_logs (week_id, logged_at, data) VALUES (?,?,?)", (wid, now, payload))
    # auto-add essay notes for completed tasks with notes
    for t in data.get("tasks", []):
        if t.get("status") == "done" and t.get("note"):
            pillar = t.get("pillar", "")
            relevant = [a for a in ESSAY_ANGLES if pillar in a.get("pillars", [])]
            for angle in relevant:
                db.execute("INSERT INTO essay_notes (angle_id, pillar, note, source_task, created_at) VALUES (?,?,?,?,?)",
                           (angle["id"], pillar, t["note"], t.get("label",""), now))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/custom-task", methods=["POST"])
def add_custom_task():
    db = get_db()
    data = request.json
    db.execute("INSERT INTO custom_tasks (pillar, label) VALUES (?,?)", (data["pillar"], data["label"]))
    db.commit()
    return jsonify({"ok": True})

@app.route("/essay")
def essay():
    db = get_db()
    angles = []
    for a in ESSAY_ANGLES:
        notes = db.execute(
            "SELECT note, pillar, source_task, created_at FROM essay_notes WHERE angle_id=? ORDER BY created_at DESC",
            (a["id"],)
        ).fetchall()
        angles.append({**a, "notes": [dict(n) for n in notes]})
    return render_template("essay.html", angles=angles, pillars=PILLARS)

@app.route("/api/essay-note", methods=["POST"])
def add_essay_note():
    db = get_db()
    data = request.json
    now = datetime.now().isoformat()
    db.execute("INSERT INTO essay_notes (angle_id, pillar, note, source_task, created_at) VALUES (?,?,?,?,?)",
               (data["angle_id"], data.get("pillar",""), data["note"], data.get("source","manual"), now))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/essay-note/<int:note_id>", methods=["DELETE"])
def delete_essay_note(note_id):
    db = get_db()
    db.execute("DELETE FROM essay_notes WHERE id=?", (note_id,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/share")
def share():
    db = get_db()
    mom = momentum_score(db)
    pillar_data = []
    for p in PILLARS:
        prog = pillar_progress(db, p["id"])
        metrics_list = []
        for m in METRICS[p["id"]]:
            cur = get_metric_val(db, f"{p['id']}.{m['id']}")
            metrics_list.append({**m, "current": cur, "pct": pct(cur, m["target"])})
        pillar_data.append({**p, "progress": prog, "metrics": metrics_list})
    return render_template("share.html", momentum=mom, pillars=pillar_data, generated=datetime.now().strftime("%B %d, %Y"))

@app.route("/api/nudges")
def api_nudges():
    db = get_db()
    return jsonify(generate_nudges(db))

# ── Init & Run ───────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
