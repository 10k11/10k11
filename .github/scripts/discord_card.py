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

W, H = 460, 150
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
o.append("""<defs><style>
text{font-family:'Segoe UI',Inter,Helvetica,Arial,sans-serif}
.n{font-size:17px;font-weight:700;fill:#f0f6fc}.s{font-size:12px;fill:#b6c0cc}.l{font-size:10px;font-weight:700;letter-spacing:1.5px;fill:#a371f7}
.t{font-size:14px;font-weight:700;fill:#f0f6fc}.m{font-size:12px;fill:#b6c0cc}
</style>
<clipPath id="av"><circle cx="46" cy="42" r="24"/></clipPath>
<clipPath id="art"><rect x="20" y="82" width="52" height="52" rx="8"/></clipPath></defs>""")
o.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="#161b22" stroke="#30363d" stroke-width="2"/>')
if avatar:
    o.append(f'<image href="{avatar}" x="22" y="18" width="48" height="48" clip-path="url(#av)"/>')
else:
    o.append('<circle cx="46" cy="42" r="24" fill="#30363d"/>')
o.append(f'<circle cx="64" cy="60" r="7" fill="{STATUS.get(status, "#747f8d")}" stroke="#161b22" stroke-width="3"/>')
o.append(f'<text class="n" x="84" y="38">{escape(user.get("global_name") or user["username"])}</text>')
sub = f'@{user["username"]}  ·  {status}'
if custom and custom.get("state"):
    sub = clip(custom["state"], 38)
o.append(f'<text class="s" x="84" y="58">{escape(sub)}</text>')
o.append(f'<rect x="20" y="76" width="{W-40}" height="1" fill="#30363d"/>')
if main:
    art = img_uri(art_url(main)) if art_url(main) else None
    if art:
        o.append(f'<image href="{art}" x="20" y="88" width="52" height="52" clip-path="url(#art)" preserveAspectRatio="xMidYMid slice"/>')
        tx = 84
    else:
        tx = 22
    o.append(f'<text class="l" x="{tx}" y="96">{LABEL[main["type"]]}</text>')
    o.append(f'<text class="t" x="{tx}" y="114">{escape(clip(main.get("details") or main["name"], 40))}</text>')
    second = main.get("state") or (main["name"] if main.get("details") else "")
    o.append(f'<text class="m" x="{tx}" y="132">{escape(clip(second, 46))}</text>')
else:
    o.append('<text class="m" x="22" y="112">No activity right now.</text>')
    o.append('<text class="s" x="22" y="130">Probably solving a CTF.</text>')
o.append("</svg>")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(o))
print("wrote", OUT)
