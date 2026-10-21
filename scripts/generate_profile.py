#!/usr/bin/env python3
"""Black & white profile with white 3D pumpkins, black blood, live GitHub stats.
Pure code: NO image files needed. Writes ../profile.svg"""
import os, json, random, datetime, urllib.request
from html import escape

USER = os.environ.get("GH_USER", "saptak-chaki")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile.svg")

# ---------------------------------------------------------------- LIVE DATA
def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

def fetch_stats():
    if not TOKEN:
        print("No token -> SAMPLE data")
        return dict(commits=32, repos=3, stars=0, streak=2,
                    langs=[("Python", 46), ("Java", 22), ("HTML", 14), ("JavaScript", 9), ("CSS", 5), ("Other", 4)])
    u = gql("""query($u:String!){ user(login:$u){ createdAt
      repositories(ownerAffiliations:OWNER, first:100){ totalCount
        nodes{ isFork stargazerCount
          languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } } } }""",
        {"u": USER})["user"]
    repos = u["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    langs = {}
    for n in repos["nodes"]:
        if n["isFork"]:
            continue
        for e in n["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    top = [(k, round(v * 100 / total)) for k, v in ranked[:6]]
    rest = 100 - sum(p for _, p in top)
    if rest > 0 and len(ranked) > 6:
        top.append(("Other", rest))
    created = datetime.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    commits, days = 0, {}
    for y in range(created.year, now.year + 1):
        a = max(created, datetime.datetime(y, 1, 1, tzinfo=datetime.timezone.utc))
        b = min(now, datetime.datetime(y, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc))
        c = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){ user(login:$u){ contributionsCollection(from:$f,to:$t){
              totalCommitContributions restrictedContributionsCount
              contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }""",
                {"u": USER, "f": a.isoformat(), "t": b.isoformat()})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    streak, day = 0, now.date()
    if days.get(day.isoformat(), 0) == 0:
        day -= datetime.timedelta(days=1)
    while days.get(day.isoformat(), 0) > 0:
        streak += 1
        day -= datetime.timedelta(days=1)
    return dict(commits=commits, repos=repos["totalCount"], stars=stars, streak=streak, langs=top)

# ---------------------------------------------------------------- SVG PARTS
W, H = 1000, 1600
MONO = "'Courier New',Courier,monospace"
HEAD = "Impact,Haettenschweiler,'Arial Narrow Bold',sans-serif"

# white 3D pumpkin, drawn with pure vector shapes (centered on 0,0, ~200 wide)
PUMPKIN = '''<g id="pk">
<ellipse cx="-56" cy="10" rx="44" ry="72" fill="url(#pg2)" stroke="#555" stroke-width="1.6"/>
<ellipse cx="56" cy="10" rx="44" ry="72" fill="url(#pg2)" stroke="#555" stroke-width="1.6"/>
<ellipse cx="-28" cy="8" rx="44" ry="80" fill="url(#pg)" stroke="#666" stroke-width="1.4"/>
<ellipse cx="28" cy="8" rx="44" ry="80" fill="url(#pg)" stroke="#666" stroke-width="1.4"/>
<ellipse cx="0" cy="8" rx="40" ry="84" fill="url(#pg)" stroke="#777" stroke-width="1.2"/>
<path d="M-8,-70 C-10,-92 4,-102 18,-99 C10,-92 13,-82 9,-70 Z" fill="url(#pst)" stroke="#000" stroke-width="1"/>
<polygon points="-70,-38 -12,-8 -62,-10" fill="#050505"/>
<polygon points="70,-38 12,-8 62,-10" fill="#050505"/>
<polygon points="0,6 -9,22 9,22" fill="#050505"/>
<polygon points="-70,28 -52,42 -40,35 -26,52 -12,42 0,56 12,42 26,52 40,35 52,42 70,28 62,58 46,68 30,60 14,72 0,62 -14,72 -30,60 -46,68 -62,58" fill="#050505"/>
<g fill="#000"><rect x="-44" y="62" width="7" height="26" rx="3.5"/><circle cx="-40.5" cy="90" r="5"/>
<rect x="-6" y="68" width="8" height="34" rx="4"/><circle cx="-2" cy="104" r="5.5"/>
<rect x="30" y="60" width="7" height="20" rx="3.5"/><circle cx="33.5" cy="82" r="5"/></g>
<ellipse cx="-34" cy="-46" rx="20" ry="10" fill="#fff" opacity="0.75" filter="url(#sm)"/>
</g>'''

def drips(n, x0, x1, y0, lmax, seed, lmin=40, ws=(6, 8, 10, 12, 16)):
    r = random.Random(seed); out = []
    for _ in range(n):
        x = r.randint(x0, x1); w = r.choice(ws); L = r.randint(lmin, lmax)
        dur = r.uniform(5, 9); beg = r.uniform(0, 7)
        kt = 'keyTimes="0;0.55;0.9;1"'
        out.append(f'''<g><rect x="{x-w/2:.1f}" y="{y0}" width="{w}" height="0" rx="{w/2}" fill="#000"><animate attributeName="height" values="0;{L};{L};{L}" {kt} dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></rect>
<circle cx="{x}" cy="{y0}" r="{w*0.75:.1f}" fill="#000"><animate attributeName="cy" values="{y0};{y0+L};{y0+L};{y0+L}" {kt} dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></circle>
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.88;0.97;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></g>''')
    return "\n".join(out)

def drops(n, seed=7):
    r = random.Random(seed); out = []
    for _ in range(n):
        x = r.randint(20, W - 20); rad = r.uniform(2.5, 5); dur = r.uniform(3, 7); beg = r.uniform(0, 8)
        out.append(f'<circle cx="{x}" cy="0" r="{rad:.1f}" fill="#000"><animate attributeName="cy" values="20;{H}" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines="0.6 0 1 0.8"/><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/></circle>')
    return "\n".join(out)

def mover(cx, cy, rx, ry, size, dur, off, tilt=7):
    """pumpkin flying in an ellipse; smaller at the far (top) side, bigger at the near (bottom) side = fake 3D"""
    s = size / 200; far, near = s * 0.72, s * 1.25
    return f'''<g transform="translate({cx-rx} {cy})"><g>
<animateMotion path="M0,0 a{rx},{ry} 0 1,1 {2*rx},0 a{rx},{ry} 0 1,1 {-2*rx},0 z" dur="{dur}s" begin="-{off}s" repeatCount="indefinite"/>
<g><animateTransform attributeName="transform" type="scale" values="{s} {s};{far} {far};{s} {s};{near} {near};{s} {s}" keyTimes="0;0.25;0.5;0.75;1" dur="{dur}s" begin="-{off}s" repeatCount="indefinite"/>
<g><animateTransform attributeName="transform" type="rotate" values="-{tilt};{tilt};-{tilt}" dur="{dur/2:.1f}s" repeatCount="indefinite"/>
<use href="#pk" xlink:href="#pk"/></g></g></g></g>'''

def floater(cx, cy, size, dur=5, beg=0):
    s = size / 200
    return f'''<g transform="translate({cx} {cy})"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="{dur}s" begin="-{beg}s" repeatCount="indefinite"/>
<g transform="scale({s})"><use href="#pk" xlink:href="#pk"/></g></g></g>'''

def card(y, h, title):
    return (f'<rect x="70" y="{y}" width="860" height="{h}" rx="22" fill="#0a0a0a" fill-opacity="0.96" stroke="#f0f0f0" stroke-width="2"/>'
            f'<text x="100" y="{y+50}" font-family="{HEAD}" font-size="30" letter-spacing="2" fill="#f5f5f5">{title}</text>')

def build(st):
    back, cards, front = [], [], []
    # pumpkins that fly BEHIND the cards (they pop out at the sides)
    back += [mover(60, 640, 45, 110, 110, 18, 0), mover(940, 820, 45, 120, 110, 20, 6),
             mover(60, 1100, 45, 120, 100, 22, 11), mover(940, 1330, 45, 110, 105, 17, 3)]
    # hero (in front)
    front += [mover(150, 215, 80, 50, 120, 14, 0), mover(850, 205, 80, 55, 135, 16, 5), mover(500, 345, 230, 22, 62, 24, 9)]
    cards.append(f'''<g text-anchor="middle">
<text x="500" y="170" font-family="{MONO}" font-weight="900" font-size="64" fill="#0b0b0b" stroke="#f2f2f2" stroke-width="1.5" letter-spacing="6">SAPTAK CHAKI</text>
<text x="500" y="222" font-family="{MONO}" font-weight="900" font-size="18" fill="#111" letter-spacing="3">ASPIRING PYTHON FULL STACK DEVELOPER</text>
<text x="500" y="258" font-family="{MONO}" font-size="16" fill="#222" letter-spacing="2">B.TECH CSE · IOT · CYBER SECURITY · BLOCKCHAIN</text></g>''')
    # about
    y = 420; cards.append(card(y, 210, "ABOUT THE SPELLBINDER"))
    for i, t in enumerate(["Welcome to my Halloween lair! I am Saptak Chaki, a B.Tech",
                           "CSE student crafting powerful Python full-stack applications.",
                           "I specialize in IoT, Cyber Security, and Blockchain - brewing",
                           "secure, high-performance digital magic into every build."]):
        cards.append(f'<text x="100" y="{y+95+i*30}" font-family="{MONO}" font-size="17" fill="#dcdcdc">{escape(t)}</text>')
    # stats (LIVE)
    y = 660; cards.append(card(y, 250, "HALLOWEEN STATS &amp; STREAK"))
    for i, (cx, val, lab) in enumerate([(235, st["commits"], "COMMITS"), (500, st["repos"], "REPOSITORIES"),
                                        (765, f'{st["stars"]} / {st["streak"]}', "STARS / STREAK")]):
        cards.append(floater(cx, y + 112, 74, 5 + i, i))
        cards.append(f'<text x="{cx}" y="{y+192}" text-anchor="middle" font-family="{MONO}" font-weight="900" font-size="44" fill="#fff">{val}</text>')
        cards.append(f'<text x="{cx}" y="{y+225}" text-anchor="middle" font-family="{MONO}" font-weight="900" font-size="15" letter-spacing="3" fill="#b5b5b5">{lab}</text>')
    # languages (LIVE)
    y = 940; cards.append(card(y, 230, "CURSED CODE BREW  ·  LANGUAGES"))
    sh = ["#f5f5f5", "#d2d2d2", "#b0b0b0", "#8e8e8e", "#6c6c6c", "#4d4d4d", "#363636"]
    cards.append(f'<clipPath id="bc"><rect x="100" y="{y+75}" width="800" height="26" rx="13"/></clipPath>')
    x, bar = 100.0, []
    for i, (n, p) in enumerate(st["langs"]):
        w = 800 * p / 100; bar.append(f'<rect x="{x:.1f}" y="{y+75}" width="{w:.1f}" height="26" fill="{sh[i % 7]}"/>'); x += w
    cards.append('<g clip-path="url(#bc)">' + "".join(bar) + '</g>')
    for i, (n, p) in enumerate(st["langs"]):
        cx, cy = 100 + (i % 3) * 280, y + 145 + (i // 3) * 36
        cards.append(f'<circle cx="{cx+8}" cy="{cy}" r="8" fill="{sh[i % 7]}"/><text x="{cx+26}" y="{cy+6}" font-family="{MONO}" font-size="18" fill="#f0f0f0">{escape(n)} {p}%</text>')
    # tech brew
    y = 1200; cards.append(card(y, 330, "WITCH'S TECH BREW"))
    techs = ["Python", "Django", "Flask / FastAPI", "HTML / CSS", "JavaScript", "React",
             "SQL / MySQL", "Git / GitHub", "Linux", "IoT", "Cyber Security", "Blockchain"]
    hot = {"Python", "JavaScript", "SQL / MySQL", "Linux", "Cyber Security"}
    for i, t in enumerate(techs):
        cx, cy = 100 + (i % 3) * 270, y + 80 + (i // 3) * 58
        f, tc = ("#ececec", "#000") if t in hot else ("#151515", "#e6e6e6")
        cards.append(f'<rect x="{cx}" y="{cy}" width="250" height="44" rx="10" fill="{f}" stroke="#bdbdbd" stroke-width="1.5"/>'
                     f'<text x="{cx+125}" y="{cy+29}" text-anchor="middle" font-family="{MONO}" font-weight="900" font-size="17" fill="{tc}">{escape(t)}</text>')
    defs = f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3c3c3c"/><stop offset="0.12" stop-color="#8f8f8f"/><stop offset="0.5" stop-color="#dcdcdc"/><stop offset="0.88" stop-color="#8f8f8f"/><stop offset="1" stop-color="#3c3c3c"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0.5"/><stop offset="0.07" stop-color="#000" stop-opacity="0"/><stop offset="0.9" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.6"/></linearGradient>
<radialGradient id="pg" cx="35%" cy="30%" r="80%"><stop offset="0" stop-color="#fff"/><stop offset="0.55" stop-color="#e6e6e6"/><stop offset="1" stop-color="#a8a8a8"/></radialGradient>
<radialGradient id="pg2" cx="40%" cy="30%" r="85%"><stop offset="0" stop-color="#f0f0f0"/><stop offset="0.6" stop-color="#c4c4c4"/><stop offset="1" stop-color="#7a7a7a"/></radialGradient>
<linearGradient id="pst" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#555"/><stop offset="1" stop-color="#0d0d0d"/></linearGradient>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope="0.16"/></feComponentTransfer></filter>
<filter id="sm" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
{PUMPKIN}
</defs>'''
    blood = "\n".join([drips(30, 20, W - 20, 0, 190, 1), drips(8, 6, 58, 120, 230, 2, 90), drips(8, W - 58, W - 6, 100, 230, 3, 90),
                       drips(6, 100, W - 100, 630, 26, 4, 12, (6, 8)), drips(6, 100, W - 100, 910, 26, 5, 12, (6, 8)),
                       drips(6, 100, W - 100, 1170, 26, 6, 12, (6, 8)), drops(26)])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="100%">
{defs}
<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" filter="url(#grain)"/><rect width="{W}" height="{H}" fill="url(#fade)"/>
{chr(10).join(back)}
{chr(10).join(cards)}
{chr(10).join(front)}
{blood}
</svg>'''

if __name__ == "__main__":
    s = fetch_stats(); print(s)
    open(OUT, "w", encoding="utf-8").write(build(s)); print("wrote", OUT)
