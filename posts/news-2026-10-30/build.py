"""Ten news carousels (1080x1350, 6 slides each), each in its own look (owner 2026-10-30: current AI news, not our
video topics; at least 10; every carousel different; combine the looks we built).
  .venv/bin/python posts/news-2026-10-30/build.py && node posts/news-2026-10-30/shoot.js posts/news-2026-10-30/*/
Every fact is from a primary source checked on 2026-10-30 (SOURCES.md). No photos: all grounds are our own.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RED = (ROOT / "explainer/frames/themes/red-grain/surface.png").as_uri()
GREEN = (ROOT / "explainer/frames/themes/card/surface-green.png").as_uri()
NOISE = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='n'>"
         "<feTurbulence type='fractalNoise' baseFrequency='1.1' numOctaves='3'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")

BASE = f"""
* {{ box-sizing: border-box; margin: 0; }}
body {{ background: #222; }}
.s {{ position: relative; width: 1080px; height: 1350px; overflow: hidden; background: var(--bg); color: var(--ink); }}
.grain {{ position: absolute; inset: 0; opacity: var(--grain, .12); mix-blend-mode: overlay; pointer-events: none; background-image: {NOISE}; }}
.tag {{ position: absolute; left: 72px; top: 66px; font: 600 24px/1 var(--ui); letter-spacing: .16em; text-transform: uppercase; }}
.num {{ position: absolute; right: 72px; top: 66px; font: 500 24px/1 'JetBrains Mono', monospace; opacity: .7; }}
.top {{ position: absolute; left: 72px; right: 72px; top: 150px; }}
h1 {{ font: var(--h1); letter-spacing: var(--h1ls, -.04em); }}
h1 i {{ font: italic 400 1.03em/1 Fraunces, serif; letter-spacing: -.02em; }}
.lede {{ margin-top: 28px; font: var(--lede); max-width: 920px; }}
.foot {{ position: absolute; left: 72px; right: 72px; bottom: 58px; display: flex; justify-content: space-between; align-items: end; gap: 40px;
  font: 500 20px/1.3 'JetBrains Mono', monospace; opacity: .8; }}
.foot b {{ font: 800 25px/1 'Bricolage Grotesque', sans-serif; letter-spacing: -.02em; white-space: nowrap; }}
.x {{ position: absolute; }}
svg.v {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1350px; overflow: visible; }}
.th {{ fill: none; stroke: var(--ink); stroke-width: 10; stroke-linecap: round; stroke-linejoin: round; }}
.tn {{ fill: none; stroke: var(--ink); stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }}
.big {{ font: 800 150px/.95 'Bricolage Grotesque', sans-serif; letter-spacing: -.05em; }}
.mono {{ font: 500 36px/1.45 'JetBrains Mono', monospace; }}
.lab {{ font: 600 25px/1.2 var(--ui); letter-spacing: .12em; text-transform: uppercase; }}
.it {{ font: italic 400 44px/1.15 Fraunces, serif; }}
.swipe {{ position: absolute; right: 72px; bottom: 116px; font: italic 400 36px/1 Fraunces, serif; }}
.row {{ position: absolute; left: 72px; right: 72px; display: flex; justify-content: space-between; align-items: baseline;
  border-top: 3px solid var(--ink); padding-top: 18px; }}
.row .k {{ font: 600 26px/1.2 var(--ui); letter-spacing: .1em; text-transform: uppercase; }}
.row .vv {{ font: 800 64px/1 'Bricolage Grotesque', sans-serif; letter-spacing: -.03em; }}
"""

THEMES = {
    # 1 red grain: heavy grotesque + Fraunces italic, cream on red
    "red": f""".t-red {{ --bg: #AB3D3C url('{RED}') 0 -285px / 1080px 1920px; --ink: #F6EEDC; --ui: 'Inter Tight', sans-serif;
      --h1: 800 112px/.9 'Bricolage Grotesque', sans-serif; --lede: italic 400 44px/1.2 Fraunces, serif; --grain: 0; }}
      .t-red .chip {{ position:absolute; padding:16px 28px 20px; background:#F6EEDC; color:#8E2A29; border-radius:14px; font:800 60px/1 'Bricolage Grotesque',sans-serif; letter-spacing:-.03em; }}""",
    # 2 blueprint: Space Grotesk + mono, white on drafting blue with a grid and rulers
    "blue": """.t-blue { --bg: #0C4297; --ink: #FFFFFF; --ui: 'Space Grotesk', sans-serif; --h1: 700 100px/.95 'Space Grotesk', sans-serif;
      --h1ls: -.035em; --lede: 400 36px/1.35 'JetBrains Mono', monospace; --grain: .1; }
      .t-blue::before { content:''; position:absolute; inset:40px; border:2px solid rgba(255,255,255,.55);
        background-image: linear-gradient(rgba(255,255,255,.13) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.13) 1px, transparent 1px),
        linear-gradient(rgba(255,255,255,.28) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,.28) 2px, transparent 2px);
        background-size: 40px 40px, 40px 40px, 200px 200px, 200px 200px; }
      .t-blue h1 i { font: 300 1em/1 'Space Grotesk', sans-serif; font-style: normal; text-decoration: underline 4px; text-underline-offset: 10px; }
      .t-blue .box { position:absolute; border:3px solid #fff; padding:22px 26px; background:#0C4297; }""",
    # 3 green leaf light: big Fraunces serif + Inter Tight, cream
    "green": f""".t-green {{ --bg: #0C462C url('{GREEN}') 0 -285px / 1080px 1920px; --ink: #F2ECDE; --ui: 'Inter Tight', sans-serif;
      --h1: 400 112px/.98 Fraunces, serif; --h1ls: -.03em; --lede: 500 38px/1.3 'Inter Tight', sans-serif; --grain: .08; }}
      .t-green h1 i {{ font: italic 300 1em/1 Fraunces, serif; color: #F8EB44; }}""",
    # 4 chat bubbles on blue: Inter Tight, white bubbles
    "chat": """.t-chat { --bg: #3D52A8; --ink: #FFFFFF; --ui: 'Inter Tight', sans-serif; --h1: 800 96px/.98 'Inter Tight', sans-serif;
      --h1ls: -.045em; --lede: 500 36px/1.3 'Inter Tight', sans-serif; --grain: .08; }
      .bub { position:absolute; max-width:760px; padding:26px 34px; border-radius:40px; font:600 38px/1.25 'Inter Tight',sans-serif; letter-spacing:-.01em; }
      .bub.l { background:#fff; color:#1D2A66; border-bottom-left-radius:10px; left:72px; }
      .bub.r { background:#A9C1FF; color:#14204F; border-bottom-right-radius:10px; right:72px; }
      .who { position:absolute; font:600 22px/1 'Inter Tight',sans-serif; letter-spacing:.14em; text-transform:uppercase; opacity:.75; }""",
    # 5 calendar paper with stickers: cobalt on cream
    "cal": """.t-cal { --bg: #F3EDDC; --ink: #002A8E; --ui: 'Inter Tight', sans-serif; --h1: 800 92px/.95 'Inter Tight', sans-serif;
      --h1ls: -.04em; --lede: italic 400 40px/1.25 Fraunces, serif; --grain: .1; }
      .t-cal .rings { position:absolute; left:28px; right:28px; top:0; height:100px; display:flex; justify-content:space-between; }
      .t-cal .rings i { width:14px; height:84px; border-radius:7px; background:#002A8E; }
      .t-cal .tag { top: 120px; } .t-cal .num { top: 120px; } .t-cal .top { top: 190px; }
      .wk { position:absolute; left:72px; right:72px; top:600px; height:560px; display:grid; grid-template-columns:repeat(7,1fr); border-top:3px solid #002A8E; }
      .wk div { border-right:3px solid #002A8E; position:relative; padding:12px 10px; font:600 30px/1 'Inter Tight',sans-serif; }
      .wk div:last-child { border-right:0; } .wk .on { background:#002A8E; color:#F3EDDC; }
      .wk small { display:block; font:600 18px/1 'Inter Tight',sans-serif; letter-spacing:.12em; margin-bottom:10px; opacity:.7; }
      .stk { position:absolute; padding:18px 24px; border:4px solid #002A8E; border-radius:20px; font:700 34px/1.1 'Inter Tight',sans-serif;
        box-shadow: 0 8px 16px rgba(0,20,70,.25); letter-spacing:-.01em; }""",
    # 6 cobalt charts (the curve post the owner liked): Bricolage + Fraunces, cream on cobalt
    "cobalt": """.t-cobalt { --bg: #002A8E; --ink: #F3EDDC; --ui: 'Inter Tight', sans-serif; --h1: 800 104px/.92 'Bricolage Grotesque', sans-serif;
      --lede: italic 400 42px/1.22 Fraunces, serif; --grain: .14; }
      .t-cobalt .blk { display:inline-block; background:#F3EDDC; color:#002A8E; padding:0 .14em .04em; rotate:-2.5deg; border-radius:6px; }""",
    # 7 warm white paper, black ink, one red: Fraunces display + mono timeline
    "paper": """.t-paper { --bg: #EFEBE3; --ink: #141414; --ui: 'Inter Tight', sans-serif; --h1: 500 104px/.98 Fraunces, serif; --h1ls: -.035em;
      --lede: 500 36px/1.32 'Inter Tight', sans-serif; --grain: .1; }
      .t-paper h1 i { color: #C8372D; }
      .t-paper .red { color: #C8372D; }""",
    # 8 yellow with giant numbers: cobalt Bricolage numerals overlapping
    "yellow": """.t-yellow { --bg: #F4D23C; --ink: #002A8E; --ui: 'Inter Tight', sans-serif; --h1: 800 92px/.95 'Bricolage Grotesque', sans-serif;
      --lede: italic 400 40px/1.22 Fraunces, serif; --grain: .12; }
      .giant { position:absolute; font:800 520px/.8 'Bricolage Grotesque',sans-serif; letter-spacing:-.07em; color:#002A8E; opacity:.95; white-space:nowrap; }""",
    # 9 newsprint front page: Fraunces headlines, rules, columns, black on newsprint
    "news": """.t-news { --bg: #F1EDE4; --ink: #111111; --ui: 'Inter Tight', sans-serif; --h1: 700 100px/.95 Fraunces, serif; --h1ls: -.03em;
      --lede: 400 34px/1.35 Fraunces, serif; --grain: .16; }
      .t-news .mast { position:absolute; left:72px; right:72px; top:100px; border-top:6px solid #111; border-bottom:2px solid #111; padding:8px 0;
        display:flex; justify-content:space-between; font:600 20px/1 'Inter Tight',sans-serif; letter-spacing:.14em; text-transform:uppercase; }
      .t-news .top { top: 170px; }
      .t-news .cols { position:absolute; left:72px; right:72px; top:700px; columns:2; column-gap:44px; column-rule:2px solid #111;
        font:400 31px/1.42 Fraunces, serif; }""",
    # 10 dark film grain, white + yellow numbers
    "dark": """.t-dark { --bg: #121212; --ink: #F2F0EB; --ui: 'Space Grotesk', sans-serif; --h1: 700 100px/.95 'Space Grotesk', sans-serif; --h1ls: -.04em;
      --lede: 400 36px/1.35 'Space Grotesk', sans-serif; --grain: .22; }
      .t-dark h1 i { font: 700 1em/1 'Space Grotesk', sans-serif; font-style: normal; color: #F4D23C; }
      .t-dark .y { color: #F4D23C; }""",
}


ROUGHC = ('<defs><filter id="rc"><feTurbulence type="fractalNoise" baseFrequency=".03" numOctaves="2" seed="5"/>'
          '<feDisplacementMap in="SourceGraphic" scale="5"/></filter></defs>')


def S(theme, i, tag, title, lede="", visual="", foot="", swipe=False, extra=""):
    return (f'<section class="s t-{theme}">{extra}<div class="tag">{tag}</div><div class="num">{i:02d} / 06</div>'
            f'<div class="top"><h1>{title}</h1>{f"<div class=lede>{lede}</div>" if lede else ""}</div>{visual}'
            f'{"<div class=swipe>swipe &rarr;</div>" if swipe else ""}'
            f'<div class="foot"><span>{foot}</span><b>binary semaphore</b></div><div class="grain"></div></section>')


def rows(items, top=720, gap=150):
    return "".join(f'<div class="row" style="top:{top + k * gap}px"><span class="k">{a}</span><span class="vv">{b}</span></div>' for k, (a, b) in enumerate(items))


def hbars(items, top=700, gap=170, w=760, fillk=None):
    out = []
    for k, (lab, v, mx, note) in enumerate(items):
        L = w * v / mx
        out.append(f'<div class="x lab" style="left:72px;top:{top + k * gap - 40}px">{lab}</div>'
                   f'<div class="x" style="left:72px;top:{top + k * gap}px;width:{L:.0f}px;height:56px;border:5px solid var(--ink);border-radius:12px;'
                   f'{"background:var(--ink);" if k == fillk else ""}rotate:{-.5 + k * .4}deg"></div>'
                   f'<div class="x" style="left:{72 + L + 24:.0f}px;top:{top + k * gap - 2}px;font:800 56px/1 Bricolage Grotesque,sans-serif;letter-spacing:-.03em">{note}</div>')
    return "".join(out)


def ipo():
    T, t = "red", "Anthropic &middot; Oct 26"
    src = "anthropic.com/news, Oct 26 2026"
    return [
        S(T, 1, t, 'Anthropic filed to go <i>public.</i>', 'The company behind Claude sent an S-1 to the SEC.',
          '<div class="x big" style="left:72px;top:820px;font-size:300px;color:#F6EEDC">S-1</div>', src, swipe=True),
        S(T, 2, t, 'An S-1 is the <i>paperwork</i> for an IPO.', 'It is filed with the U.S. Securities and Exchange Commission before shares can be sold to the public.',
          '<div class="chip" style="left:72px;top:860px;rotate:-3deg">registration statement</div>', src),
        S(T, 3, t, 'Where it plans to <i>list.</i>', '',
          rows([("exchange", "Nasdaq"), ("ticker", "ANT"), ("shares", "Class A")], top=620, gap=170), src),
        S(T, 4, t, 'What we do <i>not</i> know yet.', 'The S-1 leaves these open:',
          rows([("number of shares", "not set"), ("price range", "not set"), ("date", "not given")], top=720, gap=170), src),
        S(T, 5, t, 'You cannot buy it <i>yet.</i>', 'The registration has not become effective. Until it does, no shares can be sold.',
          '<div class="chip" style="left:72px;top:900px;rotate:2deg">not effective yet</div>', "the S-1 notice on anthropic.com"),
        S(T, 6, t, 'One of the big AI labs is heading to the <i>stock market.</i>', 'Save this. We will post when the price range is set.',
          '<div class="x big" style="left:72px;top:820px;font-size:300px;color:#F6EEDC">ANT<span style="font:italic 400 300px Fraunces,serif">?</span></div>', "binarysemaphore.com"),
    ]


def carbon():
    T, t = "blue", "Google &middot; Oct 28"
    src = "blog.google, Gemini 4 Carbon, Oct 28 2026"
    return [
        S(T, 1, t, 'Google built a model for <i>cyber defense.</i>', 'Gemini 4 Carbon. Not open to everyone yet.',
          '<div class="box" style="left:72px;top:820px;font:500 30px/1.5 JetBrains Mono,monospace">MODEL &nbsp;&nbsp;Gemini 4 Carbon<br>FOCUS &nbsp;&nbsp;cybersecurity, long tasks<br>ACCESS &nbsp;limited</div>', src, swipe=True),
        S(T, 2, t, 'Who gets it <i>first.</i>', '',
          rows([("1. cyber defenders", "now"), ("2. trusted partners", "Fairwind"), ("3. everyone else", "soon")], top=640, gap=170), src),
        S(T, 3, t, 'Find, exploit, <i>patch.</i>', 'Three security tests, Google\'s own numbers:',
          hbars([("find bugs: SEC-bench Pro", 88.2, 100, "88.2%"), ("exploit: ExploitGym", 54.8, 100, "54.8%"), ("patch: CWE-bench", 71.0, 100, "71.0%")], top=760, fillk=0), src),
        S(T, 4, t, 'Ranked <i>#1</i> on one index.', 'Artificial Analysis Intelligence Index v5.0, as Google reports it.',
          '<div class="x" style="left:72px;top:780px;font:700 300px/1 Space Grotesk,sans-serif;letter-spacing:-.05em">59</div>', src),
        S(T, 5, t, 'The <i>price</i> per million tokens.', '',
          rows([("input, intro / later", "$2 / $4"), ("output, intro / later", "$10 / $20")], top=700, gap=200), src),
        S(T, 6, t, 'A model that finds bugs can also <i>use them.</i>', 'That is why access starts with defenders. Save this.',
          '<div class="box" style="left:72px;top:820px;font:500 34px/1.7 JetBrains Mono,monospace">1 &nbsp;find the bug<br>2 &nbsp;report it<br>3 &nbsp;patch it<br><span style="opacity:.6">before someone else uses it</span></div>', "binarysemaphore.com"),
    ]


def webai():
    T, t = "green", "Opera &middot; Oct 27"
    src = "press.opera.com, Oct 27 2026"
    browser = ('<path class="th" d="M 150 700 L 930 700 L 930 1150 L 150 1150 Z"/><path class="tn" d="M 150 780 L 930 780"/>'
               '<circle cx="200" cy="740" r="10" fill="currentColor"/><circle cx="235" cy="740" r="10" fill="currentColor"/><circle cx="270" cy="740" r="10" fill="currentColor"/>')
    return [
        S(T, 1, t, 'Your browser can now run AI <i>on its own.</i>', 'Opera\'s WebAI runs open models on your computer.',
          f'<svg class="v" style="color:#F2ECDE">{browser}</svg><div class="x it" style="left:220px;top:900px">the model lives here</div>', src, swipe=True),
        S(T, 2, t, 'Which models?', '',
          rows([("Google", "Gemma"), ("Macs only", "Apple's on-device model")], top=620, gap=200), src),
        S(T, 3, t, 'Your data stays on your <i>device.</i>', '&ldquo;the information the local AI handles stays on their own device.&rdquo;',
          '<svg class="v" style="color:#F2ECDE"><path class="th" d="M 160 760 L 600 760 L 600 1080 L 160 1080 Z"/><path class="th" d="M 120 1110 L 640 1110"/>'
          '<path class="tn" d="M 760 820 C 740 760 820 730 850 770 C 880 720 970 740 960 800 C 1010 810 1000 880 950 880 L 790 880 C 740 880 730 830 760 820 Z"/>'
          '<path class="th" d="M 790 940 L 960 1080 M 960 940 L 790 1080" style="stroke:#F8EB44"/></svg>'
          '<div class="x it" style="left:200px;top:880px">your computer</div><div class="x lab" style="left:770px;top:1100px">no cloud call</div>', src),
        S(T, 4, t, 'No bill per <i>request.</i>', 'Sites can add AI features without paying for every request. Users need no AI subscription.',
          '<div class="x" style="left:72px;top:720px;font:400 340px/1 Fraunces,serif;letter-spacing:-.05em;color:#F8EB44">$0</div><div class="x lab" style="left:80px;top:1080px">per request, for the site</div>', src),
        S(T, 5, t, 'Where it works <i>today.</i>', 'An opt-in early preview in Opera One. GX and Neon follow.',
          rows([("Windows", "64-bit Intel or AMD"), ("Mac", "Apple silicon")], top=760, gap=200), src),
        S(T, 6, t, 'A proposed <i>web standard.</i>', 'Backed by companies such as Google and Microsoft. Not final yet. Save this.',
          rows([("status", "proposal"), ("backed by", "Google, Microsoft"), ("in Opera", "early preview")], top=760, gap=150), "binarysemaphore.com"),
    ]


def agents():
    T, t = "chat", "Sierra + Meta &middot; Oct 6"
    src = "sierra.ai, Personal Agent Protocol"
    return [
        S(T, 1, t, 'Your AI agent will <i>log in</i> for you.', 'A new open standard, the Personal Agent Protocol.',
          '<div class="who" style="left:72px;top:690px">your agent</div><div class="bub l" style="top:730px">Hi, I\'m shopping for Sam. Is this in stock?</div>'
          '<div class="who" style="right:72px;top:900px">the store</div><div class="bub r" style="top:940px">Yes. Want to sign in to order?</div>', src, swipe=True),
        S(T, 2, t, 'It starts as a <i>guest.</i>', 'Enough to check stock or ask about returns.',
          '<div class="bub l" style="top:760px">What is your returns policy?</div><div class="bub r" style="top:930px">30 days. No sign-in needed.</div>',
          "example chat; the protocol defines guest access"),
        S(T, 3, t, 'You decide <i>the access.</i>', 'When a task needs your account, you sign in (OAuth) and choose:',
          '<div class="bub r" style="top:820px">read-only</div><div class="bub r" style="top:960px;right:330px">read and write</div>', src),
        S(T, 4, t, 'The business sets <i>the limits.</i>', 'It decides what agents may do on its site, its APIs (MCP, OpenAPI) or its own agent.',
          '<div class="bub l" style="top:800px">Change the delivery address, please.</div><div class="bub r" style="top:970px">Agents can see orders here, not edit them.</div>',
          "example chat; limits are set by each business"),
        S(T, 5, t, 'Who is <i>in?</i>', '',
          '<div class="bub l" style="top:640px">Walmart, Shopify, Stripe</div><div class="bub l" style="top:790px">Genesys, Instinct, Rocket</div>'
          '<div class="bub r" style="top:960px">+35 design partners on the draft, incl. Visa, PayPal, OpenAI</div>', src),
        S(T, 6, t, 'Still a <i>draft.</i>', 'A 1.0 is in development. Payments are planned as an extension. Save this.',
          '<div class="bub l" style="top:800px">Can I pay for this?</div><div class="bub r" style="top:970px">Not yet. Payments come later.</div>', "binarysemaphore.com"),
    ]


def october():
    T, t = "cal", "October 2026"
    rings = '<div class="rings">' + "<i></i>" * 26 + '</div>'

    def week(days, on, stickers):
        cells = "".join(f'<div class="{"on" if d in on else ""}"><small>{n}</small>{d}</div>' for n, d in days)
        return f'<div class="wk">{cells}</div>' + stickers

    names = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    W = lambda start: list(zip(names, range(start, start + 7)))
    return [
        S(T, 1, t, 'October in AI, <i style="font:italic 400 1em Fraunces,serif">week by week.</i>', 'What actually shipped, from the companies\' own posts.',
          '<div class="x" style="left:72px;top:640px;font:800 330px/1 Inter Tight,sans-serif;letter-spacing:-.06em">Oct</div>'
          '<div class="stk" style="left:620px;top:720px;background:#F4D23C;rotate:8deg">9 things</div>', "sources on each slide", swipe=True, extra=rings),
        S(T, 2, t, 'Week of Oct 4', '',
          week(W(4), {6, 7}, '<div class="stk" style="left:120px;top:760px;background:#fff;rotate:-5deg">6: agent protocol<br><span style="font-weight:500;font-size:26px">Sierra + Meta</span></div>'
                                 '<div class="stk" style="left:420px;top:930px;background:#C9D6FF;rotate:4deg">6: 890 MW nuclear<br><span style="font-weight:500;font-size:26px">Google + Constellation</span></div>'
                                 '<div class="stk" style="left:560px;top:700px;background:#F4D23C;rotate:-3deg">7: Claude Haiku 5.5</div>'),
          "sierra.ai, constellationenergy.com, anthropic.com", extra=rings),
        S(T, 3, t, 'Week of Oct 11', '',
          week(W(11), {14}, '<div class="stk" style="left:300px;top:820px;background:#fff;rotate:-4deg">14: Anthropic opens a<br>Singapore office, signs an MOU</div>'),
          "anthropic.com/news", extra=rings),
        S(T, 4, t, 'Oct 26: a <i style="font:italic 400 1em Fraunces,serif">big</i> Monday', '',
          week(W(25), {26}, '<div class="stk" style="left:160px;top:760px;background:#F4D23C;rotate:-6deg">Anthropic files<br>an S-1 for an IPO</div>'
                              '<div class="stk" style="left:470px;top:960px;background:#fff;rotate:5deg">Microsoft offers buyouts<br>to about 60,000 staff</div>'),
          "anthropic.com; Microsoft buyouts as reported Oct 26", extra=rings),
        S(T, 5, t, 'Oct 27 and 28', '',
          week(W(25), {27, 28}, '<div class="stk" style="left:110px;top:740px;background:#C9D6FF;rotate:4deg">27: Opera WebAI,<br>AI inside the browser</div>'
                                  '<div class="stk" style="left:470px;top:860px;background:#fff;rotate:-4deg">27: Claude for all levels<br>of US government (GSA)</div>'
                                  '<div class="stk" style="left:200px;top:1000px;background:#F4D23C;rotate:-2deg">28: Gemini 4 Carbon</div>'),
          "press.opera.com, anthropic.com, blog.google", extra=rings),
        S(T, 6, t, 'Which one will matter in a <i style="font:italic 400 1em Fraunces,serif">year?</i>', 'Tell us in the comments. Save this.',
          '<div class="wk" style="top:640px;height:auto;grid-template-rows:repeat(5,96px)">' + "".join(
              f'<div class="{"on" if d in (6, 7, 14, 26, 27, 28) else ""}" style="border-bottom:3px solid #002A8E">{d if 1 <= d <= 31 else ""}</div>' for d in range(-3, 32)) + '</div>',
          "binarysemaphore.com", extra=rings),
    ]


def prices():
    T, t = "cobalt", "AI prices &middot; Sep to Oct"
    src = "anthropic.com: Opus 5.5 (Sep 22), Sonnet 5.5 (Sep 28)"
    return [
        S(T, 1, t, 'The same AI work now costs <span class="blk">less.</span>', 'Not always a lower price. Fewer tokens per task.',
          '<svg class="v" style="color:#F3EDDC"><path class="th" d="M 120 760 C 300 790 420 900 560 960 C 700 1020 820 1050 960 1060"/>'
          '<path class="tn" d="M 120 700 L 120 1120 L 980 1120"/></svg><div class="x lab" style="left:130px;top:1150px">cost per task, newer models</div>', src, swipe=True),
        S(T, 2, t, 'Opus 5.5: a <i>lower</i> list price.', 'Per million tokens, against Opus 5:',
          hbars([("input: Opus 5", 5, 5, "$5"), ("input: Opus 5.5", 4, 5, "$4"), ("output: Opus 5", 25, 25, "$25"), ("output: Opus 5.5", 20, 25, "$20")], top=640, gap=150, fillk=None), src),
        S(T, 3, t, 'Sonnet 5.5: the <span class="blk">same</span> price.', '$2 in, $10 out, like Sonnet 5. Yet Anthropic says it costs up to 30% less per task.',
          rows([("Sonnet 5 per task", "100%"), ("Sonnet 5.5 per task", "up to 30% less")], top=820, gap=180), src),
        S(T, 4, t, 'Why? It uses <i>fewer tokens.</i>', 'You pay per token. Fewer tokens for the same job means a smaller bill.',
          hbars([("cache reads: Sonnet 5", .2, .2, "$0.20"), ("cache reads: Sonnet 5.5", .1, .2, "$0.10")], top=860, gap=170, fillk=1), src),
        S(T, 5, t, 'Google\'s new model starts <i>cheap,</i> then rises.', 'Gemini 4 Carbon, per million tokens:',
          rows([("intro: in / out", "$2 / $10"), ("later: in / out", "$4 / $20")], top=780, gap=200), "blog.google, Oct 28 2026"),
        S(T, 6, t, 'Compare cost per <span class="blk">task,</span> not per token.', 'Save this before you pick a model.',
          '<div class="x" style="left:72px;top:800px;font:800 104px/1.1 Bricolage Grotesque,sans-serif;letter-spacing:-.04em">cost =<br>price &times; <span class="blk">tokens</span></div>', "binarysemaphore.com"),
    ]


def eu():
    T, t = "paper", "EU AI Act &middot; Regulation (EU) 2026/1744"
    src = "Official Journal, Regulation (EU) 2026/1744"
    line = ('<svg class="v"><path class="th" d="M 72 1000 L 1008 1000"/>'
            '<circle cx="180" cy="1000" r="16" fill="#141414"/><circle cx="560" cy="1000" r="16" fill="#C8372D"/><circle cx="900" cy="1000" r="16" fill="#C8372D"/></svg>'
            '<div class="x lab" style="left:110px;top:1040px">Aug 2026<br><span style="text-decoration:line-through">old date</span></div>'
            '<div class="x lab red" style="left:470px;top:1040px">Dec 2, 2027</div><div class="x lab red" style="left:800px;top:1040px">Aug 2, 2028</div>')
    return [
        S(T, 1, t, 'Europe gave high-risk AI <i>more time.</i>', 'The strictest AI Act rules now start later.', line, src, swipe=True),
        S(T, 2, t, 'What counts as <i>high-risk?</i>', 'AI used in areas like these:',
          rows([("biometrics", "&rarr;"), ("hiring and work", "&rarr;"), ("education", "&rarr;"), ("law enforcement", "&rarr;")], top=640, gap=130),
          "European Parliament, Mar 2026"),
        S(T, 3, t, 'Those rules: <i>Dec 2, 2027.</i>', 'Was August 2, 2026. About 16 months later.',
          '<div class="x" style="left:72px;top:760px;font:500 210px/1 Fraunces,serif;letter-spacing:-.04em"><span style="text-decoration:line-through;opacity:.35">2026</span><br><span class="red">2027</span></div>', src),
        S(T, 4, t, 'AI inside regulated <i>products:</i> Aug 2, 2028.', 'Systems covered by EU product-safety laws get even longer.',
          rows([("listed areas (hiring, education...)", "Dec 2, 2027"), ("AI inside regulated products", "Aug 2, 2028")], top=820, gap=190), src),
        S(T, 5, t, 'Why the <i>delay?</i>', 'Standards and national authorities were late, so the rules were heavier to follow than expected.',
          rows([("technical standards", "late"), ("national authorities", "not ready")], top=820, gap=190), "the regulation's own recitals"),
        S(T, 6, t, 'Delayed, not <i>cancelled.</i>', 'If you build AI for Europe, the clock is still running. Save this.',
          '<div class="x red" style="left:72px;top:760px;font:500 250px/1 Fraunces,serif;letter-spacing:-.05em">2027</div><div class="x lab" style="left:80px;top:1030px">the next date to plan for</div>', "binarysemaphore.com"),
    ]


def deals():
    T, t = "yellow", "AI deals &middot; Crunchbase"
    src = "news.crunchbase.com"
    return [
        S(T, 1, t, 'AI companies are buying <i>AI companies.</i>', 'The biggest deals of 2026 so far.',
          '<div class="giant" style="left:40px;top:780px;font-size:400px">M&amp;A</div>', src, swipe=True),
        S(T, 2, t, 'SpaceX is buying <i>Cursor.</i>', 'Plans to buy the AI coding tool for $60 billion in stock. The biggest startup deal of 2026 so far.',
          '<div class="giant" style="left:40px;top:820px;font-size:440px">$60B</div>', "Crunchbase News, Jun 16 2026"),
        S(T, 3, t, 'Nvidia bid for <i>Hugging Face.</i>', 'The home of open AI models.',
          '<div class="giant" style="left:40px;top:760px;font-size:430px">$12.9B</div>', "Crunchbase, Q3 2026 report"),
        S(T, 4, t, 'Two more <i>big</i> ones.', '',
          rows([("AMD plans to buy World Labs", "$8.2B"), ("Stripe buys OpenRouter", "$7.5B")], top=720, gap=220), "Crunchbase, Q3 2026 report"),
        S(T, 5, t, 'AI took <i>64%</i> of all startup money.', 'Q3 2026: $102B of $159B in global venture funding.',
          '<div class="giant" style="left:40px;top:760px;font-size:480px">64%</div>', "Crunchbase, Q3 2026 report"),
        S(T, 6, t, 'A record <i>27</i> rounds of $1B or more.', 'In one quarter. Save this.', '<div class="giant" style="left:40px;top:760px;font-size:480px">27</div>', "Crunchbase, Q3 2026 report"),
    ]


def buyouts():
    T, t = "news", "Work &middot; Oct 26"
    mast = '<div class="mast"><span>binary semaphore</span><span>the work edition</span><span>Oct 2026</span></div>'
    src = "as reported Oct 26 2026 (Reuters, WSJ, Business Insider)"
    return [
        S(T, 1, t, 'Microsoft offers buyouts to about <i>60,000</i> people.', 'Roughly a quarter of its workforce is eligible.',
          '<div class="cols">The offer is voluntary and time-limited. It covers eligible staff at level 70 and below in the U.S., U.K., Canada and India.<br><br>'
          'Staff have until early December to decide and would leave at the end of the year.</div>', src, swipe=True, extra=mast),
        S(T, 2, t, 'Who is <i>eligible?</i>', '',
          rows([("level", "70 and below"), ("countries", "US, UK, CA, IN"), ("eligible", "about 60,000")], top=640, gap=170), src, extra=mast),
        S(T, 3, t, 'When do they <i>decide?</i>', '',
          rows([("decide by", "early December"), ("leave", "end of the year")], top=700, gap=200), src, extra=mast),
        S(T, 4, t, 'Why <i>now?</i>', 'Reports tie it to cost control and heavy AI spending. Microsoft has not named AI as the reason.',
          '<div class="cols"><b>What reports say.</b> The buyouts help contain costs while the company spends heavily on AI.<br><br>'
          '<b>What Microsoft says.</b> Its people chief framed the offer as flexibility for employees.</div>', src, extra=mast),
        S(T, 5, t, 'Not the <i>first</i> offer this year.', 'A smaller buyout was offered earlier in 2026.',
          '<div class="x" style="left:72px;top:720px;font:700 330px/1 Fraunces,serif;letter-spacing:-.05em">2nd</div><div class="x lab" style="left:80px;top:1060px">buyout offer of 2026</div>', src, extra=mast),
        S(T, 6, t, 'AI spending is changing <i>who works</i> in tech.', 'Save this. We will follow how many accept.',
          '<div class="cols"><b>What to watch.</b> How many accept. Which teams shrink. Where the money goes next.<br><br>'
          'Microsoft has not said how many it expects to accept.</div>', "binarysemaphore.com", extra=mast),
    ]


def nuclear():
    T, t = "dark", "Energy &middot; Oct 6"
    src = "constellationenergy.com, Oct 6 2026"
    return [
        S(T, 1, t, 'AI needs power. Google is buying <i>nuclear.</i>', 'A 20-year deal with Constellation Energy.',
          '<div class="x y" style="left:72px;top:760px;font:700 300px/1 Space Grotesk,sans-serif;letter-spacing:-.06em">890<span style="font-size:120px">MW</span></div>', src, swipe=True),
        S(T, 2, t, '890 MW of <i>new</i> nuclear capacity.', 'From upgrading reactors that already run, not building new ones.',
          '<div class="x y" style="left:72px;top:760px;font:700 300px/1 Space Grotesk,sans-serif;letter-spacing:-.06em">+890</div><div class="x lab" style="left:80px;top:1070px">megawatts, from uprates</div>', src),
        S(T, 3, t, 'Where?', '11 Constellation-owned nuclear units in Illinois, Pennsylvania and New Jersey.',
          rows([("Illinois", "IL"), ("Pennsylvania", "PA"), ("New Jersey", "NJ")], top=760, gap=150), src),
        S(T, 4, t, 'When?', 'The first upgrade is expected by 2028.',
          '<div class="x y" style="left:72px;top:760px;font:700 300px/1 Space Grotesk,sans-serif;letter-spacing:-.06em">2028</div>', src),
        S(T, 5, t, 'The <i>money</i> and the deal.', '',
          rows([("Constellation invests", "$4.3B+"), ("power deal length", "20 years"), ("plus a supply deal", "2,700 MW")], top=680, gap=170), src),
        S(T, 6, t, 'Google can also <i>cut back</i> when the grid is stressed.', 'Non-critical use is curtailed in high-stress grid events. Save this.',
          '<svg class="v" style="color:#F2F0EB"><path class="tn" d="M 90 1120 L 990 1120"/><path class="th" d="M 100 1040 C 260 1000 380 860 520 800 L 560 800"/>'
          '<path class="th" d="M 560 800 L 640 800" style="stroke:#F4D23C;stroke-dasharray:4 18"/><path class="th" d="M 640 800 L 680 940 C 760 1000 880 1020 980 1030"/>'
          '<path class="th" d="M 680 940 L 700 800" style="stroke:#F4D23C"/></svg><div class="x lab y" style="left:470px;top:740px">grid stress: cut back</div>', "binarysemaphore.com"),
    ]


def curve():
    """11: the AI coding curve (the single post the owner liked), one stage per slide; the yellow dot moves along it."""
    T, t = "cobalt", "Coding with AI"
    knot, r = [], 11
    def rnd():
        nonlocal r
        r = (r * 9301 + 49297) % 233280
        return r / 233280
    import math
    pts = [(200, 1180), (330, 1010)]
    for k in range(22):
        a, R = k * 1.9 + rnd() * .8, 35 + rnd() * 52
        pts.append((420 + math.cos(a) * R + (rnd() - .5) * 26, 1000 + math.sin(a) * R * .85))
    pts += [(500, 990), (540, 950), (680, 820)]
    d = f"M {pts[0][0]} {pts[0][1]}"
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C {c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p2[0]:.0f} {p2[1]:.0f}"
    base = (f'<path class="tn" d="M 160 1220 L 160 640 M 160 1220 L 960 1220"/><path class="th" style="stroke-width:7" d="{d}"/>'
            '<path class="th" style="stroke-width:7" d="M 680 820 L 690 1160 L 930 660"/>')
    stops = {"codes": (205, 1175), "knot": (420, 1000), "accept": (680, 820), "deleted": (690, 1160), "diff": (930, 660)}
    def chart(k):
        x, y = stops[k]
        return (f'<svg class="v" style="color:#F3EDDC;top:-90px">{ROUGHC}<g filter="url(#rc)">{base}</g>'
                f'<circle cx="{x}" cy="{y}" r="26" fill="#F4D23C"/><circle cx="{x}" cy="{y}" r="44" fill="none" stroke="#F4D23C" stroke-width="4" stroke-dasharray="8 8"/></svg>'
                '<div class="x lab" style="left:110px;top:510px">trust</div><div class="x lab" style="left:900px;top:1150px">time</div>')
    return [
        S(T, 1, t, 'The AI <i>coding</i> curve.', 'Where are you on it?', f'<svg class="v" style="color:#F3EDDC;top:-90px">{ROUGHC}<g filter="url(#rc)">{base}</g></svg>'
          '<div class="x lab" style="left:110px;top:510px">trust</div><div class="x lab" style="left:900px;top:1150px">time</div>', "swipe for each stage", swipe=True),
        S(T, 2, t, '&ldquo;It <span class="blk">codes!</span>&rdquo;', 'The first hour. It writes a whole feature and you cannot believe it.', chart("codes"), "stage 1 of 5"),
        S(T, 3, t, '&ldquo;Wait, what did it <i>change?</i>&rdquo;', 'Twelve files touched. You asked for one.', chart("knot"), "stage 2 of 5"),
        S(T, 4, t, '&ldquo;<span class="blk">Accept all.</span>&rdquo;', 'It worked last time. You stop reading.', chart("accept"), "stage 3 of 5"),
        S(T, 5, t, '&ldquo;It deleted my <i>tests.</i>&rdquo;', 'The build is green because the checks are gone.', chart("deleted"), "stage 4 of 5"),
        S(T, 6, t, '&ldquo;I read <span class="blk">every</span> diff.&rdquo;', 'Small tasks, real tests, every change read. That is the top of the curve. Save this.', chart("diff"), "stage 5 of 5"),
    ]


CAROUSELS = {"01-anthropic-ipo": ipo, "02-gemini-carbon": carbon, "03-opera-webai": webai, "04-agent-protocol": agents,
             "05-october-in-ai": october, "06-ai-prices": prices, "07-eu-ai-act": eu, "08-ai-deals": deals,
             "09-microsoft-buyouts": buyouts, "10-ai-nuclear": nuclear, "11-ai-coding-curve": curve}

FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,700;"
         "1,9..144,300;1,9..144,400&family=Inter+Tight:wght@500;600;700;800&family=Space+Grotesk:wght@300;400;500;700&family=JetBrains+Mono:wght@500&display=swap")

if __name__ == "__main__":
    for slug, make in CAROUSELS.items():
        d = HERE / slug
        d.mkdir(exist_ok=True)
        html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{slug}</title><link rel="stylesheet" href="{FONTS}">'
                f'<style>{BASE}{"".join(THEMES.values())}</style></head><body>' + "\n".join(make()) + "</body></html>\n")
        (d / "slides.html").write_text(html)
        print(slug)
