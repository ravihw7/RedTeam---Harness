"""
Flask dashboard for the red-team/eval harness.

Run with: python web/app.py
Then open http://127.0.0.1:5000
"""

import os
import sys

# Allow running this file directly (python web/app.py) by adding the
# project root to the path so `harness` is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict

from flask import Flask, abort, render_template
from dotenv import load_dotenv

from harness.db import get_session, init_db
from harness.models import Run, Result, TestCase, Category

load_dotenv()

app = Flask(__name__)


def _run_summary(run: Run):
    total = len(run.results)
    passed = sum(1 for r in run.results if r.passed)
    pass_rate = round(100 * passed / total, 1) if total else 0.0
    return {"run": run, "total": total, "passed": passed, "pass_rate": pass_rate}


@app.route("/")
def dashboard():
    init_db()
    session = get_session()
    runs = session.query(Run).order_by(Run.started_at.desc()).all()
    summaries = [_run_summary(r) for r in runs]
    session.close()
    return render_template("dashboard.html", summaries=summaries)


@app.route("/run/<int:run_id>")
def run_detail(run_id):
    init_db()
    session = get_session()
    run = session.query(Run).filter_by(id=run_id).first()
    if not run:
        session.close()
        abort(404)

    by_category = defaultdict(list)
    for result in run.results:
        by_category[result.test_case.category.name].append(result)

    category_stats = []
    for cat_name, results in sorted(by_category.items()):
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        category_stats.append(
            {
                "name": cat_name,
                "total": total,
                "passed": passed,
                "pass_rate": round(100 * passed / total, 1) if total else 0.0,
                "results": sorted(results, key=lambda r: r.passed),  # fails first
            }
        )

    summary = _run_summary(run)
    session.close()
    return render_template("run_detail.html", run=run, summary=summary, categories=category_stats)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
