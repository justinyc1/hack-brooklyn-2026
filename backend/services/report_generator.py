from __future__ import annotations

from models.feedback import FeedbackReport
from models.interview_session import InterviewSession


def generate_feedback_html(report: FeedbackReport, session: InterviewSession | None) -> str:
    """Return a self-contained HTML feedback report. No side effects."""
    overall = round(report.overall_score * 10)
    score_color = _score_color(overall)
    date_str = report.generated_at.strftime("%B %d, %Y")

    session_parts: list[str] = []
    if session:
        if session.role:
            session_parts.append(_esc(session.role))
        if session.company:
            session_parts.append(f"at {_esc(session.company)}")
        session_parts.append(f"{session.mode.value.title()} Interview")
    session_info = " &middot; ".join(session_parts) if session_parts else "Interview"

    cat_rows = _category_rows(report)
    strengths_li = "".join(f"<li>&#10003; {_esc(s)}</li>" for s in report.top_strengths)
    weaknesses_li = "".join(f"<li>&#9651; {_esc(w)}</li>" for w in report.top_weaknesses)
    questions_html = _questions_html(report)
    drills_li = "".join(f"<li>{_esc(d)}</li>" for d in report.targeted_drills)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Interview Feedback &mdash; Intervue</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8f6f2;color:#1a1a1a;line-height:1.5}}
.container{{max-width:800px;margin:0 auto;padding:40px 24px}}
.brand{{font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:#888;margin-bottom:8px}}
h1{{font-size:36px;font-weight:700;color:#111}}
.meta{{font-size:13px;color:#777;margin-top:6px}}
.card{{background:#fff;border-radius:8px;border:1px solid #e4e0db;padding:28px;margin-bottom:20px}}
.section-label{{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#999;margin-bottom:16px}}
.overall-row{{display:flex;align-items:flex-start;gap:40px;flex-wrap:wrap}}
.score-big{{font-size:72px;font-weight:700;line-height:1}}
.score-denom{{font-size:13px;color:#999;margin-top:4px}}
.cat-grid{{flex:1;min-width:240px;display:flex;flex-direction:column;gap:10px;justify-content:center}}
.cat-item{{display:flex;align-items:center;gap:8px}}
.cat-label{{font-size:12px;color:#555;width:130px;flex-shrink:0}}
.cat-bar-wrap{{flex:1;height:4px;background:#eee;border-radius:2px}}
.cat-bar{{height:4px;border-radius:2px}}
.cat-score{{font-size:12px;font-weight:600;width:28px;text-align:right}}
.sw-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.sw-col ul{{list-style:none;padding:0}}
.sw-col li{{font-size:13px;color:#444;padding:4px 0}}
.strengths-header{{color:#4a7c3f}}
.improve-header{{color:#c0392b}}
.q-card{{border:1px solid #e4e0db;border-radius:6px;padding:18px;margin-bottom:12px}}
.q-header{{display:flex;align-items:flex-start;gap:12px;margin-bottom:14px}}
.q-num{{font-size:11px;font-family:monospace;color:#aaa;padding-top:2px;white-space:nowrap}}
.q-text{{flex:1;font-size:14px;font-weight:500;color:#111}}
.q-score{{font-size:16px;font-weight:700;flex-shrink:0}}
.q-cols{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.q-cols ul{{list-style:none;padding:0}}
.q-cols li{{font-size:12px;color:#555;padding:3px 0}}
.col-label{{font-size:10px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}}
.strengths-col .col-label{{color:#4a7c3f}}
.improve-col .col-label{{color:#c0392b}}
.better-ans{{margin-top:12px;padding:10px 14px;background:#f8f6f2;border-left:3px solid #ccc;font-size:12px;color:#666;font-style:italic}}
.drills-list{{list-style:none;padding:0}}
.drills-list li{{font-size:13px;color:#444;padding:7px 0;border-bottom:1px solid #f0ede9}}
.drills-list li:last-child{{border-bottom:none}}
.footer{{margin-top:48px;padding-top:20px;border-top:1px solid #e4e0db;text-align:center;font-size:11px;color:#bbb}}
@media(max-width:600px){{.sw-grid,.q-cols{{grid-template-columns:1fr}}.overall-row{{flex-direction:column}}.score-big{{font-size:56px}}}}
</style>
</head>
<body>
<div class="container">
  <div style="margin-bottom:40px">
    <p class="brand">Intervue</p>
    <h1>Interview Feedback</h1>
    <p class="meta">{session_info} &middot; {date_str}</p>
  </div>

  <div class="card">
    <p class="section-label">Overall Score</p>
    <div class="overall-row">
      <div>
        <div class="score-big" style="color:{score_color}">{overall}</div>
        <div class="score-denom">/ 100</div>
      </div>
      <div class="cat-grid">
        {cat_rows}
      </div>
    </div>
  </div>

  <div class="card">
    <p class="section-label">Summary</p>
    <div class="sw-grid">
      <div class="sw-col">
        <p class="section-label strengths-header">Top Strengths</p>
        <ul>{strengths_li}</ul>
      </div>
      <div class="sw-col">
        <p class="section-label improve-header">Areas to Improve</p>
        <ul>{weaknesses_li}</ul>
      </div>
    </div>
  </div>

  {f'<div class="card"><p class="section-label">Question Breakdown</p>{questions_html}</div>' if questions_html else ''}

  {f'<div class="card drills"><p class="section-label">Targeted Drills</p><ul class="drills-list">{drills_li}</ul></div>' if drills_li else ''}

  <div class="footer">
    Generated by <strong>Intervue</strong> &mdash; intervue.org
  </div>
</div>
</body>
</html>"""


def _score_color(score: int) -> str:
    if score >= 75:
        return "#4a7c3f"
    if score >= 55:
        return "#c85a1e"
    return "#c0392b"


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def _category_rows(report: FeedbackReport) -> str:
    _labels = {
        "clarity": "Clarity", "confidence": "Confidence", "conciseness": "Conciseness",
        "structure": "Structure", "specificity": "Specificity", "pace": "Pace",
        "problem_solving": "Problem Solving", "code_correctness": "Correctness",
        "optimization_awareness": "Optimization", "star_structure": "STAR",
        "impact_articulation": "Impact", "ownership": "Ownership",
    }
    rows = ""
    for key, val in report.category_scores.model_dump().items():
        if not isinstance(val, (int, float)):
            continue
        label = _labels.get(key, key.replace("_", " ").title())
        score_val = round(val * 10)
        color = _score_color(score_val)
        pct = min(100, val * 10)
        rows += (
            f'<div class="cat-item">'
            f'<span class="cat-label">{label}</span>'
            f'<div class="cat-bar-wrap"><div class="cat-bar" style="width:{pct}%;background:{color}"></div></div>'
            f'<span class="cat-score" style="color:{color}">{score_val}</span>'
            f'</div>'
        )
    return rows


def _questions_html(report: FeedbackReport) -> str:
    html = ""
    for i, qf in enumerate(report.per_question_feedback):
        score = round(qf.score * 10)
        color = _score_color(score)
        q_text = _esc(qf.question_text or f"Question {i + 1}")
        strengths_li = "".join(f"<li>+ {_esc(s)}</li>" for s in qf.strengths)
        improve_li = "".join(f"<li>&#9651; {_esc(imp)}</li>" for imp in qf.improvements)
        better = (
            f'<div class="better-ans">&ldquo;{_esc(qf.better_answer_example)}&rdquo;</div>'
            if qf.better_answer_example else ""
        )
        html += f"""
        <div class="q-card">
          <div class="q-header">
            <span class="q-num">Q{str(i + 1).zfill(2)}</span>
            <span class="q-text">{q_text}</span>
            <span class="q-score" style="color:{color}">{score}</span>
          </div>
          <div class="q-cols">
            <div class="strengths-col"><p class="col-label">Strengths</p><ul>{strengths_li}</ul></div>
            <div class="improve-col"><p class="col-label">Improve</p><ul>{improve_li}</ul></div>
          </div>
          {better}
        </div>"""
    return html
