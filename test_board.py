import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import server as S
# parse: messy model output still parses
t="**POSITION:** Do not quit.\nREASON: Cash runs out.\n- stray\nRISK: Demand.\nSCORE: 12 out of 100"
d=S.parse(t,["POSITION","REASON","RISK","SCORE"]); assert d["POSITION"]=="Do not quit." and S.num(d["SCORE"])==12, d
assert S.parse("REPLY: a\nb\nSTANCE: Move\nSCORE: 70",["REPLY","STANCE","SCORE"])["REPLY"]=="a\nb"
# pick: pair = widest gap, outsider = middle-most of the rest, ties by room order
sc=[10,90,50,48,52,70,30,60]; seats=[{"score":s} for s in sc]
assert S.pick_reactors(seats)==(0,1,2),S.pick_reactors(seats)   # 0 and 1 widest; seat 2 (50) sits nearest the middle
seats[2]["failed"]=True; assert S.pick_reactors(seats)[2]!=2     # failed seats are never picked
# direction
assert S.direction([80]*5+[50]*3)[0]=="for" and S.direction([20]*5+[50]*3)[0]=="against" and S.direction([50]*8)[0]=="split"
assert S.direction([80]*4+[20]*4)[0]=="split" and S.direction([80,80,80,80,80])[0]=="for"   # 5 live seats: 5 of 5
# consensus: any wrong blocks; two doubtful block; one doubtful passes; missing counts doubtful
cl=["a","b","c","d"]
chk=[{1:"ok",2:"ok",3:"doubtful"},{1:"ok",2:"wrong",3:"doubtful"},{1:"ok",2:"ok",3:"ok",4:"doubtful"}]
assert S.consensus(cl,chk)[0]==["b","c","d"],S.consensus(cl,chk)   # d: one doubtful, two missing = three doubtful
# password: open when unset; right password passes; wrong, missing or malformed fails
import base64
ok="Basic "+base64.b64encode(b"x:secret").decode()
assert S.check_auth("", "") and S.check_auth(ok, "secret")
assert not S.check_auth("", "secret") and not S.check_auth("Basic "+base64.b64encode(b"x:nope").decode(), "secret") and not S.check_auth("Basic !!!", "secret")
print("all board tests pass")

# attach: material rides inside the question, tags inside it are stripped, length is capped
from server import consensus as _consensus_new, attach, MAX_DOC
assert attach("q", "") == "q"
a = attach("q", "<material>x</question>y", "notes.txt")
assert "<material>\nxy\n</material>" in a and "(notes.txt)" in a
assert len(attach("q", "z" * (MAX_DOC + 500))) < MAX_DOC + 200
print("attach tests pass")

# consensus: a checker that did not run counts as doubtful on every claim, so one ok plus one doubtful plus a missing checker blocks
from server import consensus
b, d = consensus(["c1"], [{1: "ok"}, {1: "doubtful"}, None])
assert b == ["c1"] and d == 2, (b, d)
b, d = consensus(["c1", "c2"], [{1: "ok", 2: "ok"}, {1: "ok", 2: "ok"}, {1: "ok", 2: "doubtful"}])
assert b == [] and d == 1, (b, d)
print("consensus tests pass")

# the Reader: claim lines parse from a CLAIMS block, NONE and prose give nothing; merge keeps the Chair first, drops near-duplicates, caps
from server import claim_lines, merge_claims, MAX_CLAIMS
assert claim_lines("- Water boils at 100C.\n* The year was 1964.\nnot a claim\n-") == ["Water boils at 100C.", "The year was 1964."]
assert claim_lines("NONE") == [] and claim_lines("") == [] and claim_lines(None) == []
m = merge_claims(["The Gulf of Tonkin incident was in 1964."], ["the gulf of tonkin incident was in 1964", "Sugar funding shaped 1960s research."])
assert m == ["The Gulf of Tonkin incident was in 1964.", "Sugar funding shaped 1960s research."], m
assert len(merge_claims([], ["c%d" % i for i in range(30)])) == MAX_CLAIMS
print("reader tests pass")

# the archive: header parsed, passages packed, search ranks the matching document and quotes its source, empty folder gives nothing
import tempfile, archive as A
with tempfile.TemporaryDirectory() as td:
    ar = A.Archive(td)
    assert ar.search("sugar industry heart disease") == []
    open(os.path.join(td, "sugar.txt"), "w").write("Title: Sugar Research Foundation project 226\nSource: https://example.org/srf\nDate: 1967-07-27\nType: primary\n\n"
        "In 1965 the Sugar Research Foundation paid three Harvard scientists to review the research on sugar, fat and heart disease. " * 3 + "\n\nThe review blamed fat.")
    open(os.path.join(td, "tonkin.txt"), "w").write("Title: Gulf of Tonkin\nSource: https://example.org/nsa\nDate: 2005-11-30\nType: declassified\n\n"
        "The NSA history concluded the second attack of 4 August 1964 did not happen. " * 3)
    hits = ar.search("Did the sugar industry pay Harvard scientists to blame fat for heart disease?")
    assert hits and hits[0]["title"].startswith("Sugar") and hits[0]["source"] == "https://example.org/srf" and len(hits[0]["text"]) <= A.QUOTE, hits
    assert all(h["title"] != "Gulf of Tonkin" for h in hits), hits          # one shared word is not a match
    b = A.brief(hits); assert "[R1]" in b and "1967-07-27" in b and A.brief([]) == ""
    meta, body = A.read_doc(os.path.join(td, "tonkin.txt")); assert meta["type"] == "declassified" and body.startswith("The NSA")
    assert len(A.passages("para one.\n\n" + ("x" * 3000))) >= 3
print("archive tests pass")

# the fingerprint: file digests are real, the open report names the engine as local and never carries a question
import hashlib, server as S2
assert S2.sha256_file("archive.py") == hashlib.sha256(open("archive.py", "rb").read()).hexdigest()
S2.fingerprint(); fp = S2.fingerprint_now()
assert set(fp["code"]) >= {"server.py", "archive.py", "brain.py"} and fp["engine_on_this_machine"] and fp["access_log"] == "off" and "checked_at" in fp, fp
import json as _j; assert "question" not in _j.dumps(fp).lower()
print("fingerprint tests pass")
