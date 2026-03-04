"""
views.py
Handles all raw HTML, CSS, and Chart.js string generation.
"""

import json
from typing import List, Dict
from backend.backend import MACRO_BUCKETS, RECOMMENDED, FinancialState


def bar_chart_html(macro_buckets: Dict[str, float], sub_categories: Dict[str, float]) -> str:
    labels_macro = list(macro_buckets.keys())
    values_macro = [round(v, 2) for v in macro_buckets.values()]
    sub_sorted = sorted(sub_categories.items(), key=lambda x: x[1], reverse=True)[:12]
    labels_sub = [s[0] for s in sub_sorted]
    values_sub = [round(s[1], 2) for s in sub_sorted]
    colors = ["#22c55e","#3b82f6","#a855f7","#f97316","#eab308","#ef4444",
              "#06b6d4","#ec4899","#8b5cf6","#14b8a6","#f59e0b","#6366f1"]

    inner_html = f"""<!DOCTYPE html><html><head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>body{{margin:0;padding:20px;background:#0f0f13;font-family:Georgia,serif;color:#e5e7eb;}}
    h3{{color:#a5b4fc;font-size:.95rem;margin:20px 0 10px;}}</style>
    </head><body>
    <h3>Macro Buckets</h3>
    <canvas id="mc"></canvas>
    <h3 style="margin-top:32px;">Top Sub-Categories</h3>
    <canvas id="sc"></canvas>
    <script>
    new Chart(document.getElementById('mc'),{{
      type:'bar',
      data:{{labels:{json.dumps(labels_macro)},datasets:[{{label:'$',data:{json.dumps(values_macro)},
        backgroundColor:{json.dumps(colors[:len(labels_macro)])},borderRadius:6,borderSkipped:false}}]}},
      options:{{responsive:true,plugins:{{legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>'$ '+c.parsed.y.toLocaleString()}}}}}},
        scales:{{x:{{ticks:{{color:'#d1d5db'}},grid:{{color:'#1f2937'}}}},
                 y:{{ticks:{{color:'#d1d5db',callback:v=>'$'+v.toLocaleString()}},grid:{{color:'#1f2937'}}}}}}}}
    }});
    new Chart(document.getElementById('sc'),{{
      type:'bar',
      data:{{labels:{json.dumps(labels_sub)},datasets:[{{label:'$',data:{json.dumps(values_sub)},
        backgroundColor:{json.dumps((colors*2)[:len(labels_sub)])},borderRadius:6,borderSkipped:false}}]}},
      options:{{indexAxis:'y',responsive:true,plugins:{{legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>'$ '+c.parsed.x.toLocaleString()}}}}}},
        scales:{{x:{{ticks:{{color:'#d1d5db',callback:v=>'$'+v.toLocaleString()}},grid:{{color:'#1f2937'}}}},
                 y:{{ticks:{{color:'#d1d5db'}},grid:{{color:'#1f2937'}}}}}}}}
    }});
    </script></body></html>"""

    return f'<iframe srcdoc="{inner_html.replace(chr(34), "&quot;")}" style="width:100%;height:700px;border:none;border-radius:16px;"></iframe>'


def budget_chart_html(macro_buckets: Dict[str, float], total_income: float) -> str:
    income = total_income or 1
    buckets     = [b for b in MACRO_BUCKETS if b != "Income"]
    actual_pct  = [round(macro_buckets.get(b, 0) / income * 100, 1) for b in buckets]
    rec_min_pct = [RECOMMENDED.get(b, (0, 0))[0] for b in buckets]
    rec_max_pct = [RECOMMENDED.get(b, (0, 0))[1] for b in buckets]

    inner_html = f"""<!DOCTYPE html><html><head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>body{{margin:0;padding:20px;background:#0f0f13;font-family:Georgia,serif;color:#e5e7eb;}}</style>
    </head><body>
    <canvas id="bc"></canvas>
    <script>
    var ap={json.dumps(actual_pct)};
    var rm={json.dumps(rec_max_pct)};
    new Chart(document.getElementById('bc'),{{
      type:'bar',
      data:{{labels:{json.dumps(buckets)},datasets:[
        {{label:'Actual %',data:ap,backgroundColor:'rgba(99,102,241,0.75)',borderRadius:6,borderSkipped:false,order:1}},
        {{label:'Rec. Min %',data:{json.dumps(rec_min_pct)},type:'line',borderColor:'#22c55e',
          borderDash:[6,3],borderWidth:2,pointRadius:5,pointBackgroundColor:'#22c55e',fill:false,order:0}},
        {{label:'Rec. Max %',data:rm,type:'line',borderColor:'#ef4444',
          borderDash:[6,3],borderWidth:2,pointRadius:5,pointBackgroundColor:'#ef4444',fill:false,order:0}}
      ]}},
      options:{{responsive:true,
        plugins:{{legend:{{labels:{{color:'#d1d5db'}}}},
          tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y+'%'}}}}}},
        scales:{{x:{{ticks:{{color:'#d1d5db'}},grid:{{color:'#1f2937'}}}},
                 y:{{ticks:{{color:'#d1d5db',callback:v=>v+'%'}},grid:{{color:'#1f2937'}},
                    max:Math.max(...ap,...rm)+10}}}}}}
    }});
    </script></body></html>"""

    return f'<iframe srcdoc="{inner_html.replace(chr(34), "&quot;")}" style="width:100%;height:420px;border:none;border-radius:16px;"></iframe>'


def scorecard_html(state: FinancialState) -> str:
    income  = state["total_income"]
    expenses = state["total_expenses"]
    net = income - expenses
    net_color = "#22c55e" if net >= 0 else "#ef4444"
    savings_rate = round((state["macro_buckets"].get("Savings", 0) + state["macro_buckets"].get("Investments", 0)) / (income or 1) * 100, 1)

    cards = [
        ("💵 Monthly Income",    f"${income:,.2f}",   "#22c55e"),
        ("💸 Monthly Expenses",  f"${expenses:,.2f}", "#3b82f6"),
        ("📈 Net Cash Flow",     f"${net:,.2f}",      net_color),
        ("🏦 Wealth Building %", f"{savings_rate}%",  "#a855f7"),
        (f"{state.get('income_tier', '')} Income Tier", state.get("tier_label", "Unknown"), "#f97316"),
    ]

    cards_html = "".join(f"""
      <div style="background:#1a1a2e;border:1px solid #2d2d4a;border-radius:12px;padding:18px 22px;min-width:160px;flex:1;">
        <div style="color:#9ca3af;font-size:.78rem;margin-bottom:6px;">{c[0]}</div>
        <div style="color:{c[2]};font-size:1.25rem;font-weight:700;font-family:'Georgia',serif;">{c[1]}</div>
      </div>
    """ for c in cards)

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;letter-spacing:.03em;">🏆 Financial Scorecard</h2>
      <div style="display:flex;flex-wrap:wrap;gap:12px;">{cards_html}</div>
    </div>
    """


def transaction_table_html(transactions: List[Dict]) -> str:
    if not transactions:
        return "<p style='color:#9ca3af;'>No transactions extracted.</p>"

    rows = ""
    bucket_colors = {
        "Income": "#22c55e", "Living Expenses": "#3b82f6", "Lifestyle": "#a855f7",
        "Debt": "#f97316", "Savings": "#eab308", "Investments": "#ef4444",
    }
    for t in transactions[:50]:
        bucket = t.get("macro_bucket", "")
        color  = bucket_colors.get(bucket, "#9ca3af")
        direction = t.get("direction", "out")
        amt_color = "#22c55e" if direction == "in" else "#f87171"
        prefix = "+" if direction == "in" else "−"
        rows += f"""
        <tr style="border-bottom:1px solid #1f2937;">
          <td style="padding:8px 10px;color:#9ca3af;font-size:.82rem;">{t.get('date','')}</td>
          <td style="padding:8px 10px;font-size:.85rem;">{t.get('description','')[:45]}</td>
          <td style="padding:8px 10px;">
            <span style="background:{color}22;color:{color};border-radius:4px;padding:2px 8px;font-size:.78rem;">{bucket}</span>
          </td>
          <td style="padding:8px 10px;font-size:.82rem;color:#d1d5db;">{t.get('category','')}</td>
          <td style="padding:8px 10px;color:{amt_color};font-weight:600;text-align:right;">{prefix}${t.get('amount',0):,.2f}</td>
        </tr>
        """

    return f"""
    <div style="font-family:'Georgia',serif;background:#0f0f13;padding:24px;border-radius:16px;color:#e5e7eb;overflow-x:auto;">
      <h2 style="color:#f8fafc;margin-bottom:16px;font-size:1.4rem;">📋 Transactions ({len(transactions)} total)</h2>
      <table style="width:100%;border-collapse:collapse;font-size:.88rem;">
        <thead>
          <tr style="border-bottom:2px solid #374151;">
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Date</th>
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Description</th>
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Macro Bucket</th>
            <th style="padding:8px 10px;text-align:left;color:#6b7280;font-weight:500;">Category</th>
            <th style="padding:8px 10px;text-align:right;color:#6b7280;font-weight:500;">Amount</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      {'<p style="color:#6b7280;font-size:.78rem;margin-top:8px;">Showing first 50 transactions</p>' if len(transactions) > 50 else ''}
    </div>
    """