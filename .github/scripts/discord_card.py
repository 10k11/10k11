import base64, json, os, sys, urllib.request
from xml.sax.saxutils import escape

USER_ID = os.environ.get("DISCORD_ID", "1005536880659529808")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/discord.svg"
LABEL = {0: "PLAYING", 1: "STREAMING", 2: "LISTENING TO", 3: "WATCHING", 5: "COMPETING IN"}
STATUS = {"online": "#3ba55d", "idle": "#faa61a", "dnd": "#ed4245", "offline": "#747f8d"}


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-card"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
    return data if raw else json.loads(data)


def img_uri(url):
    try:
        data = get(url, raw=True)
        kind = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
        return f"data:{kind};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None


def clip(text, n):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def art_url(act):
    if act.get("id") == "spotify:1" and act.get("assets", {}).get("large_image", "").startswith("spotify:"):
        return "https://i.scdn.co/image/" + act["assets"]["large_image"].split(":", 1)[1]
    img = act.get("assets", {}).get("large_image")
    if not img:
        return None
    if img.startswith("mp:external/"):
        return "https://media.discordapp.net/external/" + img[len("mp:external/"):]
    if img.startswith("mp:"):
        return "https://media.discordapp.net/" + img[3:]
    if act.get("application_id"):
        return f"https://cdn.discordapp.com/app-assets/{act['application_id']}/{img}.png"
    return None


d = get(f"https://api.lanyard.rest/v1/users/{USER_ID}")["data"]
user = d["discord_user"]
status = d.get("discord_status", "offline")
acts = d.get("activities", [])
custom = next((a for a in acts if a["type"] == 4), None)
main = next((a for a in acts if a["type"] in LABEL), None)

avatar = None
if user.get("avatar"):
    avatar = img_uri(f"https://cdn.discordapp.com/avatars/{USER_ID}/{user['avatar']}.png?size=128")

import math

W, H = 460, 168
PALETTE = {"cobalt": ("#0b1a40", "#1e48a8"), "crimson": ("#3d0a14", "#c81d3c"), "violet": ("#1f0a3d", "#7c3aed")}
bg_a, bg_b = PALETTE.get(((user.get("collectibles") or {}).get("nameplate") or {}).get("palette"), PALETTE["cobalt"])
styles = user.get("display_name_styles") or {}
name_color = "#%06x" % styles["colors"][0] if styles.get("colors") else "#1c98eb"

plate = None
np_asset = ((user.get("collectibles") or {}).get("nameplate") or {}).get("asset")
if np_asset:
    plate = img_uri(f"https://cdn.discordapp.com/assets/collectibles/{np_asset}static.png")

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
o.append(f"""<defs><style>
text{{font-family:'Segoe UI',Inter,Helvetica,Arial,sans-serif}}
.n{{font-size:19px;font-weight:700;fill:{name_color}}}.s{{font-size:12px;fill:#cfe4ff}}.l{{font-size:10px;font-weight:700;letter-spacing:1.5px;fill:#6cb6ff}}
.t{{font-size:14px;font-weight:700;fill:#f0f6fc}}.m{{font-size:12px;fill:#aac4e8}}
</style>
<linearGradient id="hd" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{bg_a}"/><stop offset="1" stop-color="{bg_b}"/></linearGradient>
<linearGradient id="ice" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6fbff"/><stop offset="1" stop-color="#5cc8ff"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>
<clipPath id="card"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14"/></clipPath>
<clipPath id="av"><circle cx="48" cy="44" r="24"/></clipPath>
<clipPath id="art"><rect x="20" y="102" width="52" height="52" rx="8"/></clipPath></defs>""")
o.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#0a1020"/>')
o.append('<g clip-path="url(#card)">')
o.append(f'<rect x="0" y="0" width="{W}" height="88" fill="url(#hd)"/>')
if plate:
    o.append(f'<image href="{plate}" x="{W-448}" y="2" width="448" height="84" preserveAspectRatio="none"/>')
o.append('<rect x="0" y="87" width="460" height="1" fill="#2b3a5c"/>')
# ice crystal ring
cx, cy = 48, 44
o.append(f'<circle cx="{cx}" cy="{cy}" r="27.5" fill="none" stroke="#a8e2ff" stroke-width="1.6" opacity="0.9"/>')
for i in range(12):
    ang = math.radians(i * 30 + 8)
    long_ = 5 + (i % 3) * 2.5
    r0, r1 = 27, 27 + long_
    px, py = math.cos(ang), math.sin(ang)
    nx, ny = -py, px
    w = 1.6 + (i % 2) * 0.6
    pts = [(cx + px * r0 + nx * w, cy + py * r0 + ny * w), (cx + px * r1, cy + py * r1),
           (cx + px * r0 - nx * w, cy + py * r0 - ny * w), (cx + px * (r0 - 2), cy + py * (r0 - 2))]
    o.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" fill="#d6f2ff" opacity="0.8"/>')
if avatar:
    o.append(f'<image href="{avatar}" x="24" y="20" width="48" height="48" clip-path="url(#av)"/>')
else:
    o.append(f'<circle cx="{cx}" cy="{cy}" r="24" fill="#1b2a52"/>')
o.append(f'<circle cx="68" cy="64" r="7" fill="{STATUS.get(status, "#747f8d")}" stroke="#0a1020" stroke-width="3"/>')
o.append(f'<text class="n" x="92" y="40">{escape(user.get("global_name") or user["username"])}</text>')
sub = f'@{user["username"]}  ·  {status}'
if custom and custom.get("state"):
    sub = clip(custom["state"], 38)
o.append(f'<text class="s" x="92" y="60">{escape(sub)}</text>')
if main:
    art = img_uri(art_url(main)) if art_url(main) else None
    if art:
        o.append(f'<image href="{art}" x="20" y="102" width="52" height="52" clip-path="url(#art)" preserveAspectRatio="xMidYMid slice"/>')
        tx = 84
    else:
        tx = 22
    o.append(f'<text class="l" x="{tx}" y="114">{LABEL[main["type"]]}</text>')
    o.append(f'<text class="t" x="{tx}" y="132">{escape(clip(main.get("details") or main["name"], 40))}</text>')
    second = main.get("state") or (main["name"] if main.get("details") else "")
    o.append(f'<text class="m" x="{tx}" y="150">{escape(clip(second, 46))}</text>')
else:
    o.append('<text class="m" x="22" y="124">No activity right now.</text>')
    o.append('<text class="s" x="22" y="144">Probably solving a CTF.</text>')
o.append('</g>')
o.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="none" stroke="#2b3a5c" stroke-width="1.5"/>')
o.append("</svg>")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(o))
print("wrote", OUT)
