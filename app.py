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

WEEKLY_TASK_LIBRARY = {
    "creativity": [
        {"id": "finish-song-block", "label": "Finish one real piece of your current song", "why": "Small finished pieces create momentum faster than waiting for a perfect full release.", "effects": []},
        {"id": "post-short-video", "label": "Post 2 short videos about your music", "why": "Short content is the fastest path to more listeners noticing your work.", "effects": []},
        {"id": "playlist-pitch", "label": "Pitch your song to 2 playlists or blogs", "why": "Distribution matters as much as creation if you want your audience to grow.", "effects": []},
        {"id": "book-performance", "label": "Lock in 1 live performance or open mic", "why": "Live reps build confidence and make your story more real.", "effects": [{"metric": "creativity.performances", "amount": 1}]},
        {"id": "enter-competition", "label": "Enter 1 music competition or showcase", "why": "Competitions add proof points to your portfolio.", "effects": [{"metric": "creativity.competitions", "amount": 1}]},
    ],
    "communication": [
        {"id": "case-outline", "label": "Write one strong section of your Y&G case or bill", "why": "Great speaking starts with clear thinking on paper.", "effects": []},
        {"id": "speech-practice", "label": "Practice one speech for 20 focused minutes", "why": "Frequent reps sharpen delivery faster than occasional long sessions.", "effects": []},
        {"id": "study-example", "label": "Study one winning debate or oratory example", "why": "Seeing strong structure makes it easier to improve your own.", "effects": []},
        {"id": "publish-oped", "label": "Publish or submit one op-ed or article", "why": "Published writing is concrete evidence of your voice and ideas.", "effects": [{"metric": "communication.opeds", "amount": 1}]},
        {"id": "give-speech", "label": "Give one speech, presentation, or argument round", "why": "Real speaking reps make confidence and results measurable.", "effects": [{"metric": "communication.speeches", "amount": 1}]},
    ],
    "leadership": [
        {"id": "mentor-student", "label": "Help one younger student this week", "why": "Leadership is strongest when someone else grows because of you.", "effects": [{"metric": "leadership.mentees", "amount": 1}]},
        {"id": "lead-session", "label": "Lead one practice, meeting, or planning session", "why": "Leading the room is a visible signal of trust and responsibility.", "effects": [{"metric": "leadership.team_meetings", "amount": 1}]},
        {"id": "event-step", "label": "Finish one planning step for an event", "why": "Organizing events turns ideas into visible outcomes.", "effects": []},
        {"id": "role-prep", "label": "Take one step toward a leadership title", "why": "Applications, outreach, and prep work create future openings.", "effects": []},
        {"id": "leadership-journal", "label": "Write a quick leadership reflection", "why": "Reflection helps you notice what style of leadership actually works.", "effects": []},
    ],
    "impact": [
        {"id": "play-gig", "label": "Play one gig, set, or community performance", "why": "Performing in public turns practice into impact and momentum.", "effects": [{"metric": "impact.gigs_played", "amount": 1}]},
        {"id": "community-outreach", "label": "Reach out to one community partner or family", "why": "Direct outreach keeps the mission connected to real people.", "effects": [{"metric": "impact.families_helped", "amount": 1}]},
        {"id": "collect-testimonial", "label": "Collect one testimonial or thank-you note", "why": "Specific testimonials make your impact easier to prove later.", "effects": [{"metric": "impact.testimonials", "amount": 1}]},
        {"id": "donate-instrument", "label": "Donate or place one instrument", "why": "This is a direct, memorable proof point for your mission.", "effects": [{"metric": "impact.instruments_donated", "amount": 1}]},
        {"id": "fundraising-push", "label": "Run one fundraising push or booking push", "why": "Consistent outreach is what eventually turns into revenue and reach.", "effects": []},
    ],
    "entrepreneurship": [
        {"id": "ship-feature", "label": "Ship one small app improvement", "why": "Shipping small updates keeps the app moving forward and usable.", "effects": []},
        {"id": "user-feedback", "label": "Get feedback from one real user", "why": "Real user feedback is more valuable than guessing alone.", "effects": [{"metric": "entrepreneurship.app_users", "amount": 1}]},
        {"id": "collect-app-testimonial", "label": "Collect one app testimonial", "why": "Testimonials make the app feel credible and help your story later.", "effects": [{"metric": "entrepreneurship.app_testimonials", "amount": 1}]},
        {"id": "competition-entry", "label": "Enter one app or startup competition", "why": "Competitions create external milestones for your project.", "effects": [{"metric": "entrepreneurship.comp_entries", "amount": 1}]},
        {"id": "record-progress", "label": "Capture one screenshot or demo of progress", "why": "A visible build trail makes growth easier to show over time.", "effects": []},
    ],
}

ESSAY_ANGLES = [
    {"id":"common","label":"Common App — Personal Essay","prompt":"The moment music became more than a hobby","pillars":["creativity","impact"]},
    {"id":"whylaw","label":"Why Pre-Law / PoliSci","prompt":"How advocacy taught you systems matter","pillars":["communication","leadership"]},
    {"id":"community","label":"Community Essay","prompt":"Instrument donations & access/equity","pillars":["impact","leadership"]},
    {"id":"challenge","label":"Challenge Essay","prompt":"Building from scratch as first-gen","pillars":["creativity","entrepreneurship"]},
    {"id":"curiosity","label":"Intellectual Curiosity","prompt":"Building the app — your problem → everyone's solution","pillars":["entrepreneurship","creativity"]},
]

PILLAR_LOOKUP = {p["id"]: p for p in PILLARS}
METRIC_LOOKUP = {
    f"{pid}.{m['id']}": {**m, "pillar": pid}
    for pid, metrics in METRICS.items()
    for m in metrics
}
TASK_LOOKUP = {
    f"{pid}.{task['id']}": {**task, "pillar": pid}
    for pid, tasks in WEEKLY_TASK_LIBRARY.items()
    for task in tasks
}

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
    CREATE TABLE IF NOT EXISTS weekly_plans (
        week_id TEXT PRIMARY KEY,
        generated_at TEXT NOT NULL,
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

def get_week_start(d=None):
    d = d or datetime.now()
    days_since_sunday = (d.weekday() + 1) % 7
    start = d - timedelta(days=days_since_sunday)
    return start.replace(hour=0, minute=0, second=0, microsecond=0)

def week_reset_label(d=None):
    start = get_week_start(d)
    return start.strftime("%b %d")

def get_metric_val(db, metric_id):
    r = db.execute("SELECT current_value FROM metrics WHERE id=?", (metric_id,)).fetchone()
    return r["current_value"] if r else 0

def metric_progress(db, metric_id):
    metric = METRIC_LOOKUP[metric_id]
    return pct(get_metric_val(db, metric_id), metric["target"])

def pct(cur, target):
    if target == 0: return 100
    return min(100, round((cur / target) * 100))

def recent_activity_score(db, pid, limit=3):
    logs = db.execute(
        "SELECT data FROM weekly_logs ORDER BY logged_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    total = done = 0
    for row in logs:
        data = json.loads(row["data"])
        for task in data.get("tasks", []):
            if task.get("pillar") != pid:
                continue
            if task.get("status") == "done":
                done += 1
            total += 1
    if total == 0:
        return None
    return round(done / total * 100)

def pillar_progress(db, pid):
    ms = METRICS.get(pid, [])
    if not ms: return 0
    metric_score = sum(pct(get_metric_val(db, f"{pid}.{m['id']}"), m["target"]) for m in ms) / len(ms)
    activity_score = recent_activity_score(db, pid)
    if activity_score is None:
        return round(metric_score)
    return round(metric_score * 0.85 + activity_score * 0.15)

def momentum_score(db):
    all_p = [pillar_progress(db, p["id"]) for p in PILLARS]
    return round(sum(all_p) / len(all_p)) if all_p else 0

def metric_gap_summary(db, pid):
    weakest = min(
        METRICS[pid],
        key=lambda m: pct(get_metric_val(db, f"{pid}.{m['id']}"), m["target"])
    )
    return weakest["label"]

def pillar_attention_score(db, pid):
    progress_gap = 100 - pillar_progress(db, pid)
    weak_metric_count = sum(
        1
        for metric in METRICS[pid]
        if pct(get_metric_val(db, f"{pid}.{metric['id']}"), metric["target"]) < 30
    )
    activity = recent_activity_score(db, pid)
    activity_gap = 35 if activity is None else (100 - activity)
    return round(progress_gap + weak_metric_count * 6 + activity_gap * 0.35, 2)

def focus_reason(db, pid):
    activity = recent_activity_score(db, pid)
    if activity is not None and activity < 45:
        return "Needs more weekly consistency"
    return f"Biggest gap right now: {metric_gap_summary(db, pid)}"

def rank_tasks_for_pillar(db, pid):
    ranked = []
    for idx, task in enumerate(WEEKLY_TASK_LIBRARY.get(pid, [])):
        score = 20 - idx
        for effect in task.get("effects", []):
            score += (100 - metric_progress(db, effect["metric"])) + (effect["amount"] * 4)
        ranked.append((score, {**task, "pillar": pid}))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [task for _, task in ranked]

def format_effect(effect):
    metric = METRIC_LOOKUP[effect["metric"]]
    amount = int(effect["amount"]) if float(effect["amount"]).is_integer() else effect["amount"]
    prefix = "+" if effect["amount"] > 0 else ""
    return f"{metric['label']} {prefix}{amount}"

def generate_weekly_plan(db, week_id):
    focus_pillars = sorted(PILLARS, key=lambda p: pillar_attention_score(db, p["id"]), reverse=True)[:3]
    task_slots = [2, 2, 1]
    tasks = []
    for pillar, slots in zip(focus_pillars, task_slots):
        ranked_tasks = rank_tasks_for_pillar(db, pillar["id"])[:slots]
        for task in ranked_tasks:
            task_id = f"{pillar['id']}.{task['id']}"
            tasks.append({
                "task_id": task_id,
                "pillar": pillar["id"],
                "pillar_label": pillar["label"],
                "pillar_icon": pillar["icon"],
                "pillar_color": pillar["color"],
                "label": task["label"],
                "why": task["why"],
                "effects": task.get("effects", []),
                "effect_text": ", ".join(format_effect(effect) for effect in task.get("effects", [])),
            })
    return {
        "week_id": week_id,
        "week_starts": get_week_start().date().isoformat(),
        "generated_at": datetime.now().isoformat(),
        "reset_day": "Sunday morning",
        "focus_pillars": [
            {
                "id": pillar["id"],
                "label": pillar["label"],
                "icon": pillar["icon"],
                "color": pillar["color"],
                "reason": focus_reason(db, pillar["id"]),
            }
            for pillar in focus_pillars
        ],
        "tasks": tasks,
    }

def get_or_create_weekly_plan(db, week_id=None):
    week_id = week_id or get_week_id()
    row = db.execute("SELECT data FROM weekly_plans WHERE week_id=?", (week_id,)).fetchone()
    if row:
        return json.loads(row["data"])
    plan = generate_weekly_plan(db, week_id)
    db.execute(
        "INSERT INTO weekly_plans (week_id, generated_at, data) VALUES (?,?,?)",
        (week_id, plan["generated_at"], json.dumps(plan))
    )
    db.commit()
    return plan

def task_match_key(task):
    return task.get("task_id") or f"{task.get('pillar')}::{task.get('label')}"

def merge_status(plan_task, saved_tasks):
    status = "pending"
    note = ""
    for task in saved_tasks:
        if task.get("task_id") == plan_task.get("task_id") or (
            task.get("pillar") == plan_task.get("pillar") and task.get("label") == plan_task.get("label")
        ):
            status = task.get("status", "pending")
            note = task.get("note", "")
            break
    return {
        **plan_task,
        "status": status,
        "note": note,
    }

def load_custom_tasks(db, saved_tasks):
    custom_rows = db.execute(
        "SELECT id, pillar, label FROM custom_tasks WHERE active=1 ORDER BY id DESC"
    ).fetchall()
    items = []
    for row in custom_rows:
        task = {
            "task_id": f"custom.{row['id']}",
            "pillar": row["pillar"],
            "pillar_label": PILLAR_LOOKUP[row["pillar"]]["label"],
            "pillar_icon": PILLAR_LOOKUP[row["pillar"]]["icon"],
            "pillar_color": PILLAR_LOOKUP[row["pillar"]]["color"],
            "label": row["label"],
            "why": "A custom task you added for this pillar.",
            "effects": [],
            "effect_text": "",
            "custom": True,
        }
        items.append(merge_status(task, saved_tasks))
    return items

def apply_metric_delta(db, metric_id, delta, recorded_at):
    if not delta:
        return
    current = get_metric_val(db, metric_id)
    new_value = max(0, current + delta)
    db.execute(
        "UPDATE metrics SET current_value=?, updated_at=? WHERE id=?",
        (new_value, recorded_at, metric_id)
    )
    db.execute(
        "INSERT INTO metric_history (metric_id, value, recorded_at) VALUES (?,?,?)",
        (metric_id, new_value, recorded_at)
    )

def apply_task_effects(db, week_id, old_tasks, new_tasks, recorded_at):
    plan = get_or_create_weekly_plan(db, week_id)
    plan_tasks = {task["task_id"]: task for task in plan.get("tasks", [])}
    old_map = {task_match_key(task): task for task in old_tasks}
    new_map = {task_match_key(task): task for task in new_tasks}
    all_keys = set(old_map) | set(new_map)
    for key in all_keys:
        prev_done = old_map.get(key, {}).get("status") == "done"
        new_done = new_map.get(key, {}).get("status") == "done"
        if prev_done == new_done:
            continue
        task = plan_tasks.get(new_map.get(key, {}).get("task_id")) or plan_tasks.get(old_map.get(key, {}).get("task_id"))
        if not task:
            continue
        direction = 1 if new_done else -1
        for effect in task.get("effects", []):
            apply_metric_delta(db, effect["metric"], effect["amount"] * direction, recorded_at)

def maybe_add_essay_notes(db, tasks, recorded_at):
    for task in tasks:
        if task.get("status") != "done" or not task.get("note"):
            continue
        pillar = task.get("pillar", "")
        relevant = [angle for angle in ESSAY_ANGLES if pillar in angle.get("pillars", [])]
        for angle in relevant:
            exists = db.execute(
                "SELECT 1 FROM essay_notes WHERE angle_id=? AND pillar=? AND note=? AND source_task=?",
                (angle["id"], pillar, task["note"], task.get("label", ""))
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO essay_notes (angle_id, pillar, note, source_task, created_at) VALUES (?,?,?,?,?)",
                    (angle["id"], pillar, task["note"], task.get("label", ""), recorded_at)
                )

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
    weekly_plan = get_or_create_weekly_plan(db)
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
        cur_week=cur_week, has_log=bool(has_log), essays=ESSAY_ANGLES,
        weekly_plan=weekly_plan, reset_label=week_reset_label())

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
    weekly_plan = get_or_create_weekly_plan(db, cur_week)
    existing = db.execute("SELECT data FROM weekly_logs WHERE week_id=?", (cur_week,)).fetchone()
    existing_data = json.loads(existing["data"]) if existing else None
    saved_tasks = existing_data.get("tasks", []) if existing_data else []
    focus_tasks = [merge_status(task, saved_tasks) for task in weekly_plan.get("tasks", [])]
    custom_tasks = load_custom_tasks(db, saved_tasks)
    past_logs = db.execute("SELECT week_id, data FROM weekly_logs ORDER BY logged_at DESC LIMIT 8").fetchall()
    past = []
    for l in past_logs:
        d = json.loads(l["data"])
        done = sum(1 for t in d.get("tasks",[]) if t.get("status")=="done")
        total = len(d.get("tasks",[]))
        past.append({"week": l["week_id"], "done": done, "total": total, "reflection": d.get("reflection","")})
    return render_template(
        "weekly.html",
        cur_week=cur_week,
        has_existing=bool(existing_data),
        past_logs=past,
        weekly_plan=weekly_plan,
        focus_tasks=focus_tasks,
        custom_tasks=custom_tasks,
        reset_label=week_reset_label(),
        reflection=(existing_data or {}).get("reflection", "")
    )

@app.route("/api/weekly", methods=["POST"])
def save_weekly():
    db = get_db()
    data = request.json
    wid = get_week_id()
    now = datetime.now().isoformat()
    existing = db.execute("SELECT data FROM weekly_logs WHERE week_id=?", (wid,)).fetchone()
    old_data = json.loads(existing["data"]) if existing else {"tasks": [], "reflection": ""}
    apply_task_effects(db, wid, old_data.get("tasks", []), data.get("tasks", []), now)
    payload = json.dumps(data)
    if existing:
        db.execute("UPDATE weekly_logs SET data=?, logged_at=? WHERE week_id=?", (payload, now, wid))
    else:
        db.execute("INSERT INTO weekly_logs (week_id, logged_at, data) VALUES (?,?,?)", (wid, now, payload))
    maybe_add_essay_notes(db, data.get("tasks", []), now)
    db.commit()
    return jsonify({"ok": True, "updated_week": wid})

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
