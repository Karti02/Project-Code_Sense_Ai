"""
Optional helper for a college viva/demo: creates a demo user with
~21 days of realistic-looking activity data, so the dashboard, charts,
and ML page have something to show immediately (instead of waiting to
collect real usage first).

Run with:
    python seed_demo_data.py

Login afterwards with:
    username: demo
    password: demo1234
"""

import random
from datetime import date, timedelta, datetime

from app import create_app
from app.extensions import db
from app.models import User, DailyStat, LanguageUsage, CodingSession
from app.utils.helpers import compute_heuristic_score

LANGUAGES = ["Python", "JavaScript", "C++", "HTML", "CSS", "SQL", "Java"]
APPS = ["VS Code", "PyCharm", "Terminal", "Cursor IDE"]
PROJECTS = ["CodeSenseAI", "college-ml-lab", "portfolio-site", "dsa-practice"]

app = create_app("development")

with app.app_context():
    user = User.query.filter_by(username="demo").first()
    if user is None:
        user = User(username="demo", email="demo@codesense.ai", full_name="Demo Student")
        user.set_password("demo1234")
        db.session.add(user)
        db.session.commit()
        print("Created demo user (username: demo / password: demo1234)")
    else:
        print("Demo user already exists, adding/refreshing sample data...")

    random.seed(7)
    today = date.today()

    for i in range(20, -1, -1):
        day = today - timedelta(days=i)

        coding_seconds = random.randint(1200, 5 * 3600)
        keyboard_count = random.randint(500, 9000)
        mouse_clicks = random.randint(100, 1500)
        compile_count = random.randint(2, 25)
        project_switches = random.randint(0, 8)
        idle_seconds = random.randint(60, 1800)
        sessions_count = random.randint(1, 5)
        n_langs_today = random.randint(1, 3)
        langs_today = random.sample(LANGUAGES, n_langs_today)

        score = compute_heuristic_score(
            coding_seconds, compile_count, keyboard_count, project_switches, idle_seconds
        )

        stat = DailyStat.query.filter_by(user_id=user.id, date=day).first()
        if stat is None:
            stat = DailyStat(user_id=user.id, date=day)
            db.session.add(stat)

        stat.coding_time_seconds = coding_seconds
        stat.keyboard_count = keyboard_count
        stat.mouse_clicks = mouse_clicks
        stat.compile_count = compile_count
        stat.project_switches = project_switches
        stat.idle_seconds = idle_seconds
        stat.languages_used = n_langs_today
        stat.sessions_count = sessions_count
        stat.productivity_score = score

        remaining = coding_seconds
        for idx, lang in enumerate(langs_today):
            share = remaining if idx == len(langs_today) - 1 else int(remaining * random.uniform(0.2, 0.6))
            remaining -= share
            row = LanguageUsage.query.filter_by(user_id=user.id, language=lang, date=day).first()
            if row is None:
                row = LanguageUsage(user_id=user.id, language=lang, date=day, seconds_spent=0)
                db.session.add(row)
            row.seconds_spent = max(row.seconds_spent, share)

        for _ in range(sessions_count):
            lang = random.choice(langs_today)
            start = datetime(day.year, day.month, day.day, random.randint(9, 21), random.randint(0, 59))
            duration = random.randint(300, 5400)
            session = CodingSession(
                user_id=user.id,
                app_name=random.choice(APPS),
                project_name=random.choice(PROJECTS),
                file_name=f"main.{ {'Python':'py','JavaScript':'js','C++':'cpp','HTML':'html','CSS':'css','SQL':'sql','Java':'java'}[lang] }",
                language=lang,
                start_time=start,
                end_time=start + timedelta(seconds=duration),
                duration_seconds=duration,
                idle_seconds=random.randint(0, 300),
                keyboard_count=random.randint(50, 2000),
                mouse_clicks=random.randint(10, 400),
                compile_count=random.randint(0, 6),
                is_active=False,
            )
            db.session.add(session)

    user.current_streak = 5
    user.longest_streak = 12
    user.last_active_date = today

    db.session.commit()
    print(f"Seeded {21} days of demo activity for user '{user.username}'.")
