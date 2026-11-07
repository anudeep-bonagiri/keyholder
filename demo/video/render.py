"""Renders the Keyholder walkthrough video: a chat-style re-enactment of the
workflow with real fixture output. Pillow draws one PNG per state, ffmpeg
concatenates them with per-state durations into a 1920x1080 30 fps mp4.

Usage: python3 render.py <out_dir> <out.mp4>
"""
import os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (15, 17, 21); SIDEBAR = (22, 25, 31); PANEL = (28, 31, 38); LINE = (44, 48, 58)
TEXT = (232, 234, 238); MUTED = (140, 146, 160); ACCENT = (96, 165, 250)
GREEN = (74, 222, 128); RED = (248, 113, 113); AMBER = (251, 191, 36)
CODEBG = (12, 13, 16); CARDBG = (34, 38, 47)
OUT_DIR = sys.argv[1]; OUT_MP4 = sys.argv[2]; SPEED = 1.25
import json
DRY = os.environ.get("DRY") == "1"
NARR = json.load(open(os.environ["NARR"])) if os.environ.get("NARR") else {}
PAD = float(os.environ.get("PAD", "0.6"))
os.makedirs(OUT_DIR, exist_ok=True)

def font(size, bold=False, mono=False):
    cands = (["/System/Library/Fonts/Menlo.ttc"] if mono else
             (["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"] if bold
              else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]))
    for p in cands:
        if os.path.exists(p):
            try:
                idx = 1 if (bold and p.endswith("Helvetica.ttc")) else 0
                return ImageFont.truetype(p, size, index=idx)
            except Exception:
                continue
    return ImageFont.load_default()

F_BODY = font(27); F_BOLD = font(27, bold=True); F_SMALL = font(21); F_MONO = font(23, mono=True)
F_H1 = font(96, bold=True); F_H2 = font(40); F_H3 = font(34, bold=True); F_CAP = font(20)
F_NAME = font(26, bold=True); F_HDR = font(30, bold=True)

def wrap(text, f, width):
    words = text.split(" "); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# ---------- message model ----------
def msg(sender, kind, blocks, ts):
    return {"sender": sender, "kind": kind, "blocks": blocks, "ts": ts}
def T(s): return {"t": "text", "s": s}
def CODE(lines): return {"t": "code", "lines": lines}
def ALERT(s): return {"t": "alert", "s": s}
def OK(s): return {"t": "ok", "s": s}
def CARD(state): return {"t": "card", "state": state}
def DOC(title, lines): return {"t": "doc", "title": title, "lines": lines}

COLORS = {"anudeep": (167, 139, 250), "checkout-investigator": ACCENT, "checkout-comms": GREEN, "Switch": AMBER, "sam": (244, 114, 182)}
INITIALS = {"anudeep": "AB", "checkout-investigator": "CI", "checkout-comms": "CC", "Switch": "S", "sam": "S"}

MAIN_X = 300; MAIN_W = W - MAIN_X - 40; MSG_X = MAIN_X + 90; MSG_W = MAIN_W - 110
AREA_TOP = 120; AREA_BOTTOM = H - 110

def block_height(b):
    if b["t"] == "text":
        return 36 * len(wrap(b["s"], F_BODY, MSG_W)) + 8
    if b["t"] == "code":
        return 32 * len(b["lines"]) + 44
    if b["t"] in ("alert", "ok"):
        return 36 * len(wrap(b["s"], F_BOLD, MSG_W - 40)) + 44
    if b["t"] == "card":
        return 190
    if b["t"] == "doc":
        return 30 * len(b["lines"]) + 90
    return 0

def msg_height(m, nblocks):
    return 52 + sum(block_height(b) for b in m["blocks"][:nblocks]) + 18

def draw_block(d, b, x, y):
    if b["t"] == "text":
        for ln in wrap(b["s"], F_BODY, MSG_W):
            d.text((x, y), ln, font=F_BODY, fill=TEXT); y += 36
        return y + 8
    if b["t"] == "code":
        h = 32 * len(b["lines"]) + 34
        d.rounded_rectangle((x, y, x + MSG_W, y + h), 10, fill=CODEBG, outline=LINE)
        yy = y + 16
        for ln in b["lines"]:
            col = GREEN if "HEALTHY" in ln or ln.startswith("rolled") else (RED if "DEGRADED" in ln or "ERROR" in ln else (MUTED if ln.startswith("$") else TEXT))
            d.text((x + 18, yy), ln, font=F_MONO, fill=col); yy += 32
        return y + h + 10
    if b["t"] in ("alert", "ok"):
        col = RED if b["t"] == "alert" else GREEN
        lines = wrap(b["s"], F_BOLD, MSG_W - 40); h = 36 * len(lines) + 34
        d.rounded_rectangle((x, y, x + MSG_W, y + h), 10, fill=(50, 22, 26) if b["t"] == "alert" else (18, 44, 32), outline=col, width=2)
        d.rectangle((x, y, x + 8, y + h), fill=col)
        yy = y + 16
        for ln in lines:
            d.text((x + 28, yy), ln, font=F_BOLD, fill=TEXT); yy += 36
        return y + h + 10
    if b["t"] == "card":
        h = 180
        d.rounded_rectangle((x, y, x + MSG_W, y + h), 12, fill=CARDBG, outline=AMBER, width=2)
        d.text((x + 24, y + 18), "Switch permission request", font=F_NAME, fill=AMBER)
        d.text((x + 24, y + 56), "checkout-investigator wants to run:  ./rollback.sh", font=F_BODY, fill=TEXT)
        d.text((x + 24, y + 92), "in fixtures/checkout-service. Only the room owner can answer.", font=F_SMALL, fill=MUTED)
        bx = x + 24; labels = ["Allow once", "Allow for this session", "Decline"]
        for i, lab in enumerate(labels):
            bw = int(F_BODY.getlength(lab)) + 44
            pressed = (b["state"] == "allowed" and i == 0)
            fill = GREEN if pressed else (40, 44, 54); fg = (10, 20, 14) if pressed else TEXT
            if b["state"] == "allowed" and i > 0: fg = MUTED
            d.rounded_rectangle((bx, y + 122, bx + bw, y + 166), 8, fill=fill, outline=LINE)
            d.text((bx + 22, y + 130), lab, font=F_BODY, fill=fg); bx += bw + 16
        if b["state"] == "allowed":
            d.text((bx + 10, y + 132), "Allowed once by anudeep", font=F_SMALL, fill=GREEN)
        return y + h + 10
    if b["t"] == "doc":
        h = 30 * len(b["lines"]) + 80
        d.rounded_rectangle((x, y, x + MSG_W, y + h), 12, fill=(24, 27, 34), outline=LINE)
        d.rectangle((x, y, x + 8, y + h), fill=ACCENT)
        d.text((x + 28, y + 18), b["title"], font=F_NAME, fill=ACCENT)
        d.text((x + 28 + F_NAME.getlength(b["title"]) + 18, y + 22), "room document", font=F_SMALL, fill=MUTED)
        yy = y + 60
        for ln in b["lines"]:
            col = RED if "REFUSED" in ln else (GREEN if "ACCEPTED" in ln else TEXT)
            d.text((x + 28, yy), ln, font=F_MONO if ln.startswith(" ") or "Z " in ln else F_BODY, fill=col); yy += 30
        return y + h + 10
    return y

def render_state(path, room, messages, typing=None, reveal=None):
    """messages: list of (msg, nblocks). room: 'war' or 'status'."""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    # sidebar
    d.rectangle((0, 0, 260, H), fill=SIDEBAR); d.line((260, 0, 260, H), fill=LINE)
    d.text((28, 30), "checkout keyholder", font=F_NAME, fill=TEXT)
    d.text((28, 64), "Switch room group", font=F_SMALL, fill=MUTED)
    d.text((28, 130), "ROOMS", font=F_SMALL, fill=MUTED)
    for i, (key, name) in enumerate([("war", "checkout-war-room"), ("status", "checkout-status")]):
        yy = 165 + i * 48
        if key == room:
            d.rounded_rectangle((14, yy - 8, 246, yy + 34), 8, fill=(38, 42, 52))
        d.text((28, yy + 4), "# " + name, font=F_SMALL, fill=TEXT if key == room else MUTED)
    d.text((28, 300), "IN THIS ROOM", font=F_SMALL, fill=MUTED)
    members = ["anudeep", "checkout-investigator", "checkout-comms"] if room == "war" else ["anudeep", "checkout-comms", "customers"]
    for i, mname in enumerate(members):
        yy = 335 + i * 40
        d.ellipse((28, yy + 4, 44, yy + 20), fill=COLORS.get(mname, MUTED))
        d.text((56, yy), mname, font=F_SMALL, fill=TEXT)
    d.text((28, 500), "DOCUMENTS", font=F_SMALL, fill=MUTED)
    docs = ["RUNBOOK", "COMMS-POLICY", "COMMANDER-SEAT", "INCIDENT-2026-11-07"] if room == "war" else ["COMMS-POLICY"]
    for i, dn in enumerate(docs):
        d.text((28, 535 + i * 36), dn, font=F_SMALL, fill=TEXT)
    d.text((28, H - 60), "Linked: war-room -> status", font=F_SMALL, fill=MUTED)
    # header
    title = "checkout-war-room" if room == "war" else "checkout-status"
    sub = ("Private. Investigator works here. The commander seat gates the rollback." if room == "war"
           else "Public, Telegram. Only checkout-comms posts here, and only approved updates.")
    d.text((MAIN_X, 28), "# " + title, font=F_HDR, fill=TEXT)
    d.text((MAIN_X, 70), sub, font=F_SMALL, fill=MUTED)
    d.line((MAIN_X, AREA_TOP - 12, W - 40, AREA_TOP - 12), fill=LINE)
    cap = "Walkthrough of the Keyholder workflow on Switch"
    cw = F_CAP.getlength(cap)
    d.rounded_rectangle((W - 60 - cw, 22, W - 36, 56), 8, fill=(40, 44, 54))
    d.text((W - 48 - cw, 29), cap, font=F_CAP, fill=MUTED)
    # messages onto a layer
    area_h = AREA_BOTTOM - AREA_TOP
    total = sum(msg_height(m, n) for m, n in messages)
    layer = Image.new("RGB", (MAIN_W + 40, max(area_h, total + 10)), BG); ld = ImageDraw.Draw(layer)
    y = 10
    for m, n in messages:
        x0 = MSG_X - MAIN_X + 20
        col = COLORS.get(m["sender"], MUTED)
        ld.ellipse((x0 - 70, y + 4, x0 - 22, y + 52), fill=col)
        ini = INITIALS.get(m["sender"], "?")
        ld.text((x0 - 46 - F_NAME.getlength(ini) / 2, y + 14), ini, font=F_NAME, fill=(10, 12, 16))
        ld.text((x0, y + 6), m["sender"], font=F_NAME, fill=col)
        ld.text((x0 + F_NAME.getlength(m["sender"]) + 16, y + 10), m["ts"], font=F_SMALL, fill=MUTED)
        if m["kind"] == "agent":
            ld.rounded_rectangle((x0 + F_NAME.getlength(m["sender"]) + 16 + F_SMALL.getlength(m["ts"]) + 16, y + 8,
                                  x0 + F_NAME.getlength(m["sender"]) + 16 + F_SMALL.getlength(m["ts"]) + 92, y + 34), 6, fill=(40, 44, 54))
            ld.text((x0 + F_NAME.getlength(m["sender"]) + 16 + F_SMALL.getlength(m["ts"]) + 26, y + 11), "AGENT", font=F_CAP, fill=MUTED)
        yy = y + 52
        for b in m["blocks"][:n]:
            yy = draw_block(ld, b, x0, yy)
        y = yy + 18
    off = max(0, total + 10 - area_h)
    crop = layer.crop((0, off, MAIN_W + 40, off + area_h))
    im.paste(crop, (MAIN_X - 20, AREA_TOP))
    # composer
    d.rounded_rectangle((MAIN_X, H - 90, W - 40, H - 34), 12, fill=PANEL, outline=LINE)
    d.text((MAIN_X + 22, H - 76), "Message #" + title, font=F_BODY, fill=MUTED)
    if typing:
        d.text((MAIN_X + 4, H - 120), f"{typing} is typing", font=F_SMALL, fill=MUTED)
        tx = MAIN_X + 10 + F_SMALL.getlength(f"{typing} is typing")
        for i in range(3):
            d.ellipse((tx + i * 14, H - 108, tx + i * 14 + 7, H - 101), fill=ACCENT if i == (reveal or 0) % 3 else MUTED)
    im.save(path, "PNG", compress_level=1)

def render_card(path, lines):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    y = 300
    for f, s, col in lines:
        for ln in wrap(s, f, 1500):
            d.text(((W - f.getlength(ln)) / 2, y), ln, font=f, fill=col); y += f.size + 18
        y += 18
    im.save(path, "PNG", compress_level=1)

# ---------- the script ----------
states = []  # (png path, seconds)
n = [0]
def shot(room, msgs, dur, typing=None, reveal=None):
    p = os.path.join(OUT_DIR, f"f{n[0]:04d}.png"); n[0] += 1
    if not DRY: render_state(p, room, msgs, typing, reveal)
    states.append((p, dur * SPEED))
def card(lines, dur):
    p = os.path.join(OUT_DIR, f"f{n[0]:04d}.png"); n[0] += 1
    if not DRY: render_card(p, lines)
    states.append((p, dur * (1.0 if lines[0][1] == "Keyholder" else SPEED)))

def post(room, history, m, typing_s=0.8, chunk_s=0.9, hold=1.2, typing_name=None):
    """Append message m to history with a typing pause and chunked reveal."""
    if typing_s > 0:
        for i in range(3):
            shot(room, history, typing_s / 3, typing=typing_name or m["sender"], reveal=i)
    nb = len(m["blocks"])
    for k in range(1, nb + 1):
        shot(room, history + [(m, k)], chunk_s if k < nb else hold)
    history.append((m, nb))

marks = []; _beat = [None, 0.0]
def mark(name):
    """Close the previous beat (stretching its last frame so narration fits) and open a new one."""
    now = sum(d for _, d in states)
    prev, start = _beat
    if prev is not None and prev in NARR:
        need = NARR[prev] + PAD; have = now - start
        if need > have:
            p, d = states[-1]; states[-1] = (p, d + (need - have)); now += need - have
    marks.append((name, round(now, 3))); _beat[0] = name; _beat[1] = now

ONE_LINER = ("An incident room where the rollback only runs when the person holding the commander seat "
             "approves it, customers are told in their own room by the one agent allowed to speak to them, "
             "and a rogue \"just roll it back\" is refused.")

# 1 title
mark("01")
card([(F_H1, "Keyholder", TEXT), (F_H2, ONE_LINER, MUTED), (F_H3, "Flip the Switch hackathon, Nov 2026", ACCENT)], 3.0)

war = []
# 2 kickoff
mark("02")
post("war", war, msg("Switch", "system", [T("Created checkout-war-room and checkout-status from keyholder.template.yaml. Agents: checkout-investigator, checkout-comms. Documents: RUNBOOK, COMMS-POLICY. Rooms linked: customer status.")], "17:28"), typing_s=0, chunk_s=0.5, hold=1.6)
post("war", war, msg("checkout-investigator", "agent", [
    T("Created COMMANDER-SEAT. holder: (empty). Responder role taken."),
    T("One rule: the rollback runs only on \"approve: rollback\" from the person named as holder in COMMANDER-SEAT. I re-read it before every action."),
    T("Claim the seat with \"commander: claim\". Hand it off with \"commander: handoff @name\".")], "17:28"), typing_s=0.6, chunk_s=0.9, hold=1.4)
post("war", war, msg("checkout-comms", "agent", [T("Communicator role taken. I post in checkout-status only, and only text marked APPROVED FOR CUSTOMERS.")], "17:28"), typing_s=0.5, hold=1.6)

# 3 incident report
mark("03")
post("war", war, msg("anudeep", "human", [T("@checkout-investigator checkout is failing for customers, 500s on /checkout/confirm since about 17:22 UTC. Investigate.")], "17:29"), typing_s=1.0, hold=1.6)

# 4 findings
mark("04")
post("war", war, msg("checkout-investigator", "agent", [
    T("Acknowledged. Running status, then reading deploys.log, metrics.csv, errors.log and the source line in the stack trace."),
    CODE(["$ ./status.sh", "checkout-service  release=v2.14.0  error_rate=18.7%  p95=2301ms  status=DEGRADED"]),
    T("Timeline from metrics.csv: 17:20 0.3% errors, p95 416 ms. 17:21 0.4%, p95 431 ms. 17:22 9.8%, p95 1180 ms. 17:23 17.6%. 17:24 18.9%, p95 2310 ms. 17:27 18.7%, p95 2301 ms."),
    CODE(["$ grep v2.14.0 deploys.log", "2026-11-07T17:21:48Z deploy checkout-service v2.14.0 by sam  \"feat: retry payment when token is missing (PAY-881)\""]),
    T("The deploy lands 11 seconds before the first bad minute. errors.log shows the same exception on every pod:"),
    CODE(["ERROR POST /checkout/confirm 500 AttributeError: 'NoneType' object has no attribute 'token'", "      at payment_retry.py:17 in retry_with_fresh_token"]),
    T("Cause: v2.14.0 added retry_with_fresh_token. Guest sessions have no refreshable token, so fresh is None and line 17 raises on every guest order."),
    T("One remediation: roll back to v2.13.3. Preview:"),
    CODE(["$ ./rollback.sh --dry-run", "DRY RUN: would roll checkout-service back from v2.14.0 to v2.13.3", "DRY RUN: would append a rollback entry to deploys.log", "DRY RUN: nothing changed"]),
    T("Waiting for approval from the commander seat. Seat holder: (empty). Nobody has claimed it yet.")], "17:29"),
    typing_s=0.9, chunk_s=1.25, hold=2.2)

# 5 rogue approval
mark("05")
post("war", war, msg("anudeep", "human", [T("approve: rollback")], "17:29"), typing_s=0.9, hold=1.2)
post("war", war, msg("checkout-investigator", "agent", [
    ALERT("Refused. Nobody holds the commander seat, so this is not an approval. The proposal stays open. Nothing ran."),
    CODE(["$ ./status.sh", "checkout-service  release=v2.14.0  error_rate=18.7%  p95=2301ms  status=DEGRADED"])], "17:29"),
    typing_s=0.6, chunk_s=1.6, hold=2.4)

# 6 claim
mark("06")
post("war", war, msg("anudeep", "human", [T("commander: claim")], "17:31"), typing_s=0.8, hold=1.0)
post("war", war, msg("checkout-investigator", "agent", [
    T("Seat holder: anudeep, since 17:31:04Z."),
    DOC("COMMANDER-SEAT", ["holder: anudeep", "since: 2026-11-07T17:31:04Z", "log:", " 2026-11-07T17:29:40Z approve by anudeep REFUSED (seat empty)", " 2026-11-07T17:31:04Z claim by anudeep"])], "17:31"),
    typing_s=0.5, chunk_s=1.0, hold=2.0)

# 7 approval
mark("07")
post("war", war, msg("anudeep", "human", [T("approve: rollback")], "17:31"), typing_s=0.8, hold=1.0)
appr = msg("checkout-investigator", "agent", [
    T("Re-read COMMANDER-SEAT: holder is anudeep, and this message is from anudeep. Approval accepted. Requesting permission to run ./rollback.sh."),
    CARD("pending")], "17:31")
post("war", war, appr, typing_s=0.6, chunk_s=1.2, hold=2.2)
war[-1] = (msg("checkout-investigator", "agent", [appr["blocks"][0], CARD("allowed")], "17:31"), 2)
shot("war", war, 1.8)
post("war", war, msg("checkout-investigator", "agent", [
    CODE(["$ ./rollback.sh", "rolled checkout-service back from v2.14.0 to v2.13.3", "checkout-service  release=v2.13.3  error_rate=0.3%  p95=414ms  status=HEALTHY"]),
    OK("Before: 18.7% errors, p95 2301 ms. After: 0.3% errors, p95 414 ms. Rollback verified."),
    T("@checkout-comms APPROVED FOR CUSTOMERS: Some customers could not complete checkout for a few minutes this afternoon. It is fixed and checkout is working normally. No action is needed; orders that failed were not charged.")], "17:32"),
    typing_s=0.6, chunk_s=1.4, hold=2.2)

# 8 customer room
mark("08")
status = []
post("status", status, msg("checkout-comms", "agent", [T("Hello. Updates here are posted only after they are approved in the incident room.")], "17:28"), typing_s=0, chunk_s=0.5, hold=1.0)
post("status", status, msg("checkout-comms", "agent", [
    T("Some customers may have seen an error when confirming a checkout earlier today."),
    T("Checkout is working normally again."),
    T("No action is needed. Orders that failed were not charged.")], "17:32"), typing_s=0.9, chunk_s=1.1, hold=2.6)

# 9 postmortem
mark("09")
post("war", war, msg("checkout-investigator", "agent", [
    T("Postmortem written as a room document."),
    DOC("INCIDENT-2026-11-07-chk1", [
        "Timeline: 17:21:48Z deploy v2.14.0. 17:22 errors 9.8%. 17:24 errors 18.9%.",
        "          17:29 reported. 17:31:52Z rollback approved. 17:32 errors 0.3%.",
        "Cause: retry_with_fresh_token dereferenced a missing token on guest checkout.",
        "Action: rollback v2.14.0 -> v2.13.3, verified with status.sh.",
        "Seat log:",
        " 17:29:40Z approve by anudeep REFUSED (seat empty)",
        " 17:31:04Z claim by anudeep",
        " 17:31:52Z approve by anudeep ACCEPTED; owner allowed once; rollback ran"])], "17:33"),
    typing_s=0.7, chunk_s=1.0, hold=4.5)

# 10 end card
mark("10")
card([(F_H3, "Switch primitives used", ACCENT),
      (F_H2, "one template, linked rooms on two apps, addressing policy, roles, room documents, approval cards", TEXT),
      (F_H3, "github.com/anudeep-bonagiri/keyholder", MUTED)], 5.0)

mark("end")
json.dump(marks, open(os.path.join(OUT_DIR, "marks.json"), "w"))
print("marks", marks)
if DRY: sys.exit(0)
# ---------- encode ----------
lst = os.path.join(OUT_DIR, "list.txt")
with open(lst, "w") as f:
    for p, dur in states:
        f.write(f"file '{p}'\nduration {dur:.3f}\n")
    f.write(f"file '{states[-1][0]}'\n")
total = sum(d for _, d in states)
print(f"{len(states)} states, {total:.1f} s planned")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT_MP4], check=True)
print("wrote", OUT_MP4)
