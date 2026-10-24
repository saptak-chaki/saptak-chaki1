#!/usr/bin/env python3
"""
Usage:  python blend_patch.py profile.svg
Output: profile_new.svg   (original file untouched)

Kora hobe:
 1. Social media (LinkedIn/Instagram/Facebook) section remove
 2. Sob text Japanese font stack e (about + intro shoh)
 3. Hero image er sathe realistic blend: real bloom (image-er nijer blur copy), colour grade,
    wet-road glow, rain, film grain, neon flicker
 4. Baki cards image-er colour er sathe blend (blurred image background + glass cards)
 5. Page height trim, stale c2pa metadata remove
"""
import re, sys

src = sys.argv[1] if len(sys.argv) > 1 else "profile.svg"
s = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= 1, f"NOT FOUND: {old[:70]}"
    s = s.replace(old, new, count)

# ---- 1. social media remove + height trim ----
s, n = re.subn(r'<rect x="30" y="1449".*?letter-spacing="1\.4">SAPTAK</text>', '', s, flags=re.S)
assert n == 1, "social block not found"
rep('<text x="360" y="1511"', '<text x="360" y="1460"')
s = s.replace('viewBox="0 0 720 1527" width="720" height="1527"', 'viewBox="0 0 720 1485" width="720" height="1485"')
rep('<rect width="720" height="1527" fill="url(#bg)"/>', '<rect width="720" height="1485" fill="url(#bg)"/>')

# ---- stale metadata ----
s = re.sub(r'<metadata>.*?</metadata>', '', s, flags=re.S)

# ---- 2. Japanese font everywhere ----
JP = "'Yu Gothic UI','Yu Gothic','Hiragino Kaku Gothic ProN','Noto Sans JP','Noto Sans CJK JP','Meiryo','MS Gothic',sans-serif"
s, n = re.subn(r'font-family="[^"]*"', f'font-family="{JP}"', s, count=1)
assert n == 1

# ---- ids on the two pictures (so we can reuse them for bloom / blurred bg) ----
rep('<image href="data:image/jpeg', '<image id="heroImg" href="data:image/jpeg')
rep('<image href="data:image/webp', '<image id="carImg" href="data:image/webp')

# ---- 4. cards: more glass, same palette ----
rep('stop-color="#1b1260" stop-opacity="0.94"', 'stop-color="#1b1260" stop-opacity="0.66"')
rep('stop-color="#2e0f58" stop-opacity="0.94"', 'stop-color="#2e0f58" stop-opacity="0.66"')
s = s.replace('fill="#120a36" stroke="#ff8a3d"', 'fill="#120a36" fill-opacity="0.66" stroke="#ff66b3"')
s = s.replace('#ff8a3d', '#ff66b3')   # orange -> palette pink

# ---- defs ----
DEFS = '''
  <filter id="bgblur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="16"/></filter>
  <filter id="bloom" filterUnits="userSpaceOnUse" x="-60" y="-60" width="840" height="740"><feColorMatrix type="matrix" values="1.7 0 0 0 -0.28  0 1.7 0 0 -0.28  0 0 1.7 0 -0.28  0 0 0 1 0"/><feGaussianBlur stdDeviation="13"/></filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
  <linearGradient id="grade" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1f6bff"/><stop offset="0.55" stop-color="#6a2cff"/><stop offset="1" stop-color="#ff2fa0"/></linearGradient>
  <linearGradient id="wetH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d8ff"/><stop offset="0.5" stop-color="#7a5cff"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient>
  <linearGradient id="wetV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="wetMask"><rect x="0" y="520" width="720" height="100" fill="url(#wetV)"/></mask>
  <linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0524" stop-opacity="1"/><stop offset="1" stop-color="#0d0524" stop-opacity="0"/></linearGradient>
  <linearGradient id="fadeBot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d0524" stop-opacity="0"/><stop offset="1" stop-color="#0d0524" stop-opacity="1"/></linearGradient>
</defs>'''
rep('</defs>', DEFS)

# ---- css ----
CSS = '''
  .scr{mix-blend-mode:screen} .ovl{mix-blend-mode:overlay} .sl{mix-blend-mode:soft-light}
  .pulse{animation:pulse 3.4s ease-in-out infinite}
  @keyframes pulse{0%,100%{opacity:.42}50%{opacity:.78}}
  .flick{animation:flick 5.5s infinite}
  @keyframes flick{0%,40%{opacity:.7}42%{opacity:.25}44%,60%{opacity:.7}62%{opacity:.35}64%,100%{opacity:.7}}
  .rain line{animation:rain .75s linear infinite}
  @keyframes rain{from{transform:translate(0,-40px)}to{transform:translate(-45px,640px)}}
</style>'''
rep('</style>', CSS)

# ---- 4. blurred picture behind the lower cards ----
BG = '''
<g opacity="0.36" filter="url(#bgblur)"><use href="#heroImg" transform="translate(0 600) scale(1 1.42)"/></g>
<rect y="600" width="720" height="110" fill="url(#fadeTop)"/>
<rect y="1380" width="720" height="105" fill="url(#fadeBot)"/>
'''
rep('<rect width="720" height="1485" fill="url(#bg)"/>', '<rect width="720" height="1485" fill="url(#bg)"/>' + BG)

# ---- 3. realistic blend layers on the hero ----
rain = "".join(
    f'<line x1="{x}" y1="0" x2="{x-5}" y2="16" stroke="#bfe6ff" stroke-width="1" opacity="0.22" style="animation-delay:-{(i*0.13)%0.75:.2f}s;animation-duration:{0.6+(i%4)*0.1:.1f}s"/>'
    for i, x in enumerate(range(15, 740, 45)))
HERO = f'''
  <rect width="720" height="620" fill="url(#grade)" class="sl" opacity="0.5"/>
  <g class="scr pulse" filter="url(#bloom)"><use href="#heroImg"/><use href="#carImg"/></g>
  <g class="scr flick" mask="url(#wetMask)"><rect x="0" y="520" width="720" height="100" fill="url(#wetH)" opacity="0.55"/></g>
  <g class="rain">{rain}</g>
  <rect width="720" height="620" fill="#808080" filter="url(#grain)" class="ovl" opacity="0.16"/>
  <rect width="720" height="620" fill="url(#vig)"/>'''
rep('<rect width="720" height="620" fill="url(#vig)"/>', HERO)

out = src.rsplit(".", 1)[0] + "_new.svg"
open(out, "w", encoding="utf-8").write(s)
print("ok ->", out)
