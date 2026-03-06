"""
views.py — CreditSense Dashboard HTML Generator.
Generates a complete static HTML dashboard from a CreditSense report,
using Chart.js for visualizations and a dark-themed UI inspired by
financial analytics dashboards.
"""

import json
from typing import Dict, List, Optional


# ── Colour palette ──────────────────────────────────────────────
TIER_COLORS = {
    "excellent": "#22c55e", "very_good": "#3b82f6",
    "good": "#a855f7", "fair": "#f97316", "poor": "#ef4444",
}
ACCOUNT_COLORS = [
    "#22c55e", "#3b82f6", "#a855f7", "#f97316", "#eab308",
    "#ef4444", "#06b6d4", "#ec4899", "#8b5cf6", "#14b8a6",
]
PRIORITY_COLORS = {"High": "#ef4444", "Medium": "#f97316", "Low": "#22c55e"}


# ── 1. Credit Score Gauge ───────────────────────────────────────
def score_gauge_html(score: int, tier: str, risk_level: str, score_model: str) -> str:
    """Renders a semi-circular credit score gauge with Chart.js doughnut."""
    tier_color = TIER_COLORS.get(tier, "#9ca3af")
    pct = max(0, min(100, round((score - 300) / 550 * 100)))  # 300-850 → 0-100

    inner = f"""<!DOCTYPE html><html><head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>body{{margin:0;padding:0;background:#0f0f13;display:flex;justify-content:center;align-items:center;height:320px;}}
    .wrap{{position:relative;width:280px;height:180px;}}
    .center{{position:absolute;top:58%;left:50%;transform:translate(-50%,-50%);text-align:center;font-family:Georgia,serif;}}
    .score{{font-size:3rem;font-weight:700;color:{tier_color};}}
    .label{{font-size:.85rem;color:#9ca3af;margin-top:2px;}}
    .model{{font-size:.7rem;color:#6b7280;margin-top:4px;}}
    </style></head><body>
    <div class="wrap">
      <canvas id="gauge"></canvas>
      <div class="center">
        <div class="score">{score}</div>
        <div class="label">{risk_level}</div>
        <div class="model">{score_model}</div>
      </div>
    </div>
    <script>
    new Chart(document.getElementById('gauge'),{{
      type:'doughnut',
      data:{{datasets:[{{data:[{pct},{100-pct}],
        backgroundColor:['{tier_color}','#1f2937'],borderWidth:0}}]}},
      options:{{rotation:-90,circumference:180,cutout:'78%',
        plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}},
        responsive:true,maintainAspectRatio:false}}
    }});
    </script></body></html>"""

    return _iframe(inner, height=340)


# ── 2. Scorecard (KPI Cards) ───────────────────────────────────
def scorecard_html(report: Dict) -> str:
    """Renders key credit metrics as styled cards."""
    overview = report.get("account_overview", {})
    consumer = report.get("consumer", {})
    meta = report.get("metadata", {})
    tier = meta.get("credit_tier", "unknown")
    tier_color = TIER_COLORS.get(tier, "#9ca3af")
    tier_label = tier.replace("_", " ").title()

    utilization = overview.get("overall_utilization", 0)
    util_color = "#22c55e" if utilization < 30 else "#f97316" if utilization < 50 else "#ef4444"

    on_time = overview.get("on_time_payment_percentage", 0)
    on_time_color = "#22c55e" if on_time >= 97 else "#f97316" if on_time >= 90 else "#ef4444"

    cards = [
        ("🏆 Credit Score", str(consumer.get("credit_score", "N/A")), tier_color),
        ("📊 Credit Tier", tier_label, tier_color),
        ("💳 Total Accounts", f"{overview.get('open_accounts', 0)} open / {overview.get('closed_accounts', 0)} closed", "#3b82f6"),
        ("📈 Utilization", f"{utilization:.1f}%", util_color),
        ("💰 Total Balance", f"${overview.get('total_balance', 0):,.0f}", "#a855f7"),
        ("🏦 Credit Limit", f"${overview.get('total_credit_limit', 0):,.0f}", "#06b6d4"),
        ("✅ On-Time Payments", f"{on_time}%", on_time_color),
        ("🔍 Hard Inquiries", str(overview.get("hard_inquiries", 0)), "#f97316"),
    ]

    cards_html = "".join(f"""
      <div style="background:#1a1a2e;border:1px solid #2d2d4a;border-radius:12px;padding:18px 22px;min-width:160px;flex:1;">
        <div style="color:#9ca3af;font-size:.78rem;margin-bottom:6px;">{c[0]}</div>
        <div style="color:{c[2]};font-size:1.35rem;font-weight:700;font-family:'Georgia',serif;">{c[1]}</div>
      </div>
    """ for c in cards)

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;letter-spacing:.03em;">🏆 Credit Report Scorecard</h2>
      <div style="display:flex;flex-wrap:wrap;gap:12px;">{cards_html}</div>
    </div>
    """


# ── 3. Utilization Bar Chart (per account) ─────────────────────
def utilization_chart_html(report: Dict) -> str:
    """Renders a horizontal bar chart of utilization per account + overall."""
    structured = report.get("_structured_data", {})
    accounts = structured.get("accounts", [])

    labels = []
    utilizations = []
    balances = []
    limits = []

    for acc in accounts:
        limit = acc.get("credit_limit") or 0
        balance = acc.get("current_balance") or 0
        if limit > 0:
            util = round(balance / limit * 100, 1)
            labels.append(acc.get("account_name", "Unknown")[:25])
            utilizations.append(util)
            balances.append(balance)
            limits.append(limit)

    # Add overall
    overview = report.get("account_overview", {})
    labels.append("OVERALL")
    utilizations.append(round(overview.get("overall_utilization", 0), 1))
    balances.append(overview.get("total_balance", 0))
    limits.append(overview.get("total_credit_limit", 0))

    bar_colors = [
        "'#22c55e'" if u < 30 else "'#f97316'" if u < 50 else "'#ef4444'"
        for u in utilizations
    ]

    inner = f"""<!DOCTYPE html><html><head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>body{{margin:0;padding:20px;background:#0f0f13;font-family:Georgia,serif;color:#e5e7eb;}}</style>
    </head><body>
    <canvas id="util"></canvas>
    <script>
    var bals={json.dumps(balances)};
    var lims={json.dumps(limits)};
    new Chart(document.getElementById('util'),{{
      type:'bar',
      data:{{labels:{json.dumps(labels)},datasets:[{{
        label:'Utilization %',data:{json.dumps(utilizations)},
        backgroundColor:[{','.join(bar_colors)}],borderRadius:6,borderSkipped:false
      }}]}},
      options:{{indexAxis:'y',responsive:true,
        plugins:{{legend:{{display:false}},
          tooltip:{{callbacks:{{label:function(c){{
            var i=c.dataIndex;return c.parsed.x+'% — $'+bals[i].toLocaleString()+' / $'+lims[i].toLocaleString()
          }}}}}}}},
        scales:{{
          x:{{max:100,ticks:{{color:'#d1d5db',callback:function(v){{return v+'%'}}}},grid:{{color:'#1f2937'}}}},
          y:{{ticks:{{color:'#d1d5db'}},grid:{{color:'#1f2937'}}}}
        }}
      }}
    }});
    </script></body></html>"""

    chart_height = max(300, len(labels) * 55 + 80)
    return _section("📊 Credit Utilization by Account", _iframe(inner, height=chart_height))


# ── 4. Key Factors Chart ───────────────────────────────────────
def key_factors_html(report: Dict) -> str:
    """Renders the key factors affecting the score as styled pills."""
    factors = report.get("consumer", {}).get("key_factors", [])
    if not factors:
        return ""

    pills = ""
    icons = ["⚠️", "📉", "⏳", "🔍", "📋"]
    for i, factor in enumerate(factors):
        icon = icons[i % len(icons)]
        pills += f"""
        <div style="background:#1a1a2e;border:1px solid #2d2d4a;border-radius:10px;padding:14px 18px;
                     display:flex;align-items:flex-start;gap:10px;">
          <span style="font-size:1.2rem;">{icon}</span>
          <span style="color:#d1d5db;font-size:.88rem;line-height:1.4;">{factor}</span>
        </div>
        """

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">⚠️ Key Factors Affecting Your Score</h2>
      <div style="display:flex;flex-direction:column;gap:10px;">{pills}</div>
    </div>
    """


# ── 5. Summary Section ─────────────────────────────────────────
def summary_html(report: Dict) -> str:
    """Renders the credit health summary with markdown-like formatting."""
    summary = report.get("summary", "")
    if not summary:
        return ""

    # Simple markdown → HTML conversion
    import re
    html = summary
    html = re.sub(r'^## (.+)$', r'<h3 style="color:#a5b4fc;font-size:1.05rem;margin:20px 0 10px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#e5e7eb;">\1</strong>', html)
    html = re.sub(r'^• (.+)$', r'<div style="padding:4px 0 4px 16px;color:#d1d5db;font-size:.9rem;">• \1</div>', html, flags=re.MULTILINE)
    html = re.sub(r'^\u2022 (.+)$', r'<div style="padding:4px 0 4px 16px;color:#d1d5db;font-size:.9rem;">• \1</div>', html, flags=re.MULTILINE)
    html = html.replace("\n\n", "<br>")

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">📝 Credit Health Summary</h2>
      <div style="line-height:1.6;font-size:.92rem;color:#d1d5db;">{html}</div>
    </div>
    """


# ── 6. Recommendations Section ─────────────────────────────────
def recommendations_html(report: Dict) -> str:
    """Renders prioritized recommendations as styled cards."""
    recs = report.get("recommendations", [])
    if not recs:
        return ""

    cards = ""
    for i, rec in enumerate(recs, 1):
        priority = rec.get("priority", "Medium")
        p_color = PRIORITY_COLORS.get(priority, "#9ca3af")

        cards += f"""
        <div style="background:#1a1a2e;border:1px solid #2d2d4a;border-radius:12px;padding:20px;margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <span style="color:#f8fafc;font-size:1rem;font-weight:700;">#{i}</span>
            <span style="background:{p_color}22;color:{p_color};border-radius:6px;padding:3px 10px;font-size:.75rem;font-weight:600;">{priority} Priority</span>
          </div>
          <div style="color:#e5e7eb;font-size:.92rem;font-weight:600;margin-bottom:10px;line-height:1.4;">{rec.get('action','')}</div>
          <div style="color:#9ca3af;font-size:.84rem;margin-bottom:8px;line-height:1.4;">💡 {rec.get('reason','')}</div>
          <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <span style="color:#22c55e;font-size:.82rem;">📈 Impact: {rec.get('expected_impact','')}</span>
            <span style="color:#3b82f6;font-size:.82rem;">⏱ {rec.get('timeframe','')}</span>
          </div>
        </div>
        """

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">🎯 Personalized Recommendations</h2>
      {cards}
    </div>
    """


# ── 7. Accounts Table ──────────────────────────────────────────
def accounts_table_html(report: Dict) -> str:
    """Renders a detailed table of all credit accounts."""
    structured = report.get("_structured_data", {})
    accounts = structured.get("accounts", [])
    if not accounts:
        return ""

    rows = ""
    for i, acc in enumerate(accounts):
        status = acc.get("account_status", "")
        status_color = "#22c55e" if "open" in status.lower() or "current" in status.lower() else "#6b7280"
        payment = acc.get("payment_status", "")
        pay_color = "#22c55e" if "current" in payment.lower() else "#ef4444"

        limit = acc.get("credit_limit") or 0
        balance = acc.get("current_balance") or 0
        util = round(balance / limit * 100, 1) if limit > 0 else 0
        util_color = "#22c55e" if util < 30 else "#f97316" if util < 50 else "#ef4444"

        rows += f"""
        <tr style="border-bottom:1px solid #1f2937;">
          <td style="padding:10px;font-size:.88rem;color:#e5e7eb;font-weight:600;">{acc.get('account_name','')}</td>
          <td style="padding:10px;font-size:.82rem;color:#9ca3af;">{acc.get('account_type','')}</td>
          <td style="padding:10px;">
            <span style="background:{status_color}22;color:{status_color};border-radius:4px;padding:2px 8px;font-size:.78rem;">{status}</span>
          </td>
          <td style="padding:10px;">
            <span style="background:{pay_color}22;color:{pay_color};border-radius:4px;padding:2px 8px;font-size:.78rem;">{payment}</span>
          </td>
          <td style="padding:10px;text-align:right;color:#e5e7eb;font-size:.88rem;">${balance:,.0f}</td>
          <td style="padding:10px;text-align:right;color:#9ca3af;font-size:.88rem;">{"$"+f"{limit:,.0f}" if limit else "N/A"}</td>
          <td style="padding:10px;text-align:right;">
            <span style="color:{util_color};font-weight:600;font-size:.88rem;">{util}%</span>
          </td>
          <td style="padding:10px;text-align:right;color:#9ca3af;font-size:.82rem;">{acc.get('date_opened','N/A')}</td>
        </tr>
        """

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;overflow-x:auto;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">💳 Account Details ({len(accounts)} accounts)</h2>
      <table style="width:100%;border-collapse:collapse;font-size:.88rem;">
        <thead>
          <tr style="border-bottom:2px solid #374151;">
            <th style="padding:10px;text-align:left;color:#6b7280;font-weight:500;">Account</th>
            <th style="padding:10px;text-align:left;color:#6b7280;font-weight:500;">Type</th>
            <th style="padding:10px;text-align:left;color:#6b7280;font-weight:500;">Status</th>
            <th style="padding:10px;text-align:left;color:#6b7280;font-weight:500;">Payment</th>
            <th style="padding:10px;text-align:right;color:#6b7280;font-weight:500;">Balance</th>
            <th style="padding:10px;text-align:right;color:#6b7280;font-weight:500;">Limit</th>
            <th style="padding:10px;text-align:right;color:#6b7280;font-weight:500;">Util.</th>
            <th style="padding:10px;text-align:right;color:#6b7280;font-weight:500;">Opened</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


# ── 8. Inquiries Table ─────────────────────────────────────────
def inquiries_table_html(report: Dict) -> str:
    """Renders a table of hard credit inquiries."""
    structured = report.get("_structured_data", {})
    inquiries = structured.get("inquiries", [])
    if not inquiries:
        return ""

    rows = ""
    for inq in inquiries:
        rows += f"""
        <tr style="border-bottom:1px solid #1f2937;">
          <td style="padding:8px 10px;color:#9ca3af;font-size:.85rem;">{inq.get('date','')}</td>
          <td style="padding:8px 10px;color:#e5e7eb;font-size:.88rem;">{inq.get('creditor','')}</td>
          <td style="padding:8px 10px;">
            <span style="background:#f9731622;color:#f97316;border-radius:4px;padding:2px 8px;font-size:.78rem;">{inq.get('inquiry_type','')}</span>
          </td>
        </tr>
        """

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">🔍 Hard Inquiries ({len(inquiries)})</h2>
      <table style="width:100%;border-collapse:collapse;font-size:.88rem;">
        <thead>
          <tr style="border-bottom:2px solid #374151;">
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Date</th>
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Creditor</th>
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Type</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


# ── 9. Disclaimer ──────────────────────────────────────────────
def disclaimer_html(report: Dict) -> str:
    """Renders the financial disclaimer."""
    text = report.get("disclaimer", "")
    if not text:
        return ""

    return f"""
    <div style="font-family:'Georgia',serif;background:#1a1a2e;padding:16px 20px;border-radius:12px;
                border:1px solid #2d2d4a;color:#6b7280;font-size:.78rem;line-height:1.5;">
      ⚖️ {text}
    </div>
    """


# ── Full Dashboard Builder ──────────────────────────────────────
def build_dashboard_html(report: Dict, structured_data: Optional[Dict] = None) -> str:
    """
    Build a complete standalone HTML dashboard from a CreditSense report.

    Args:
        report: The final_report dict from the pipeline.
        structured_data: Optional structured_data dict (for account details).

    Returns:
        Complete HTML string ready to write to a file.
    """
    if structured_data:
        report["_structured_data"] = structured_data

    consumer = report.get("consumer", {})
    meta = report.get("metadata", {})
    name = consumer.get("name", "Consumer")
    bureau = meta.get("bureau", "Unknown").title()
    report_date = meta.get("report_date", "")
    generated = report.get("generated_at", "")

    sections = [
        scorecard_html(report),
        score_gauge_html(
            consumer.get("credit_score", 0),
            meta.get("credit_tier", "unknown"),
            consumer.get("risk_level", "Unknown"),
            consumer.get("score_model", "FICO"),
        ),
        key_factors_html(report),
        utilization_chart_html(report),
        summary_html(report),
        recommendations_html(report),
        accounts_table_html(report),
        inquiries_table_html(report),
        disclaimer_html(report),
    ]

    body = "\n".join(f'<div style="margin-bottom:20px;">{s}</div>' for s in sections if s)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CreditSense — {name}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0a0a0f;
    font-family: 'Georgia', 'Times New Roman', serif;
    color: #e5e7eb;
    padding: 24px;
    max-width: 1100px;
    margin: 0 auto;
  }}
  .header {{
    text-align: center;
    padding: 32px 0 24px;
  }}
  .header h1 {{
    font-size: 2rem;
    color: #f8fafc;
    letter-spacing: .05em;
    margin-bottom: 8px;
  }}
  .header .sub {{
    color: #6b7280;
    font-size: .9rem;
  }}
  .header .name {{
    color: #a5b4fc;
    font-size: 1.1rem;
    margin-top: 4px;
  }}
  .footer {{
    text-align: center;
    padding: 24px 0;
    color: #4b5563;
    font-size: .78rem;
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>CreditSense</h1>
    <div class="sub">{bureau} Report &mdash; {report_date}</div>
    <div class="name">{name}</div>
  </div>
  {body}
  <div class="footer">
    Generated by CreditSense &mdash; {generated}
  </div>
</body>
</html>"""


# ── Helpers ─────────────────────────────────────────────────────
def _iframe(inner_html: str, height: int = 400) -> str:
    """Wrap raw HTML in a sandboxed iframe."""
    safe = inner_html.replace('"', '&quot;')
    return f'<iframe srcdoc="{safe}" style="width:100%;height:{height}px;border:none;border-radius:16px;"></iframe>'


def _section(title: str, content: str) -> str:
    """Wrap content in a titled dark section."""
    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">{title}</h2>
      {content}
    </div>
    """
