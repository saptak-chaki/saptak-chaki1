#!/usr/bin/env python3
"""
generate_profile.py  (v3 - JDM neon Tokyo night)

Builds profile.svg for the saptak-chaki GitHub profile:
  * neon Tokyo night, a JDM coupe driving with exhaust flame pops
  * rim-shaped language graph (spinning), gauge stats
  * live stats + a language-percentage graph from ALL your repositories
Standard library only.

    GITHUB_TOKEN=xxxx python generate_profile.py     # live data
    python generate_profile.py --demo                # offline sample data
"""
import json
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

# ----------------------------------------------------------------------------
# CONFIG - edit this part only
# ----------------------------------------------------------------------------
USERNAME = os.environ.get("GITHUB_USER", "saptak-chaki")
NAME = "SAPTAK CHAKI"
TITLE = "ASPIRING PYTHON FULL STACK DEVELOPER"
SUBTITLE = "B.Tech CSE · IoT · Cyber Security · Blockchain"
ABOUT_LINES = [
    "Welcome to my garage! I am Saptak Chaki, a B.Tech",
    "CSE student crafting powerful Python full-stack applications.",
    "I specialize in IoT, Cyber Security, and Blockchain—brewing",
    "secure, high-performance digital magic into every build.",
]
TECH = [
    "Python", "Django", "Flask / FastAPI",
    "HTML / CSS", "JavaScript", "React",
    "SQL / MySQL", "Git / GitHub", "Linux",
    "IoT", "Cyber Security", "Blockchain",
]
TOP_LANGS = 5          # languages shown in the graph (rest become "Other")
OUTPUT = "profile.svg"
W = 980
H = 1320

# ----------------------------------------------------------------------------
# GitHub data
# ----------------------------------------------------------------------------
API = "https://api.github.com/graphql"


def gql(query, variables, token):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-svg-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_stats(token):
    q1 = """query($login:String!){ user(login:$login){
        contributionsCollection{ contributionYears }
        repositories(ownerAffiliations:OWNER, isFork:false, first:100){
            totalCount
            nodes{ stargazerCount
                   languages(first:10, orderBy:{field:SIZE, direction:DESC}){
                       edges{ size node{ name } } } } } } }"""
    u = gql(q1, {"login": USERNAME}, token)["user"]
    years = u["contributionsCollection"]["contributionYears"]
    repos = u["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])

    sizes = {}
    for n in u["repositories"]["nodes"]:
        for e in (n.get("languages") or {}).get("edges", []):
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]

    q2 = """query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
        contributionsCollection(from:$from,to:$to){ totalCommitContributions
          contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }"""
    commits, days = 0, {}
    for y in years:
        d = gql(q2, {"login": USERNAME, "from": f"{y}-01-01T00:00:00Z",
                     "to": f"{y}-12-31T23:59:59Z"}, token)["user"]["contributionsCollection"]
        commits += d["totalCommitContributions"]
        for w in d["contributionCalendar"]["weeks"]:
            for day in w["contributionDays"]:
                days[day["date"]] = day["contributionCount"]

    streak, cur = 0, date.today()
    if days.get(cur.isoformat(), 0) == 0:
        cur -= timedelta(days=1)
    while days.get(cur.isoformat(), 0) > 0:
        streak += 1
        cur -= timedelta(days=1)
    return {"commits": commits, "repos": repos, "stars": stars, "streak": streak,
            "langs": language_percentages(sizes)}


def language_percentages(sizes):
    total = sum(sizes.values())
    if not total:
        return []
    ranked = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
    top, rest = ranked[:TOP_LANGS], ranked[TOP_LANGS:]
    out = [(n, s * 100.0 / total) for n, s in top]
    if rest:
        out.append(("Other", sum(s for _, s in rest) * 100.0 / total))
    return out


# ----------------------------------------------------------------------------
# SVG
# ----------------------------------------------------------------------------
MAG, CYA, VIO, ORA = "#ff2bd6", "#19e3ff", "#8b5cff", "#ffb02e"
PAL = [MAG, CYA, VIO, ORA, "#3dffa2", "#ff5a7a"]
import math

STYLE = """<style>
text{font-family:'Arial Black',Impact,'Segoe UI',sans-serif}
.m{font-family:'Courier New',Courier,monospace;font-weight:700}
.card{fill:#0b0820;fill-opacity:.78;stroke-width:1.6}
.bob{animation:bob 1.1s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 100%}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-2.5px)}}
.spin{animation:spin .55s linear infinite;transform-box:fill-box;transform-origin:50% 50%}
.spinS{animation:spin 14s linear infinite;transform-box:fill-box;transform-origin:50% 50%}
@keyframes spin{to{transform:rotate(360deg)}}
.sk{animation:sk 6s linear infinite}
.sk2{animation:sk 14s linear infinite}
@keyframes sk{from{transform:translateX(0)}to{transform:translateX(-980px)}}
.road{animation:rd .35s linear infinite}
@keyframes rd{from{transform:translateX(0)}to{transform:translateX(-80px)}}
.streak{animation:st 1.2s linear infinite}
@keyframes st{from{transform:translateX(120px);opacity:0}20%{opacity:.9}to{transform:translateX(-260px);opacity:0}}
.pop{transform-box:fill-box;transform-origin:100% 50%;animation:pop 1.7s ease-out infinite;animation-delay:var(--d,0s);opacity:0}
@keyframes pop{0%{transform:scale(.1);opacity:0}8%{opacity:1}30%{transform:scale(1.15);opacity:.95}60%,100%{transform:scale(1.5,.4);opacity:0}}
.spark{animation:sp 1.7s ease-out infinite;animation-delay:var(--d,0s);opacity:0}
@keyframes sp{0%{transform:translate(0,0);opacity:0}10%{opacity:1}100%{transform:translate(-90px,var(--y,-20px));opacity:0}}
.glow{animation:gl 2.4s ease-in-out infinite alternate}
@keyframes gl{from{opacity:.55}to{opacity:1}}
.arc{stroke-dashoffset:var(--len);animation:draw 2.2s ease-out forwards}
@keyframes draw{to{stroke-dashoffset:var(--off)}}
.tick{animation:tk 3s ease-in-out infinite alternate;animation-delay:var(--d,0s)}
@keyframes tk{from{opacity:.5}to{opacity:1}}
</style>"""

DEFS = f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05030f"/><stop offset=".55" stop-color="#1a0b45"/><stop offset="1" stop-color="#3a0f5e"/></linearGradient>
<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a2bff"/><stop offset=".45" stop-color="#d21fc0"/><stop offset="1" stop-color="#2a0b6b"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0a0a22"/><stop offset=".5" stop-color="#1b2a66"/><stop offset="1" stop-color="#05050f"/></linearGradient>
<linearGradient id="chrome" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f9ff"/><stop offset=".5" stop-color="#6c7bb8"/><stop offset="1" stop-color="#1a1d3a"/></linearGradient>
<radialGradient id="tire" cx=".5" cy=".5" r=".5"><stop offset=".78" stop-color="#0d0d14"/><stop offset="1" stop-color="#000"/></radialGradient>
<radialGradient id="fire" cx=".9" cy=".5" r=".9"><stop offset="0" stop-color="#fff6c8"/><stop offset=".3" stop-color="{ORA}"/><stop offset=".7" stop-color="#ff2f5e"/><stop offset="1" stop-color="#ff2f5e" stop-opacity="0"/></radialGradient>
<linearGradient id="road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1040"/><stop offset="1" stop-color="#05030f"/></linearGradient>
<filter id="neon" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft"><feGaussianBlur stdDeviation="6"/></filter>
<symbol id="wheel" viewBox="-30 -30 60 60" overflow="visible">
 <circle r="26" fill="url(#tire)"/><circle r="26" fill="none" stroke="{MAG}" stroke-width=".8" opacity=".7"/>
 <circle r="18" fill="#1a1d3a" stroke="url(#chrome)" stroke-width="2.4"/>
 <g class="spin">{"".join(f'<g transform="rotate({i*72})"><path d="M-2.2 -3 L-3 -17 L0 -17.5 L3 -17 L2.2 -3Z" fill="url(#chrome)"/><path d="M0 -6 L0 -16" stroke="#000" stroke-width=".7" opacity=".5"/></g>' for i in range(5))}
 <circle r="5" fill="url(#chrome)"/><circle r="1.6" fill="#05050f"/></g>
 <path d="M6 -14 A15 15 0 0 1 14 -6 L9 -3 A9 9 0 0 0 4 -8Z" fill="{MAG}" opacity=".9"/>
</symbol>
</defs>"""


def stars(rnd):
    return "".join(f'<circle cx="{rnd.randint(0,W)}" cy="{rnd.randint(0,300)}" r="{rnd.choice([.6,.9,1.2])}" fill="#fff" class="tick" style="--d:{rnd.random()*3:.1f}s" opacity=".7"/>' for _ in range(70))


def skyline(rnd, y, hmin, hmax, color, glow=None):
    x, out = 0, []
    while x < W * 2:
        w = rnd.randint(34, 80); h = rnd.randint(hmin, hmax)
        out.append(f'<rect x="{x}" y="{y-h}" width="{w}" height="{h}" fill="{color}"/>')
        if glow:
            for _ in range(rnd.randint(2, 6)):
                out.append(f'<rect x="{x+rnd.randint(4,w-8)}" y="{y-rnd.randint(8,h-4)}" width="3" height="4" fill="{rnd.choice(glow)}" opacity=".85"/>')
        x += w + rnd.randint(2, 10)
    return "".join(out)


def car():
    # original JDM-style coupe, nose to the right, ground line y=0
    return f"""<g class="bob">
<ellipse cx="0" cy="2" rx="150" ry="6" fill="#000" opacity=".55" filter="url(#soft)"/>
<path d="M-150 -18 L-152 -34 Q-150 -42 -138 -44 L-110 -46 Q-96 -48 -82 -62 Q-64 -84 -30 -88 L22 -88 Q52 -86 74 -62 L92 -46 Q124 -42 144 -36 Q154 -33 154 -24 L152 -14 L-150 -14Z" fill="url(#body)" stroke="#ff9bf0" stroke-width="1" filter="url(#neon)"/>
<path d="M-70 -62 Q-56 -80 -28 -82 L16 -82 Q40 -80 58 -62 L-70 -62Z" fill="url(#glass)" stroke="#05030f" stroke-width="1.5"/>
<path d="M-4 -82 L-6 -62" stroke="#05030f" stroke-width="2"/>
<path d="M-44 -78 L-30 -64 M30 -80 L42 -64" stroke="#8fd4ff" stroke-width="1.4" opacity=".5"/>
<path d="M-126 -40 Q-100 -52 -78 -46 M60 -44 Q104 -46 142 -34" fill="none" stroke="#ffd0f8" stroke-width="1.4" opacity=".7"/>
<path d="M-142 -60 L-120 -62 L-118 -58 L-142 -56Z" fill="#7a2bff" stroke="{CYA}" stroke-width="1"/>
<path d="M-92 -60 L-96 -22 M30 -62 L33 -20" stroke="#05030f" stroke-width="1.5" opacity=".8"/>
<rect x="-54" y="-48" width="18" height="3" rx="1.5" fill="#05030f"/>
<rect x="-150" y="-38" width="7" height="10" rx="2" fill="#ff2f5e" filter="url(#neon)" class="glow"/>
<path d="M144 -34 L152 -30 L150 -26 L132 -30Z" fill="#fff" filter="url(#neon)"/>
<path d="M154 -26 L150 -18 L120 -16" fill="none" stroke="{CYA}" stroke-width="2.4" filter="url(#neon)"/>
<path d="M-146 -17 L146 -17" stroke="{CYA}" stroke-width="1.6" filter="url(#neon)" opacity=".9"/>
<ellipse cx="-150" cy="-20" rx="3" ry="2.2" fill="#2a2a38" stroke="url(#chrome)"/>
<g><circle cx="-100" cy="-22" r="30" fill="#05030f"/><use href="#wheel" x="-130" y="-52" width="60" height="60"/></g>
<g><circle cx="92" cy="-22" r="30" fill="#05030f"/><use href="#wheel" x="62" y="-52" width="60" height="60"/></g>
<!-- exhaust pops -->
<g transform="translate(-156,-20)">
 <ellipse class="pop" style="--d:0s" cx="-34" cy="0" rx="40" ry="11" fill="url(#fire)" filter="url(#neon)"/>
 <ellipse class="pop" style="--d:.55s" cx="-26" cy="2" rx="28" ry="8" fill="url(#fire)" filter="url(#neon)"/>
 <ellipse class="pop" style="--d:1.1s" cx="-38" cy="-2" rx="46" ry="12" fill="url(#fire)" filter="url(#neon)"/>
 {"".join(f'<circle class="spark" style="--d:{(i*.37)%1.7:.2f}s;--y:{(-30+i*9)}px" cx="-6" cy="0" r="1.8" fill="{ORA if i%2 else "#fff6c8"}"/>' for i in range(9))}
</g></g>"""


def arc_path(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    return f"M{x0:.1f} {y0:.1f} A{r} {r} 0 {1 if a1-a0>math.pi else 0} 1 {x1:.1f} {y1:.1f}"


def gauge(cx, cy, label, val, target, color, i):
    r = 52; circ = 2 * math.pi * r * 0.75
    frac = min(1.0, val / target) if target else 0
    off = circ * (1 - frac)
    ticks = "".join(f'<line x1="{cx+(r+9)*math.cos(math.radians(135+k*27))}" y1="{cy+(r+9)*math.sin(math.radians(135+k*27))}" x2="{cx+(r+14)*math.cos(math.radians(135+k*27))}" y2="{cy+(r+14)*math.sin(math.radians(135+k*27))}" stroke="{color}" stroke-width="2" opacity=".7"/>' for k in range(11))
    ang = math.radians(135 + 270 * frac)
    return f"""<g>{ticks}
<circle cx="{cx}" cy="{cy}" r="{r+22}" fill="#05030f" opacity=".55" stroke="#2b2260" stroke-width="2"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#241a55" stroke-width="12" stroke-dasharray="{circ:.1f} 999" transform="rotate(135 {cx} {cy})" stroke-linecap="round"/>
<circle class="arc" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{circ:.1f} 999" style="--len:{circ:.1f};--off:{off:.1f}" transform="rotate(135 {cx} {cy})" filter="url(#neon)"/>
<line x1="{cx}" y1="{cy}" x2="{cx+(r-8)*math.cos(ang):.1f}" y2="{cy+(r-8)*math.sin(ang):.1f}" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
<circle cx="{cx}" cy="{cy}" r="5" fill="#fff"/>
<text x="{cx}" y="{cy+34}" text-anchor="middle" font-size="22" fill="#fff">{val}</text>
<text x="{cx}" y="{cy+r+30}" text-anchor="middle" font-size="13" fill="{color}" letter-spacing="2">{label}</text></g>"""


def rim_graph(cx, cy, langs):
    R_t, R_a = 128, 98
    circ = 2 * math.pi * R_a
    segs, a = [], -90.0
    gap = 1.6
    for i, (n, p) in enumerate(langs):
        sweep = p * 3.6
        col = PAL[i % len(PAL)]
        L = circ * max(0.0, sweep - gap) / 360
        segs.append(f'<circle cx="{cx}" cy="{cy}" r="{R_a}" fill="none" stroke="{col}" stroke-width="28" stroke-dasharray="{L:.1f} {circ:.1f}" transform="rotate({a:.1f} {cx} {cy})" filter="url(#neon)"/>')
        a += sweep
    spokes = "".join(f'<g transform="rotate({k*72} {cx} {cy})"><path d="M{cx-5} {cy-26} L{cx-9} {cy-84} L{cx-1} {cy-86} L{cx+1} {cy-26}Z M{cx+5} {cy-26} L{cx+9} {cy-84} L{cx+1} {cy-86} L{cx-1} {cy-26}Z" fill="url(#chrome)" opacity=".92"/></g>' for k in range(5))
    lugs = "".join(f'<circle cx="{cx+16*math.cos(math.radians(k*72-90)):.1f}" cy="{cy+16*math.sin(math.radians(k*72-90)):.1f}" r="3.2" fill="#05030f" stroke="#cfd8ff"/>' for k in range(5))
    return f"""<g>
<circle cx="{cx}" cy="{cy}" r="{R_t+8}" fill="#000" opacity=".5" filter="url(#soft)"/>
<circle cx="{cx}" cy="{cy}" r="{R_t}" fill="#07070d" stroke="#2b2260" stroke-width="3"/>
<circle cx="{cx}" cy="{cy}" r="{R_t-10}" fill="none" stroke="{MAG}" stroke-width="1.2" opacity=".8"/>
<circle cx="{cx}" cy="{cy}" r="{R_a+20}" fill="#12123a" stroke="url(#chrome)" stroke-width="3"/>
{"".join(segs)}
<circle cx="{cx}" cy="{cy}" r="{R_a-16}" fill="#0a0a22" stroke="url(#chrome)" stroke-width="2"/>
<g class="spinS">{spokes}</g>
<circle cx="{cx}" cy="{cy}" r="30" fill="url(#chrome)"/><circle cx="{cx}" cy="{cy}" r="24" fill="#10132b"/>
{lugs}
<path d="M{cx+52} {cy-70} A88 88 0 0 1 {cx+84} {cy-20} L{cx+60} {cy-12} A62 62 0 0 0 {cx+40} {cy-48}Z" fill="{MAG}" opacity=".35"/>
</g>"""


def card(x, y, w, h, color=CYA):
    return f'<rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="16" stroke="{color}" filter="url(#neon)"/>'


def heading(x, y, t, color=CYA):
    return f'<text x="{x}" y="{y}" font-size="24" fill="{color}" letter-spacing="3" filter="url(#neon)">{escape(t)}</text>'


def build_svg(st):
    rnd = random.Random(7)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}">', STYLE, DEFS,
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>', stars(rnd)]
    # parallax city
    o.append(f'<g class="sk2" opacity=".9">{skyline(rnd,330,60,150,"#150a38",["#19e3ff","#ff2bd6"])}</g>')
    o.append(f'<g class="sk">{skyline(rnd,360,40,110,"#0b0522",["#ffb02e","#ff2bd6","#19e3ff"])}</g>')
    # road
    o.append(f'<rect x="0" y="352" width="{W}" height="58" fill="url(#road)"/><rect x="0" y="352" width="{W}" height="2" fill="{CYA}" filter="url(#neon)"/>')
    o.append(f'<g class="road">{"".join(f'<rect x="{i*80}" y="382" width="44" height="4" rx="2" fill="{MAG}" opacity=".9"/>' for i in range(-1,14))}</g>')
    for i in range(7):
        y = 360 + i * 7
        o.append(f'<rect class="streak" style="animation-delay:{i*.17:.2f}s" x="{300+i*90}" y="{y}" width="{70+i*10}" height="2" fill="{CYA}" opacity=".7"/>')
    o.append(f'<g transform="translate(560,372) scale(1.0)">{car()}</g>')
    # title
    o.append(f'<text x="40" y="92" font-size="64" fill="#fff" filter="url(#neon)" letter-spacing="4">{escape(NAME)}</text>')
    o.append(f'<text x="42" y="132" font-size="21" fill="{MAG}" letter-spacing="2" filter="url(#neon)">{escape(TITLE)}</text>')
    o.append(f'<text x="42" y="164" class="m" font-size="16" fill="{CYA}">{escape(SUBTITLE)}</text>')
    # about
    o.append(card(30, 430, 920, 170, MAG) + heading(60, 472, "// ABOUT THE DRIVER", MAG))
    for i, ln in enumerate(ABOUT_LINES):
        o.append(f'<text x="60" y="{506+i*26}" class="m" font-size="16" fill="#e8e6ff" style="font-family:\'Courier New\',monospace">{escape(ln)}</text>')
    # gauges
    o.append(card(30, 620, 920, 210, CYA) + heading(60, 660, "DASHBOARD", CYA))
    items = [("COMMITS", st["commits"], max(100, st["commits"]*1.5), MAG), ("REPOS", st["repos"], max(10, st["repos"]*1.5), CYA),
             ("STARS", st["stars"], max(10, st["stars"]*1.5), ORA), ("STREAK", st["streak"], max(14, st["streak"]*1.5), "#3dffa2")]
    for i, (l, v, t, c) in enumerate(items):
        o.append(gauge(145 + i * 230, 735, l, v, t, c, i))
    # rim graph
    o.append(card(30, 850, 920, 260, VIO) + heading(60, 890, "RIM  //  LANGUAGE MIX", VIO))
    langs = st["langs"] or [("No code yet", 100.0)]
    o.append(f'<g transform="translate(210,1006) scale(.8) translate(-210,-1010)">{rim_graph(210,1010,langs)}</g>')
    for i, (n, p) in enumerate(langs):
        y = 930 + i * 34
        col = PAL[i % len(PAL)]
        o.append(f'<rect x="480" y="{y-14}" width="16" height="16" rx="4" fill="{col}" filter="url(#neon)"/>')
        o.append(f'<text x="508" y="{y}" font-size="17" fill="#fff">{escape(n)}</text>')
        o.append(f'<rect x="680" y="{y-12}" width="200" height="10" rx="5" fill="#241a55"/><rect x="680" y="{y-12}" width="{2*p:.0f}" height="10" rx="5" fill="{col}"/>')
        o.append(f'<text x="935" y="{y}" text-anchor="end" font-size="16" fill="{col}" class="m">{p:.1f}%</text>')
    # tech
    o.append(card(30, 1130, 920, 170, ORA) + heading(60, 1170, "GARAGE // TECH STACK", ORA))
    for i, t in enumerate(TECH):
        col, row = i % 4, i // 4
        x, y = 60 + col * 225, 1192 + row * 36
        c = PAL[i % len(PAL)]
        o.append(f'<rect x="{x}" y="{y}" width="205" height="28" rx="14" fill="#0b0820" stroke="{c}" stroke-width="1.6" filter="url(#neon)"/>')
        o.append(f'<text x="{x+102}" y="{y+19}" text-anchor="middle" font-size="14" fill="#fff">{escape(t)}</text>')
    o.append('</svg>')
    return "\n".join(o)


DEMO = {"commits": 27, "repos": 3, "stars": 0, "streak": 1,
        "langs": [("Python", 48.0), ("JavaScript", 22.0), ("HTML", 15.0), ("CSS", 10.0), ("Other", 5.0)]}


def main():
    if "--demo" in sys.argv:
        st = DEMO
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GITHUB_TOKEN or use --demo")
        st = fetch_stats(token)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(build_svg(st))
    print("wrote", OUTPUT, st)


if __name__ == "__main__":
    main()
