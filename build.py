#!/usr/bin/env python3
"""쌤이다 총괄보고 빌드: data/*.json -> index.html + reports/YYYY-MM-DD.html

사용법:  python build.py
데이터 규칙 (data/YYYY-MM-DD.json)
  reports[].issues[]  {area, level(risk|decision|wait|insight|ongoing), title, body}
  reports[].done[]    {area, text, note?, sub?[], files?[[label, path|url]], status?}
  reports[].todo[]    {id, area, text, note?, due?(YYYY-MM-DD), pri?(high)}
  reports[].closed[]  이전 날짜 todo id 중 완료된 것 (완료 처리 = 대시보드에서 사라짐)
  reports[].pending   true면 미제출
"""
import json, glob, os, html, datetime as dt

ROOT = os.path.dirname(os.path.abspath(__file__))
WD = "월화수목금토일"
LEVEL = {"risk": ("위험", "lv-risk"), "decision": ("결정", "lv-dec"), "wait": ("대기", "lv-wait"),
         "insight": ("발견", "lv-ins"), "ongoing": ("진행 과제", "lv-on")}

def e(s): return html.escape(str(s or ""))
def d(s): return dt.date.fromisoformat(s)
def md(s): x = d(s); return f"{x.month}/{x.day}({WD[x.weekday()]})"

days = []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))):
    days.append(json.load(open(f, encoding="utf-8")))
latest = days[-1]
TODAY = d(latest["date"])

# ---------- todo 이월 계산 ----------
closed = set()
for day in days:
    for r in day["reports"]:
        closed.update(r.get("closed", []))
open_todos = []
for day in days:
    for r in day["reports"]:
        for t in r.get("todo", []):
            if t["id"] in closed: continue
            t = dict(t); t["who"] = r["name"]; t["wid"] = r["id"]; t["from"] = day["date"]
            t["age"] = (TODAY - d(day["date"])).days
            open_todos.append(t)

def due_badge(t, prefix=""):
    if not t.get("due"): return ""
    left = (d(t["due"]) - TODAY).days - 1  # 보고일 다음날 기준
    cls = "due-hot" if left <= 0 else ("due-warm" if left <= 3 else "due")
    return f'<span class="{cls}">~{md(t["due"])}</span>'

def link(label, path, prefix):
    href = path if path.startswith("http") else prefix + path
    ext = "↗" if path.startswith("http") else "→"
    return f'<a class="file" href="{e(href)}" target="_blank" rel="noopener">{e(label)} <i>{ext}</i></a>'


def page(title, body, prefix):
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>{e(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>{body}
<footer class="ft">쌤이다 총괄보고 · 아이스캔 그룹 내부용 · 외부 공유 금지</footer>
</body></html>"""

def issue_html(i, who=None):
    lb, cls = LEVEL.get(i.get("level"), ("이슈", "lv-on"))
    w = f'<span class="who">{e(who)}</span>' if who else ""
    body = f'<p>{e(i["body"])}</p>' if i.get("body") else ""
    return f'<li class="iss"><div class="ih"><span class="lv {cls}">{lb}</span><span class="area">{e(i["area"])}</span>{w}</div><b>{e(i["title"])}</b>{body}</li>'

def done_html(t, prefix):
    sub = "".join(f"<li>{e(s)}</li>" for s in t.get("sub", []))
    sub = f'<ul class="sub">{sub}</ul>' if sub else ""
    note = f'<span class="note">{e(t["note"])}</span>' if t.get("note") else ""
    files = "".join(link(a, b, prefix) for a, b in t.get("files", []))
    files = f'<div class="files">{files}</div>' if files else ""
    st = t.get("status", "완료")
    stc = "st-done" if st == "완료" else "st-prog"
    return f'<li class="it"><span class="st {stc}">{e(st)}</span><div class="tx"><div class="tt"><span class="area">{e(t["area"])}</span><b>{e(t["text"])}</b>{note}</div>{sub}{files}</div></li>'

def todo_html(t, show_who=False):
    note = f'<span class="note">{e(t["note"])}</span>' if t.get("note") else ""
    pri = '<span class="pri">우선</span>' if t.get("pri") == "high" else ""
    age = f'<span class="carry">{t["age"]}일째 이월</span>' if t.get("age", 0) > 0 else ""
    who = f'<span class="who">{e(t["who"])}</span>' if show_who else ""
    return f'<li class="it todo"><span class="box"></span><div class="tx"><div class="tt"><span class="area">{e(t["area"])}</span><b>{e(t["text"])}</b>{pri}{due_badge(t)}{age}{who}</div>{note and "<div>"+note+"</div>"}</div></li>'

# ---------- 일자별 총괄 보고 ----------
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
for day in days:
    P = "../"
    rs = day["reports"]
    sub_n = sum(1 for r in rs if not r.get("pending"))
    nav = "".join(f'<a href="#{r["id"]}" class="{"off" if r.get("pending") else ""}">{e(r["name"])} {e(r.get("title",""))}</a>' for r in rs)
    cards = []
    for r in rs:
        head = f'<div class="ph"><div><h2>{e(r["name"])} <small>{e(r.get("title",""))}</small></h2><span class="role">{e(r.get("role",""))}</span></div>'
        if r.get("original"): head += f'<a class="orig" href="{P}{e(r["original"])}">원본 보고서 ↓</a>'
        head += "</div>"
        if r.get("pending"):
            cards.append(f'<section class="person pend" id="{r["id"]}">{head}<p class="pendmsg">미제출 — 제출되면 여기에 들어갑니다</p></section>')
            continue
        iss = "".join(issue_html(i) for i in r.get("issues", []))
        dn = "".join(done_html(t, P) for t in r.get("done", []))
        td = "".join(todo_html(dict(t, age=0)) for t in r.get("todo", []))
        cards.append(f"""<section class="person" id="{r['id']}">{head}
<h3 class="sec">이슈 <em>{len(r.get('issues',[]))}</em></h3><ul class="issues">{iss}</ul>
<div class="cols"><div><h3 class="sec">오늘 한 일 <em>{len(r.get('done',[]))}</em></h3><ul class="list">{dn}</ul></div>
<div><h3 class="sec">내일 할 일 <em>{len(r.get('todo',[]))}</em></h3><ul class="list">{td}</ul></div></div></section>""")
    body = f"""<header class="hd"><div class="in"><a class="back" href="{P}index.html">← 대시보드</a>
<div class="kick">쌤이다 총괄보고 · 일일</div><h1>{d(day['date']).year}. {d(day['date']).month}. {d(day['date']).day} ({WD[d(day['date']).weekday()]})</h1>
<p class="meta">제출 {sub_n} / {len(rs)}명</p><nav class="pnav">{nav}</nav></div></header>
<main class="in">{''.join(cards)}</main>"""
    open(os.path.join(ROOT, "reports", day["date"] + ".html"), "w", encoding="utf-8").write(page(f"쌤이다 총괄보고 {day['date']}", body, P))

# ---------- 대시보드 ----------
P = ""
rs = latest["reports"]
sub_n = sum(1 for r in rs if not r.get("pending"))
all_issues = [(r["name"], i) for r in rs for i in r.get("issues", [])]
order = {"risk": 0, "decision": 1, "wait": 2, "insight": 3, "ongoing": 4}
all_issues.sort(key=lambda x: order.get(x[1].get("level"), 9))
hot = [t for t in open_todos if t.get("due") and (d(t["due"]) - TODAY).days <= 2]
done_n = sum(len(r.get("done", [])) for r in rs)

kpi = f"""<div class="kpis">
<div class="kpi"><span>보고 제출</span><b>{sub_n}<small>/{len(rs)}</small></b></div>
<div class="kpi"><span>오늘 완료</span><b>{done_n}</b></div>
<div class="kpi"><span>열린 할 일</span><b>{len(open_todos)}</b></div>
<div class="kpi warn"><span>마감 임박 (2일 내)</span><b>{len(hot)}</b></div></div>"""

boards = []
for r in rs:
    ts = [t for t in open_todos if t["wid"] == r["id"]]
    ts.sort(key=lambda t: (t.get("pri") != "high", t.get("due") or "9999"))
    inner = "".join(todo_html(t) for t in ts) if ts else '<li class="empty">할 일 없음</li>'
    if r.get("pending"): inner = '<li class="empty">보고 미제출</li>'
    boards.append(f'<div class="board"><div class="bh"><b>{e(r["name"])} <small>{e(r.get("title",""))}</small></b><em>{len(ts)}</em></div><ul class="list">{inner}</ul></div>')

hist = "".join(f'<li><a href="reports/{x["date"]}.html"><b>{md(x["date"])}</b><span>제출 {sum(1 for r in x["reports"] if not r.get("pending"))}/{len(x["reports"])} · 이슈 {sum(len(r.get("issues",[])) for r in x["reports"])} · 완료 {sum(len(r.get("done",[])) for r in x["reports"])}</span><i>→</i></a></li>' for x in reversed(days))

outs = []
for x in reversed(days):
    for r in x["reports"]:
        for t in r.get("done", []):
            for a, b in t.get("files", []):
                outs.append(f'<li>{link(a, b, P)}<span>{e(r["name"])} · {md(x["date"])} · {e(t["text"])}</span></li>')

body = f"""<header class="hd"><div class="in"><div class="kick">쌤이다 총괄보고 · Dashboard</div>
<h1>쌤이다 총괄 현황</h1><p class="meta">기준 {md(latest['date'])} · 보고 {e(', '.join(r['name']+' '+r.get('title','') for r in rs))}</p>{kpi}</div></header>
<main class="in">
<h3 class="sec big">할 일 <em>{len(open_todos)}</em><a class="more" href="reports/{latest['date']}.html">{md(latest['date'])} 보고 전체 →</a></h3>
<div class="boards">{''.join(boards)}</div>
<h3 class="sec big">이슈 <em>{len(all_issues)}</em></h3><ul class="issues grid">{''.join(issue_html(i, w) for w, i in all_issues)}</ul>
<div class="cols2"><div><h3 class="sec big">일자별 보고</h3><ul class="hist">{hist}</ul></div>
<div><h3 class="sec big">산출물</h3><ul class="outs">{''.join(outs)}</ul></div></div>
</main>"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page("쌤이다 총괄보고", body, P))
print("built:", len(days), "day(s),", len(open_todos), "open todos")

# ---------- 산출물 HTML 모바일 보정 (갤럭시 폴드 커버/메인 화면) ----------
MOBILE_TAG = "<!--ssr-mobile-->"
GENERIC = """<style>@media(max-width:900px){html{-webkit-text-size-adjust:100%}
img,video,svg{max-width:100%;height:auto}
table{display:block;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
pre,code{white-space:pre-wrap;word-break:break-all}}</style>"""
DECK = """<style>
/* 좁은 세로 화면(폴드 커버·폰): 슬라이드를 세로 문서로 펼침 */
@media (max-width:900px) and (orientation:portrait){
html,body{height:auto!important;overflow:auto!important;display:block!important;-webkit-text-size-adjust:100%}
#canvas{transform:none!important;width:100%!important;height:auto!important}
.s{position:relative!important;display:flex!important;inset:auto;padding:34px 18px 30px!important;border-bottom:1px solid #22282c;min-height:0}
h1{font-size:34px!important;letter-spacing:-1.2px!important}
h2{font-size:24px!important;letter-spacing:-.8px!important;margin-bottom:16px!important}
h3{font-size:17px!important}
p{font-size:15.5px!important}.sub{font-size:13.5px!important}
li{font-size:15px!important;margin-bottom:10px!important}li:before{top:9px!important}
.kick{font-size:11px!important;margin-bottom:12px!important}
table{display:table!important;width:100%!important;font-size:13px!important}th,td{padding:7px 8px!important;font-size:13px!important;width:auto!important}
table[style*="font-size:15px"]{display:block!important;overflow-x:auto}table[style*="font-size:15px"] th,table[style*="font-size:15px"] td{min-width:82px}
td.c,th.c{white-space:normal!important}
.two{grid-template-columns:1fr!important;gap:12px!important}
.card{padding:16px!important}.card p{font-size:14.5px!important}
.big{font-size:46px!important;letter-spacing:-2px!important}
.bar .l{width:96px!important;font-size:13px!important}.bar{font-size:13px!important}
.sb{grid-template-columns:repeat(2,1fr)!important;gap:12px!important}
.sb>div{min-width:0}.fr{width:100%!important;height:auto!important;aspect-ratio:1/1}.fl{width:auto!important}
.s>div[style*="display:flex"]{flex-direction:column!important;gap:20px!important}
.wf{zoom:.76}
.nav,#hud,#tip,#bar{display:none!important}
}</style>"""
for f in glob.glob(os.path.join(ROOT, "files", "*", "*.html")):
    t = open(f, encoding="utf-8").read()
    if MOBILE_TAG in t: continue
    css = GENERIC + (DECK if 'id="canvas"' in t else "")
    t = t.replace("</head>", MOBILE_TAG + css + "</head>", 1)
    open(f, "w", encoding="utf-8").write(t)
