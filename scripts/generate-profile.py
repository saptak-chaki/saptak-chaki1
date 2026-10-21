#!/usr/bin/env python3
"""
generate_profile.py  -  builds profile.svg for the saptak-chaki GitHub profile README.

* Pulls live numbers (commits, repositories, stars, streak) from the GitHub GraphQL API.
* Draws a Halloween banner with realistic 3D-style pumpkins that float, sway and turn.
* No third-party packages needed (standard library only).

Usage:
    GITHUB_TOKEN=xxxx python generate_profile.py          # live stats
    python generate_profile.py --demo                      # offline sample numbers
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

# ----------------------------------------------------------------------------
# CONFIG - edit this part only
# ----------------------------------------------------------------------------
USERNAME = os.environ.get("GITHUB_USER", "saptak-chaki")
NAME = "SAPTAK CHAKI"
TITLE = "ASPIRING PYTHON FULL STACK DEVELOPER"
SUBTITLE = "B.Tech CSE · IoT · Cyber Security · Blockchain"
ABOUT_LINES = [
    "Welcome to my Halloween lair! I am Saptak Chaki, a B.Tech",
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
OUTPUT = "profile.svg"
W = 980

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
            totalCount nodes{ stargazerCount } } } }"""
    u = gql(q1, {"login": USERNAME}, token)["user"]
    years = u["contributionsCollection"]["contributionYears"]
    repos = u["repositories"]["totalCount"]
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])

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

    # current streak (today may still be empty)
    streak, cur = 0, date.today()
    if days.get(cur.isoformat(), 0) == 0:
        cur -= timedelta(days=1)
    while days.get(cur.isoformat(), 0) > 0:
        streak += 1
        cur -= timedelta(days=1)
    return {"commits": commits, "repos": repos, "stars": stars, "streak": streak}


# ----------------------------------------------------------------------------
# SVG parts
# ----------------------------------------------------------------------------
DEFS = r"""
<defs>
  <radialGradient id="bgG" cx="50%" cy="38%" r="80%">
    <stop offset="0" stop-color="#2b1309"/><stop offset=".55" stop-color="#130a07"/><stop offset="1" stop-color="#050303"/>
  </radialGradient>
  <radialGradient id="moonG" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#ffb347" stop-opacity=".32"/><stop offset="1" stop-color="#ff6a00" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="fogG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ff7a1a" stop-opacity="0"/><stop offset="1" stop-color="#ff7a1a" stop-opacity=".14"/>
  </linearGradient>

  <!-- pumpkin skin -->
  <radialGradient id="lobe" cx="36%" cy="28%" r="85%">
    <stop offset="0" stop-color="#ffc067"/><stop offset=".28" stop-color="#ff8f24"/>
    <stop offset=".65" stop-color="#d9480f"/><stop offset="1" stop-color="#5c1a03"/>
  </radialGradient>
  <radialGradient id="lobeSide" cx="28%" cy="30%" r="95%">
    <stop offset="0" stop-color="#ff9c33"/><stop offset=".55" stop-color="#bf3f0a"/><stop offset="1" stop-color="#4a1402"/>
  </radialGradient>
  <linearGradient id="stemG" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#3a5518"/><stop offset=".45" stop-color="#8aa83a"/><stop offset="1" stop-color="#26380d"/>
  </linearGradient>
  <radialGradient id="faceG" cx="50%" cy="55%" r="65%">
    <stop offset="0" stop-color="#fff6b0"/><stop offset=".55" stop-color="#ffc936"/><stop offset="1" stop-color="#ff7a00"/>
  </radialGradient>
  <radialGradient id="spill" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#ffb02e" stop-opacity=".55"/><stop offset="1" stop-color="#ff6a00" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="shadowG" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#000" stop-opacity=".75"/><stop offset="1" stop-color="#000" stop-opacity="0"/>
  </radialGradient>

  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>
  <filter id="softer" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.4"/></filter>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="dofA" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="dofB" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4.5"/></filter>
  <!-- bumpy pumpkin skin -->
  <filter id="skin" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.06 0.012" numOctaves="4" seed="8" result="n"/>
    <feDiffuseLighting in="n" lighting-color="#fff" surfaceScale="1.6" diffuseConstant="1.1" result="l">
      <feDistantLight azimuth="225" elevation="62"/>
    </feDiffuseLighting>
    <feComponentTransfer in="l" result="l2"><feFuncR type="linear" slope="1.2"/><feFuncG type="linear" slope="1.2"/><feFuncB type="linear" slope="1.2"/></feComponentTransfer>
    <feComposite in="l2" in2="SourceAlpha" operator="in" result="lc"/>
    <feBlend in="SourceGraphic" in2="lc" mode="multiply"/>
  </filter>
  <filter id="cardGlow" x="-5%" y="-10%" width="110%" height="120%">
    <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>

  <!-- ===== one realistic 3D pumpkin (200 x 190 box, centre 100,100) ===== -->
  <g id="pk">
    <g filter="url(#skin)">
      <ellipse cx="30"  cy="106" rx="28" ry="56" fill="url(#lobeSide)" stroke="#4a1402" stroke-width="2"/>
      <ellipse cx="170" cy="106" rx="28" ry="56" fill="url(#lobeSide)" stroke="#4a1402" stroke-width="2"/>
      <ellipse cx="52"  cy="104" rx="34" ry="64" fill="url(#lobeSide)" stroke="#5c1a03" stroke-width="2"/>
      <ellipse cx="148" cy="104" rx="34" ry="64" fill="url(#lobeSide)" stroke="#5c1a03" stroke-width="2"/>
      <ellipse cx="74"  cy="102" rx="38" ry="70" fill="url(#lobe)" stroke="#6f2004" stroke-width="2"/>
      <ellipse cx="126" cy="102" rx="38" ry="70" fill="url(#lobe)" stroke="#6f2004" stroke-width="2"/>
      <ellipse cx="100" cy="100" rx="40" ry="74" fill="url(#lobe)" stroke="#7a2504" stroke-width="2"/>
    </g>
    <!-- turning ribs and creases (shift left/right = the pumpkin appears to rotate) -->
    <g class="turn">
      <g fill="none" stroke="#2e0b00" stroke-linecap="round" filter="url(#softer)">
        <path d="M58 40 C38 80 38 130 58 168" stroke-width="4" opacity=".6"/>
        <path d="M142 40 C162 80 162 130 142 168" stroke-width="4" opacity=".6"/>
        <path d="M30 56 C14 86 14 126 30 156" stroke-width="3.5" opacity=".5"/>
        <path d="M170 56 C186 86 186 126 170 156" stroke-width="3.5" opacity=".5"/>
        <path d="M100 30 C84 70 84 132 100 172" stroke-width="2.4" opacity=".28"/>
      </g>
    </g>
    <!-- light and shade -->
    <g class="spec">
      <ellipse cx="76" cy="58" rx="15" ry="28" fill="#fff" opacity=".3" filter="url(#soft)" transform="rotate(-18 76 58)"/>
      <ellipse cx="40" cy="84" rx="7" ry="20" fill="#fff" opacity=".17" filter="url(#soft)"/>
      <ellipse cx="150" cy="70" rx="5" ry="26" fill="#ffd9a0" opacity=".25" filter="url(#soft)"/>
    </g>
    <ellipse cx="100" cy="158" rx="52" ry="18" fill="#2a0800" opacity=".3" filter="url(#soft)"/>
    <path d="M26 150 C60 176 140 176 174 150" fill="none" stroke="#ff9a2e" stroke-width="3" opacity=".22" filter="url(#softer)"/>
    <!-- stem -->
    <path d="M88 42 C86 26 90 14 99 6 C110 14 114 26 112 42 C106 47 94 47 88 42 Z" fill="url(#stemG)" stroke="#223208" stroke-width="1.6"/>
    <path d="M92 38 C92 28 94 20 98 14" fill="none" stroke="#c4dc72" stroke-width="2" opacity=".5" stroke-linecap="round"/>
    <path d="M99 6 C108 -2 118 0 121 8" fill="none" stroke="#4d6c1f" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M88 42 C96 50 104 50 112 42" fill="none" stroke="#2a1405" stroke-width="2" opacity=".7"/>
    <!-- carved face with inner glow -->
    <g class="turn face">
      <ellipse cx="100" cy="110" rx="46" ry="38" fill="url(#spill)" filter="url(#soft)"/>
      <g fill="#2a0a00">
        <path d="M64 84 L90 77 L85 103 Z"/><path d="M136 84 L110 77 L115 103 Z"/>
        <path d="M100 98 L91 117 L109 117 Z"/>
        <path d="M60 121 L74 135 L83 124 L92 140 L100 127 L108 140 L117 124 L126 135 L140 121 C128 156 72 156 60 121 Z"/>
      </g>
      <g filter="url(#glow)">
        <path d="M68 86 L88 80 L84 99 Z" fill="url(#faceG)"/>
        <path d="M132 86 L112 80 L116 99 Z" fill="url(#faceG)"/>
        <path d="M100 101 L94 114 L106 114 Z" fill="url(#faceG)"/>
        <path d="M65 123 L76 133 L84 125 L92 137 L100 128 L108 137 L116 125 L124 133 L135 123 C125 151 75 151 65 123 Z" fill="url(#faceG)"/>
      </g>
    </g>
  </g>
</defs>
"""

STYLE = """<style>
.bobA{animation:bobA 6.5s ease-in-out infinite;animation-delay:var(--d,0s)}
.bobB{animation:bobB 8s ease-in-out infinite;animation-delay:var(--d,0s)}
.bobC{animation:bobC 10s ease-in-out infinite;animation-delay:var(--d,0s)}
@keyframes bobA{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-20px) rotate(3deg)}}
@keyframes bobB{0%,100%{transform:translateY(-6px) rotate(4deg)}50%{transform:translateY(12px) rotate(-4deg)}}
@keyframes bobC{0%,100%{transform:translateY(8px) rotate(-5deg)}50%{transform:translateY(-12px) rotate(5deg)}}
.turn{animation:turn 8s ease-in-out infinite alternate;animation-delay:var(--d,0s)}
@keyframes turn{from{transform:translateX(-11px)}to{transform:translateX(11px)}}
.spec{animation:spec 8s ease-in-out infinite alternate;animation-delay:var(--d,0s)}
@keyframes spec{from{transform:translateX(5px)}to{transform:translateX(-5px)}}
.face{animation:turn 8s ease-in-out infinite alternate,flick 2.7s ease-in-out infinite;animation-delay:var(--d,0s),0s}
@keyframes flick{0%,100%{opacity:1}28%{opacity:.8}46%{opacity:1}72%{opacity:.88}}
.gs{animation:gs 6.5s ease-in-out infinite;animation-delay:var(--d,0s);transform-box:fill-box;transform-origin:50% 50%}
@keyframes gs{0%,100%{transform:scale(1);opacity:.9}50%{transform:scale(.8);opacity:.55}}
.ember{animation:rise linear infinite}
@keyframes rise{0%{transform:translateY(0) translateX(0);opacity:0}12%{opacity:.95}100%{transform:translateY(-520px) translateX(24px);opacity:0}}
.bat{animation:fly 16s linear infinite}
@keyframes fly{0%{transform:translateX(-60px)}100%{transform:translateX(1060px)}}
.flap{animation:flap .45s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:50% 60%}
@keyframes flap{from{transform:scaleY(1)}to{transform:scaleY(.4)}}
.num{animation:pop 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 50%}
@keyframes pop{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>"""

H_FONT = "Impact,Haettenschweiler,'Arial Narrow Bold','Franklin Gothic Heavy',sans-serif"
M_FONT = "'Courier New',Courier,monospace"
S_FONT = "Georgia,'Times New Roman',serif"


def pumpkin(x, y, s, anim, delay, blur=None, opacity=1.0, flip=False):
    f = f' filter="url(#{blur})"' if blur else ""
    sx = -s if flip else s
    return (
        f'<g opacity="{opacity}"{f}><g transform="translate({x} {y})">'
        f'<ellipse class="gs" style="--d:{delay}s" cx="0" cy="{88*s:.1f}" rx="{84*s:.1f}" ry="{14*s:.1f}" fill="url(#shadowG)"/>'
        f'<g transform="scale({sx} {s})"><g class="{anim}" style="--d:{delay}s;transform-box:fill-box;transform-origin:50% 100%">'
        f'<g transform="translate(-100 -100)"><use xlink:href="#pk"/></g></g></g></g></g>'
    )


def card(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="#0b0604" fill-opacity=".5" '
            f'stroke="#ff3b1f" stroke-width="1.8" filter="url(#cardGlow)"/>')


def build_svg(st):
    parts = []
    # --- layout ---
    cx, cw = 70, W - 140
    y_head, h_head = 40, 190
    y_about, h_about = 260, 220
    y_stats, h_stats = 510, 255
    y_tech, h_tech = 790, 345
    H = y_tech + h_tech + 50

    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
                 f'aria-label="Saptak Chaki - Halloween profile">')
    parts.append(STYLE)
    parts.append(DEFS)
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#bgG)"/>')
    parts.append(f'<circle cx="{W/2}" cy="260" r="330" fill="url(#moonG)"/>')
    parts.append(f'<rect y="{H-320}" width="{W}" height="320" fill="url(#fogG)"/>')

    # --- background pumpkins (far, blurred) ---
    parts.append(pumpkin(215, 150, .75, "bobC", 1, "dofB", .6))
    parts.append(pumpkin(770, 140, .8, "bobB", 3, "dofB", .6))
    parts.append(pumpkin(780, 395, .85, "bobC", 5, "dofB", .55))
    parts.append(pumpkin(190, 640, .8, "bobB", 2, "dofA", .6))
    parts.append(pumpkin(500, 900, .9, "bobC", 6, "dofB", .5))
    parts.append(pumpkin(840, 960, .7, "bobB", 4, "dofA", .55, True))
    # embers
    import random
    rnd = random.Random(7)
    for _ in range(36):
        parts.append(
            f'<circle class="ember" cx="{rnd.randint(10, W-10)}" cy="{rnd.randint(int(H*.5), H)}" '
            f'r="{rnd.choice([1.1, 1.6, 2.2, 2.8])}" fill="#ffa43a" '
            f'style="animation-duration:{rnd.randint(7, 15)}s;animation-delay:-{rnd.randint(0, 14)}s"/>')
    # bats
    for i, (by, dl) in enumerate([(110, -3), (640, -10)]):
        parts.append(
            f'<g class="bat" style="animation-delay:{dl}s"><g transform="translate(0 {by})"><g class="flap">'
            '<path d="M0 0C-9-10-22-8-30 2C-22 0-18 4-14 8C-10 2-4 4 0 9C4 4 10 2 14 8C18 4 22 0 30 2C22-8 9-10 0 0Z" fill="#0a0606"/>'
            '</g></g></g>')

    # --- header card ---
    parts.append(card(cx, y_head, cw, h_head))
    mx = W / 2
    parts.append(f'<text x="{mx}" y="{y_head+78}" text-anchor="middle" font-family="{H_FONT}" font-size="62" '
                 f'fill="#ff8a1f" stroke="#7a2504" stroke-width="1.2" letter-spacing="2" filter="url(#glow)">{escape(NAME)}</text>')
    parts.append(f'<text x="{mx}" y="{y_head+122}" text-anchor="middle" font-family="{M_FONT}" font-weight="700" '
                 f'font-size="19" fill="#ffd36a" letter-spacing="2.5">\U0001F383 {escape(TITLE)} \U0001F383</text>')
    parts.append(f'<text x="{mx}" y="{y_head+158}" text-anchor="middle" font-family="{S_FONT}" font-style="italic" '
                 f'font-size="18" fill="#cfe3ff">{escape(SUBTITLE)}</text>')

    # --- about card ---
    parts.append(card(cx, y_about, cw, h_about))
    parts.append(f'<text x="{cx+36}" y="{y_about+48}" font-family="{H_FONT}" font-size="28" fill="#ffb02e" '
                 f'letter-spacing="1">\U0001F578 ABOUT THE SPELLBINDER</text>')
    for i, line in enumerate(ABOUT_LINES):
        parts.append(f'<text x="{cx+36}" y="{y_about+92+i*30}" font-family="{M_FONT}" font-weight="700" '
                     f'font-size="17" fill="#f3e9dc">{escape(line)}</text>')

    # --- stats card ---
    parts.append(card(cx, y_stats, cw, h_stats))
    parts.append(f'<text x="{mx}" y="{y_stats+48}" text-anchor="middle" font-family="{H_FONT}" font-size="28" '
                 f'fill="#ff5a2a" letter-spacing="1.5">\U0001F383 HALLOWEEN STATS &amp; STREAK \U0001F383</text>')
    items = [(st["commits"], "COMMITS"), (st["repos"], "REPOSITORIES"),
             (f'{st["stars"]} / {st["streak"]}', "STARS / STREAK")]
    for i, (val, label) in enumerate(items):
        gx = cx + cw * (i + .5) / 3
        parts.append(pumpkin(round(gx, 1), y_stats + 112, .56, ["bobA", "bobB", "bobC"][i], i * 2))
        parts.append(f'<text class="num" x="{gx:.1f}" y="{y_stats+200}" text-anchor="middle" font-family="{H_FONT}" '
                     f'font-size="34" fill="#fff4d6" stroke="#5c1a03" stroke-width="1.2">{escape(str(val))}</text>')
        parts.append(f'<text x="{gx:.1f}" y="{y_stats+231}" text-anchor="middle" font-family="{M_FONT}" font-size="14" '
                     f'fill="#ff7a3c" letter-spacing="2">{label}</text>')

    # --- tech card ---
    parts.append(card(cx, y_tech, cw, h_tech))
    parts.append(f'<text x="{cx+36}" y="{y_tech+50}" font-family="{H_FONT}" font-size="28" fill="#ffb02e" '
                 f'letter-spacing="1">\U0001F52E WITCH’S TECH BREW</text>')
    pw, ph, gap = 232, 52, 20
    px0 = cx + (cw - (3 * pw + 2 * gap)) / 2
    for i, name in enumerate(TECH):
        r, c = divmod(i, 3)
        x = px0 + c * (pw + gap)
        y = y_tech + 78 + r * (ph + 16)
        hot = (r + c) % 2 == 0
        fill = "#16164a" if hot else "#0d1424"
        stroke = "#ff6a2a" if hot else "#35506e"
        tcol = "#ffd36a" if hot else "#e8eefc"
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{pw}" height="{ph}" rx="14" fill="{fill}" '
                     f'stroke="{stroke}" stroke-width="{2 if hot else 1.2}"/>')
        parts.append(f'<text x="{x+pw/2:.1f}" y="{y+ph/2+6}" text-anchor="middle" font-family="{M_FONT}" '
                     f'font-weight="700" font-size="17" fill="{tcol}">{escape(name)}</text>')

    # --- foreground pumpkins (near, sharp, overlap the card edges) ---
    parts.append(pumpkin(58, 520, .62, "bobA", 0))
    parts.append(pumpkin(W - 58, 470, .58, "bobB", 2, flip=True))
    parts.append(pumpkin(70, H - 90, .5, "bobB", 4))
    parts.append(pumpkin(W - 70, H - 80, .55, "bobA", 1, flip=True))

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if "--demo" in sys.argv:
        stats = {"commits": 11, "repos": 2, "stars": 0, "streak": 0}
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GITHUB_TOKEN (or run with --demo).")
        stats = fetch_stats(token)
    svg = build_svg(stats)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUTPUT} written ({len(svg)//1024} KB) - {stats} - {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main()
