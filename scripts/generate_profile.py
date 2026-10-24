#!/usr/bin/env python3
"""
generate_profile.py  (v4 - neon Tokyo AE86 hero + live stats)

Builds profile.svg for the saptak-chaki GitHub profile:
  * hero banner: neon Tokyo street, AE86 with blinking headlights + engine vibration
  * dashboard gauges (commits / repos / stars / streak) from LIVE GitHub data
  * spinning rim + language-percentage graph from ALL your repositories
  * tech stack neon pills
Standard library only. The hero images live in ./assets (3 files).

    GITHUB_TOKEN=xxxx python generate_profile.py     # live data
    python generate_profile.py --demo                # offline sample data
"""
import base64
import json
import math
import os
import sys
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

# ----------------------------------------------------------------------------
# CONFIG - edit this part only
# ----------------------------------------------------------------------------
USERNAME = os.environ.get("GITHUB_USER", "saptak-chaki")
NAME = "SAPTAK CHAKI"
KATAKANA = "サプタク・チャキ"
TITLE = "ASPIRING PYTHON FULL STACK DEVELOPER"
SUBTITLE = "B.Tech CSE  ·  IoT  ·  Cyber Security  ·  Blockchain"
STAMP = "速"
ABOUT_LINES = [
    "「ようこそ、俺のガレージへ！」 Welcome to my garage! I am Saptak Chaki, a B.Tech CSE",
    "student crafting powerful Python full-stack applications. I specialize in IoT,",
    "Cyber Security, and Blockchain — brewing secure, high-performance digital magic into every build.",
]
TECH = [
    "Python", "Django", "Flask / FastAPI", "HTML / CSS",
    "JavaScript", "React", "SQL / MySQL", "Git / GitHub",
    "Linux", "IoT", "Cyber Security", "Blockchain",
]
TECH_COLORS = ["#ff4fb8", "#22e5ff", "#4a8bff", "#ff4a5e",
               "#7cff3d", "#ff5a4a", "#ff4fb8", "#22b8e5",
               "#4a7bff", "#ff4a5e", "#7cff3d", "#ff4a5e"]
FOOTER = "TOYOTA AE86 TRUENO // 走れ、止まるな"
TOP_LANGS = 5          # languages shown in the graph (rest become "Other")
OUTPUT = "profile.svg"

# ----------------------------------------------------------------------------
# GitHub data  (unchanged from v3)
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
# Hero assets (./assets next to this script)
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
# crop offset + layer boxes inside the 1440px-wide hero image (see assets)
Y0 = 1187
ON_BOX = (0, 1539, 1018, 888)       # x, y, w, h  (lights-on overlay)
CAR_BOX = (0, 1407, 1440, 919)      # x, y, w, h  (vibrating car layer)
BASE_H = 621                        # displayed height of the base image
S = 3.4698795180722892              # source(415px) -> 1440px scale
K = 720 / 415
BH = 620                            # banner height
LIGHTS = [(47, 528, 34), (197, 542, 40), (46, 603, 26), (173, 625, 30)]
STREAKS = [(47, 528, 95), (197, 542, 120)]


def b64(name):
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        sys.exit(f"Missing asset: {path}  (upload the whole assets/ folder to the repo)")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def LY(y):
    return (y * S - Y0) * 0.5


# ----------------------------------------------------------------------------
# SVG pieces
# ----------------------------------------------------------------------------
LANG_COLORS = ["#ff3d9a", "#22d8ff", "#5b6bff", "#7cff3d", "#ff8a3d", "#ff4a5e"]

STYLE = """<style>
  .vib { animation: vib .14s steps(1,end) infinite; }
  @keyframes vib { 0%{transform:translate(0,0)} 20%{transform:translate(1.4px,-1px)} 40%{transform:translate(-1.2px,.8px)} 60%{transform:translate(.8px,1.2px)} 80%{transform:translate(-1px,-.6px)} }
  .blink { animation: blink 2.4s infinite; }
  @keyframes blink { 0%,38%{opacity:1} 40%,47%{opacity:0} 49%,61%{opacity:1} 63%,68%{opacity:0} 70%,100%{opacity:1} }
  .nf { animation: nf 5s infinite; }
  @keyframes nf { 0%,17%,23%,58%,100%{opacity:1} 19%{opacity:.5} 21%{opacity:.85} 60%{opacity:.65} 62%{opacity:1} }
  .barfill { transform-box: fill-box; transform-origin: left center; animation: grow 1.6s ease-out both; }
  @keyframes grow { from{transform:scaleX(0)} to{transform:scaleX(1)} }
</style>"""

DEFS = """<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0524"/><stop offset="0.5" stop-color="#1a0b45"/><stop offset="1" stop-color="#0c0630"/></linearGradient>
  <linearGradient id="frame" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22d8ff"/><stop offset="0.5" stop-color="#7a5cff"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient>
  <linearGradient id="cardGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b1260" stop-opacity="0.94"/><stop offset="1" stop-color="#2e0f58" stop-opacity="0.94"/></linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.10"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
  <linearGradient id="chrome" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="0.25" stop-color="#aab4e8"/><stop offset="0.5" stop-color="#2b2f63"/><stop offset="0.75" stop-color="#cdd5ff"/><stop offset="1" stop-color="#4a4f8a"/></linearGradient>
  <radialGradient id="dialRad" cx="0.42" cy="0.35" r="0.8"><stop offset="0" stop-color="#22329a"/><stop offset="0.55" stop-color="#0b0d3e"/><stop offset="1" stop-color="#02031a"/></radialGradient>
  <radialGradient id="bezelIn" cx="0.5" cy="0.5" r="0.5"><stop offset="0.8" stop-color="#05061f"/><stop offset="1" stop-color="#2a2f6a"/></radialGradient>
  <linearGradient id="glare" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.34"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
  <radialGradient id="alloy" cx="0.4" cy="0.35" r="0.8"><stop offset="0" stop-color="#f3f6ff"/><stop offset="0.5" stop-color="#8089c0"/><stop offset="1" stop-color="#262a62"/></radialGradient>
  <linearGradient id="spokeG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="0.5" stop-color="#9aa4de"/><stop offset="1" stop-color="#363b82"/></linearGradient>
  <radialGradient id="disc" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#3a3e70"/><stop offset="0.6" stop-color="#9aa2d4"/><stop offset="1" stop-color="#cfd5f5"/></radialGradient>
  <radialGradient id="ambC" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#22d8ff" stop-opacity="0.22"/><stop offset="1" stop-color="#22d8ff" stop-opacity="0"/></radialGradient>
  <radialGradient id="ambM" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ff3d9a" stop-opacity="0.22"/><stop offset="1" stop-color="#ff3d9a" stop-opacity="0"/></radialGradient>
  <radialGradient id="lglow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffffff" stop-opacity="0.95"/><stop offset="0.35" stop-color="#7fe9ff" stop-opacity="0.6"/><stop offset="1" stop-color="#22d8ff" stop-opacity="0"/></radialGradient>
  <linearGradient id="topFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e0626" stop-opacity="0.93"/><stop offset="0.6" stop-color="#0e0626" stop-opacity="0.55"/><stop offset="1" stop-color="#0e0626" stop-opacity="0"/></linearGradient>
  <linearGradient id="botFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0524" stop-opacity="0"/><stop offset="1" stop-color="#0d0524" stop-opacity="0.75"/></linearGradient>
  <radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.55" stop-color="#05010f" stop-opacity="0"/><stop offset="1" stop-color="#05010f" stop-opacity="0.6"/></radialGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.22"/></pattern>
  <filter id="neon" x="-40%" y="-60%" width="180%" height="220%"><feGaussianBlur in="SourceGraphic" stdDeviation="1.6" result="a"/><feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="glowS" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="a"/><feMerge><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="softblur" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="streak" x="-20%" y="-300%" width="140%" height="700%"><feGaussianBlur stdDeviation="1.8"/></filter>
  <clipPath id="bannerClip"><rect x="1" y="1" width="718" height="%BH2%" rx="22"/></clipPath>
  <clipPath id="rimClip"><circle r="80"/></clipPath>
</defs>""".replace("%BH2%", str(BH - 2))


def card(x, y, w, h, stroke="url(#frame)", fill="url(#cardGlass)"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="none" stroke="{stroke}" stroke-width="3.5" opacity="0.55" filter="url(#softblur)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>'
            f'<rect x="{x+1.5}" y="{y+1.5}" width="{w-3}" height="{h*0.45:.0f}" rx="16" fill="url(#sheen)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="url(#scan)" opacity="0.5"/>')


def pt(cx, cy, r, a):
    a = math.radians(a)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def arc(cx, cy, r, a0, a1):
    x0, y0 = pt(cx, cy, r, a0)
    x1, y1 = pt(cx, cy, r, a1)
    return f"M{x0:.2f} {y0:.2f} A{r} {r} 0 {1 if a1 - a0 > 180 else 0} 1 {x1:.2f} {y1:.2f}"


def gauge(cx, cy, color, val, label, labcol, target):
    f = min(1.0, val / target) if target else 0.0
    theta = -135 + 270 * f
    s = f'<ellipse cx="{cx}" cy="{cy+60}" rx="48" ry="6" fill="{color}" opacity="0.35" filter="url(#softblur)"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{color}" stroke-width="3" opacity="0.4" filter="url(#softblur)"/>'
    s += (f'<circle cx="{cx}" cy="{cy}" r="58" fill="url(#chrome)"/><circle cx="{cx}" cy="{cy}" r="54" fill="url(#bezelIn)"/>'
          f'<circle cx="{cx}" cy="{cy}" r="51" fill="url(#dialRad)"/>')
    s += f'<path d="{arc(cx,cy,41,135,405)}" fill="none" stroke="#ffffff" stroke-opacity="0.12" stroke-width="5" stroke-linecap="round"/>'
    if f > 0:
        s += f'<path d="{arc(cx,cy,41,135,135+270*f)}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linecap="round" filter="url(#neon)"/>'
    for i in range(28):
        a = 135 + 270 * i / 27
        major = i % 3 == 0
        x0, y0 = pt(cx, cy, 45 if major else 47, a)
        x1, y1 = pt(cx, cy, 51, a)
        lit = f > 0 and (i / 27) <= f
        s += (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{color if lit else "#ffffff"}" '
              f'stroke-opacity="{0.95 if lit else 0.4}" stroke-width="{1.8 if major else 1}"/>')
    sweep = max(theta, 70)
    s += (f'<g transform="translate({cx} {cy})"><g><animateTransform attributeName="transform" type="rotate" '
          f'values="-135;{sweep:.1f};{theta:.1f};{theta:.1f}" keyTimes="0;0.2;0.3;1" dur="5s" repeatCount="indefinite"/>'
          f'<path d="M0 -40 L2.8 -4 L0 8 L-2.8 -4 Z" fill="{color}" filter="url(#glowS)"/>'
          f'<path d="M0 -40 L0.9 -4 L0 6 Z" fill="#ffffff" opacity="0.55"/></g>'
          f'<circle r="6.5" fill="url(#chrome)" stroke="#05061f" stroke-width="1"/><circle r="2.4" fill="{color}"/></g>')
    s += f'<text x="{cx}" y="{cy+30}" font-size="15" font-weight="700" fill="#ffffff" text-anchor="middle" filter="url(#glowS)">{val}</text>'
    s += f'<ellipse cx="{cx-14}" cy="{cy-27}" rx="31" ry="14" transform="rotate(-28 {cx-14} {cy-27})" fill="url(#glare)"/>'
    s += f'<path d="{arc(cx,cy,56,205,290)}" fill="none" stroke="#ffffff" stroke-opacity="0.6" stroke-width="1.4" stroke-linecap="round"/>'
    s += f'<text x="{cx}" y="{cy+81}" font-size="10" font-weight="700" fill="{labcol}" text-anchor="middle" letter-spacing="1" filter="url(#glowS)">{label}</text>'
    return s


def spokes():
    s = ""
    for i in range(10):
        s += (f'<g transform="rotate({36*i})"><path d="M-5 -13 L-9.6 -62 Q0 -66 9.6 -62 L5 -13 Z" fill="url(#spokeG)" '
              f'stroke="#ffffff" stroke-opacity="0.35" stroke-width="0.7"/>'
              f'<line x1="0" y1="-19" x2="0" y2="-57" stroke="#0b0a26" stroke-opacity="0.45" stroke-width="1.6"/></g>')
    return s


def build_svg(st):
    base = b64("hi_base.jpg")
    on = b64("hi_on.webp")
    car = b64("hi_car.webp")

    # ---- layout ----
    n_about = len(ABOUT_LINES)
    ABOUT_Y = BH + 16
    ABOUT_H = 52 + 18 * (n_about - 1) + 18
    DASH_Y = ABOUT_Y + ABOUT_H + 16
    DASH_H = 205
    RIM_Y = DASH_Y + DASH_H + 16
    RIM_H = 262
    trows = (len(TECH) + 3) // 4
    TECH_Y = RIM_Y + RIM_H + 16
    TECH_H = 51 + 38 * (trows - 1) + 30 + 18
    FOOT_Y = TECH_Y + TECH_H + 28
    TOTAL = FOOT_Y + 14

    # ---- banner ----
    glows = "".join(f'<circle cx="{x*K:.1f}" cy="{LY(y):.1f}" r="{r*K*0.9:.1f}" fill="url(#lglow)"/>' for x, y, r in LIGHTS)
    streaks = "".join(f'<ellipse cx="{x*K:.1f}" cy="{LY(y):.1f}" rx="{rx}" ry="2.2" fill="#d8fbff" opacity="0.85" filter="url(#streak)"/>' for x, y, rx in STREAKS)
    cx0, cy0, cw, ch = CAR_BOX
    ox, oy, ow, oh = ON_BOX
    banner = f'''<g clip-path="url(#bannerClip)">
  <rect width="720" height="{BH}" fill="#1b0a45"/>
  <image href="data:image/jpeg;base64,{base}" x="0" y="0" width="720" height="{BASE_H}" preserveAspectRatio="none"/>
  <g class="vib">
    <image href="data:image/webp;base64,{car}" x="{cx0*0.5:.1f}" y="{(cy0-Y0)*0.5:.1f}" width="{cw*0.5:.1f}" height="{ch*0.5:.1f}" preserveAspectRatio="none"/>
    <g class="blink">
      <image href="data:image/webp;base64,{on}" x="{ox*0.5:.1f}" y="{(oy-Y0)*0.5:.1f}" width="{ow*0.5:.1f}" height="{oh*0.5:.1f}" preserveAspectRatio="none"/>
      {glows}{streaks}
    </g>
  </g>
  <rect width="720" height="{BH}" fill="url(#vig)"/>
  <rect x="0" y="{BH-90}" width="720" height="90" fill="url(#botFade)"/>
  <rect x="0" y="0" width="720" height="230" fill="url(#topFade)"/>
  <g class="nf" filter="url(#neon)">
    <text x="36" y="86" font-size="54" font-weight="900" font-style="italic" fill="#e6f8ff" stroke="#3b7bff" stroke-width="1.6" letter-spacing="1">{escape(NAME)}</text>
  </g>
  <text x="36" y="117" font-size="22" font-weight="700" fill="#ff66b3" letter-spacing="3" filter="url(#neon)">{escape(KATAKANA)}</text>
  <text x="36" y="143" font-size="12.5" font-weight="700" fill="#22d8ff" letter-spacing="3" filter="url(#glowS)">{escape(TITLE)}</text>
  <text x="38" y="163" font-size="10.5" fill="#ffffff" letter-spacing="2.4">{escape(SUBTITLE)}</text>
  <g transform="rotate(-6 652 44)" filter="url(#glowS)">
    <rect x="632" y="26" width="42" height="40" rx="4" fill="#e8213a" stroke="#ffffff" stroke-width="2"/>
    <text x="653" y="56" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle">{escape(STAMP)}</text>
  </g>
</g>
<rect x="1" y="1" width="718" height="{BH-2}" rx="22" fill="none" stroke="url(#frame)" stroke-width="2.2" filter="url(#glowS)"/>'''

    # ---- about ----
    about = (card(22, ABOUT_Y, 676, ABOUT_H) +
             f'<text x="684" y="{ABOUT_Y+36}" font-size="32" fill="#ff66b3" opacity="0.3" text-anchor="end" filter="url(#glowS)">侍</text>'
             f'<text x="42" y="{ABOUT_Y+26}" font-size="14" font-weight="700" letter-spacing="1.5" filter="url(#glowS)"><tspan fill="#ff66b3">// 運転手について ——</tspan><tspan fill="#8aeaff"> ABOUT THE DRIVER</tspan></text>' +
             '<g fill="#ffffff" font-size="10.5" font-weight="500">' +
             "".join(f'<text x="42" y="{ABOUT_Y+52+18*i}">{escape(ln)}</text>' for i, ln in enumerate(ABOUT_LINES)) + "</g>")

    # ---- dashboard ----
    gcy = DASH_Y + 100
    dash = (card(22, DASH_Y, 676, DASH_H) +
            f'<text x="42" y="{DASH_Y+28}" font-size="14" font-weight="700" letter-spacing="1.5" filter="url(#glowS)"><tspan fill="#ff66b3">// ダッシュボード ——</tspan><tspan fill="#8aeaff"> DASHBOARD</tspan></text>' +
            gauge(107, gcy, "#ff3d9a", st["commits"], "COMMITS · コミット", "#ff66b3", max(100, st["commits"] * 1.5)) +
            gauge(276, gcy, "#22d8ff", st["repos"], "REPOS · リポジトリ", "#8aeaff", max(10, st["repos"] * 1.5)) +
            gauge(445, gcy, "#d4ff3a", st["stars"], "STARS · スター", "#d4ff3a", max(10, st["stars"] * 1.5)) +
            gauge(614, gcy, "#ff4a5e", st["streak"], "STREAK · ストリーク", "#ff7a88", max(14, st["streak"] * 1.5)))

    # ---- rim + languages ----
    langs = st["langs"] or [("No code yet", 100.0)]
    RCX, RCY = 180, RIM_Y + 142
    circ = 2 * math.pi * 92
    donut, off = "", 0.0
    for i, (n, p) in enumerate(langs):
        L = circ * p / 100
        donut += f'<circle r="92" fill="none" stroke="{LANG_COLORS[i % len(LANG_COLORS)]}" stroke-width="13" stroke-dasharray="{max(L-1.2,0.5):.1f} {circ:.1f}" stroke-dashoffset="{-off:.1f}"/>'
        off += L
    rot = '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" repeatCount="indefinite"/>'
    lugs = "".join(f'<circle cx="{14*math.cos(math.radians(72*i)):.1f}" cy="{14*math.sin(math.radians(72*i)):.1f}" r="2.2"/>' for i in range(5))
    rim = (card(22, RIM_Y, 676, RIM_H) +
           f'<text x="42" y="{RIM_Y+30}" font-size="14" font-weight="700" letter-spacing="1.5" filter="url(#glowS)"><tspan fill="#ff66b3">// リム ——</tspan><tspan fill="#8aeaff"> RIM // LANGUAGE MIX 言語</tspan></text>'
           f'<g transform="translate({RCX} {RCY})">'
           f'<circle r="108" fill="url(#ambM)"/>'
           f'<ellipse cx="0" cy="104" rx="82" ry="8" fill="#22d8ff" opacity="0.4" filter="url(#softblur)"/>'
           f'<g>{rot}<circle r="92" fill="none" stroke="#140c4a" stroke-width="16"/>'
           f'<g transform="rotate(-90)" filter="url(#neon)">{donut}</g>'
           f'<circle r="80" fill="#06041a" stroke="#30306a" stroke-width="1.2"/>'
           f'<circle r="77.5" fill="none" stroke="#1b1a45" stroke-width="5" stroke-dasharray="2.5 4"/>'
           f'<circle r="70" fill="url(#alloy)"/><circle r="62" fill="#090722"/>'
           f'<circle r="47" fill="url(#disc)"/><circle r="41" fill="none" stroke="#1a1d45" stroke-width="5" stroke-dasharray="5 5" stroke-opacity="0.8"/></g>'
           f'<path d="{arc(0,0,44,-30,35)}" fill="none" stroke="#ff2a3a" stroke-width="11" stroke-linecap="round" filter="url(#glowS)"/>'
           f'<path d="{arc(0,0,44,-24,28)}" fill="none" stroke="#ff8a8a" stroke-opacity="0.55" stroke-width="2.5" stroke-linecap="round"/>'
           f'<g>{rot}{spokes()}<circle r="17" fill="url(#chrome)" stroke="#0b0a26"/><circle r="11" fill="#0f0c36"/>'
           f'<g fill="url(#chrome)">{lugs}</g><circle r="3.6" fill="#ff3d9a" filter="url(#glowS)"/></g>'
           f'<g clip-path="url(#rimClip)"><ellipse cx="-26" cy="-38" rx="58" ry="24" transform="rotate(-35 -26 -38)" fill="url(#glare)"/></g>'
           f'<path d="{arc(0,0,76,200,285)}" fill="none" stroke="#ffffff" stroke-opacity="0.45" stroke-width="1.6" stroke-linecap="round"/>'
           f'<circle r="101" fill="none" stroke="url(#frame)" stroke-opacity="0.4" stroke-width="1"/></g>')
    n = len(langs)
    sp = min(46, 150 / (n - 1)) if n > 1 else 46
    lang = ""
    for i, (nm, p) in enumerate(langs):
        yb = RIM_Y + 86 + sp * i
        c = LANG_COLORS[i % len(LANG_COLORS)]
        w = max(2.0, 1.62 * p)
        lang += (f'<rect x="361" y="{yb-11:.1f}" width="12" height="12" rx="2" fill="{c}" filter="url(#glowS)"/>'
                 f'<text x="381" y="{yb:.1f}" font-size="15" font-weight="700" fill="#ffffff">{escape(nm)}</text>'
                 f'<rect x="468" y="{yb-9:.1f}" width="162" height="9" rx="4.5" fill="#0a0830" stroke="#ffffff" stroke-opacity="0.1"/>'
                 f'<rect class="barfill" x="468" y="{yb-9:.1f}" width="{w:.1f}" height="9" rx="4.5" fill="{c}" filter="url(#neon)" style="animation-delay:{i*0.2:.1f}s"/>'
                 f'<text x="680" y="{yb:.1f}" font-size="12" font-weight="700" fill="{c}" text-anchor="end" filter="url(#glowS)">{p:.1f}%</text>')

    # ---- tech ----
    cols = [42, 204, 366, 528]
    pills = ""
    for i, t in enumerate(TECH):
        x = cols[i % 4]
        y = TECH_Y + 51 + 38 * (i // 4)
        c = TECH_COLORS[i % len(TECH_COLORS)]
        pills += (f'<g class="nf" style="animation-duration:{4+(i%5)*1.3:.1f}s;animation-delay:{i*0.37:.2f}s">'
                  f'<rect x="{x}" y="{y}" width="150" height="30" rx="15" fill="none" stroke="{c}" stroke-width="3.5" opacity="0.6" filter="url(#softblur)"/>'
                  f'<rect x="{x}" y="{y}" width="150" height="30" rx="15" fill="#120b3a" stroke="{c}" stroke-width="1.8"/>'
                  f'<rect x="{x+3}" y="{y+2}" width="144" height="13" rx="6.5" fill="url(#sheen)"/>'
                  f'<text x="{x+75}" y="{y+20}" font-size="12" font-weight="800" fill="#ffffff" text-anchor="middle" filter="url(#glowS)">{escape(t)}</text></g>')
    tech = (card(22, TECH_Y, 676, TECH_H, stroke="#ff8a3d", fill="#120a36") +
            f'<text x="42" y="{TECH_Y+33}" font-size="17" font-weight="900" fill="#ff8a3d" letter-spacing="3.5" filter="url(#neon)">GARAGE // TECH STACK</text>' + pills)

    foot = f'<text x="360" y="{FOOT_Y}" font-size="8" fill="#8f9be0" text-anchor="middle" letter-spacing="1.2">© {date.today().year} {escape(KATAKANA)} // {escape(FOOTER)}</text>'
    ambient = (f'<circle cx="40" cy="{ABOUT_Y+60}" r="260" fill="url(#ambC)"/><circle cx="700" cy="{DASH_Y+80}" r="280" fill="url(#ambM)"/>'
               f'<circle cx="60" cy="{RIM_Y+160}" r="260" fill="url(#ambC)"/><circle cx="690" cy="{TECH_Y+60}" r="260" fill="url(#ambM)"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 {TOTAL}" width="720" height="{TOTAL}" '
            f'font-family="\'Orbitron\',\'Rajdhani\',\'Noto Sans JP\',\'Hiragino Sans\',\'Yu Gothic\',Arial,sans-serif">\n'
            f'<title>{escape(NAME)} - Neon Garage Profile</title>\n{DEFS}\n{STYLE}\n'
            f'<rect width="720" height="{TOTAL}" fill="url(#bg)"/>\n{ambient}\n{banner}\n{about}\n{dash}\n{rim}\n{lang}\n{tech}\n{foot}\n</svg>\n')


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
