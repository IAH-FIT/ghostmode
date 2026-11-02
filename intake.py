"""Intake for the evidence archive: one Internet Archive item -> one archive text file with a header.

    python3 intake.py <identifier> [<identifier> ...]

Takes the item's OCR text (the *_djvu.txt file) and the item's own metadata for the header, so every document says where it
came from. Judge the item before you run this: primary record only (the report, the hearing, the memo), never a book about it.
Raw downloads land in RAW_DIR and are untrusted data; the archive file is the only thing the board reads.
"""
import json, os, re, sys, urllib.request

ARCHIVE_DIR = os.environ.get("QB_ARCHIVE", "/root/archive")
RAW_DIR = os.environ.get("QB_ARCHIVE_RAW", "/root/archive-raw")


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "askboard-ghostmode-intake/1 (hello@askboard.ai)"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def intake(ident):
    meta = json.loads(fetch("https://archive.org/metadata/%s" % ident))
    m = meta.get("metadata", {})
    txt = [f["name"] for f in meta.get("files", []) if f["name"].endswith("_djvu.txt")]
    if not txt:
        return "%s: no OCR text file" % ident
    name = txt[0]
    os.makedirs(RAW_DIR, exist_ok=True); os.makedirs(ARCHIVE_DIR, exist_ok=True)
    raw = fetch("https://archive.org/download/%s/%s" % (ident, urllib.request.quote(name)), timeout=600)
    open(os.path.join(RAW_DIR, ident + ".txt"), "wb").write(raw)
    body = raw.decode("utf-8", "ignore")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    title = m.get("title", ident)
    title = title if isinstance(title, str) else title[0]
    date = str(m.get("date") or m.get("year") or "")[:10]
    who = m.get("creator", "")
    who = who if isinstance(who, str) else ", ".join(who)
    head = "Title: %s\nSource: https://archive.org/details/%s\nDate: %s\nType: primary record, %s, scanned text (OCR, so spellings can be off)\n\n" % (
        title.strip(), ident, date, who.strip() or "Internet Archive")
    out = os.path.join(ARCHIVE_DIR, re.sub(r"[^A-Za-z0-9_-]", "-", ident)[:80] + ".txt")
    open(out, "w", encoding="utf-8").write(head + body)
    return "%s: %s (%d characters) -> %s" % (ident, title[:60], len(body), out)


if __name__ == "__main__":
    for ident in sys.argv[1:]:
        try:
            print(intake(ident))
        except Exception as e:
            print("%s: failed, %s" % (ident, type(e).__name__))
