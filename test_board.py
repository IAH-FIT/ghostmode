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
    b, kept = A.brief(hits); assert "[R1]" in b and "1967-07-27" in b and kept == hits and A.brief([]) == ("", [])
    assert A.brief(hits, limit=10) == ("", [])   # nothing fits, nothing is claimed
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

# engine address: exact loopback only, no look-alikes, no override
assert S.engine_is_local("http://127.0.0.1:8081/v1") and S.engine_is_local("http://localhost:8081/x") and S.engine_is_local("http://[::1]:8081/x")
assert not S.engine_is_local("http://localhost.example.org/x") and not S.engine_is_local("https://127.0.0.1/x") and not S.engine_is_local("http://user@127.0.0.1/x")
# merge: the uncapped list reveals overflow
assert len(merge_claims([], ["c%d" % i for i in range(30)], cap=None)) == 30
print("loopback and overflow tests pass")

# attach strips fake record marks; the Reader fails closed on prose
assert "[R4]" not in S.attach("q", "see [R4] Declassified memo")
assert "[R4]" in S.attach("q [R4]", "")   # the question itself is never rewritten
import archive as _A2
assert _A2.tokens("the government report") == [] and "northwoods" in _A2.tokens("Operation Northwoods")
print("attach and stopword tests pass")

# three engines: seats dealt round the labs; checkers and the Reader never on the Chair's engine
_E, _C = S.ENGINES, S.CHAIR_ENGINE
S.ENGINES, S.CHAIR_ENGINE = ["http://127.0.0.1:8081/x", "http://127.0.0.1:8082/x", "http://127.0.0.1:8083/x"], 0
assert [S.seat_engine(i) for i in range(8)] == [0, 1, 2, 0, 1, 2, 0, 1]
assert all(S.checker_engine(ci) != 0 for ci in range(3)) and {S.checker_engine(ci) for ci in range(3)} == {1, 2}
assert S.checker_engine(len(S.ENGINES)) != 0
S.CHAIR_ENGINE = 1; assert all(S.checker_engine(ci) != 1 for ci in range(4))
S.ENGINES, S.CHAIR_ENGINE = ["http://127.0.0.1:8081/x"], 0; assert S.checker_engine(2) == 0   # one engine: everything shares it
S.ENGINES, S.CHAIR_ENGINE = _E, _C
import subprocess
r = subprocess.run([sys.executable, "-B", "-c", "import server"], env={**os.environ, "QB_ENGINES": "http://127.0.0.1:8081/x,http://10.0.0.5:8082/x"}, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
assert r.returncode != 0 and "must be this machine" in r.stderr, r.stderr   # one remote engine and the server refuses to start
print("three-engine tests pass")

# numbered verdicts parse whether an AI writes "1:", "1." or "1)"
for raw in ("1: ok | a\n2: wrong | b", "1. ok | a\n2. wrong | b", "1) ok | a\n2) wrong | b", "**1.** ok | a\n**2.** wrong | b"):
    d = S.parse(raw, ["1", "2"]); assert d.get("1", "").startswith("ok") and d.get("2", "").startswith("wrong"), (raw, d)
assert S.parse("SCORE. 40\nSCORE: 70", ["SCORE"]).get("SCORE") == "70"   # word keys still need a colon
print("verdict format tests pass")

# statements about the room and advice are not facts to check; facts stay
_c = S.claim_lines("- The AIs were split on the cause.\n- The Board agrees it was staged.\n- You should wait a year.\n- A proven manager would change the answer.\n- The Gulf of Tonkin Resolution passed on August 7, 1964.\n- The Senate vote was 88 to 2.")
assert _c == ["The Gulf of Tonkin Resolution passed on August 7, 1964.", "The Senate vote was 88 to 2."], _c
print("claim hygiene tests pass")

# a verdict behind an echoed template "N:" still reads; the board of a company is still a fact
import types
_orig = S.call
S.call = lambda *a, **k: S.parse("1. N: ok | fine\n2. N: wrong | no", ["1", "2"])
assert S.fact_check(0, {"headline": "h", "answer": "a", "holds": [], "risks": [], "would_change": "", "claims": ["x", "y"]}) == {1: "ok", 2: "wrong"}
S.call = _orig
assert S.claim_lines("- The board of Enron hid losses.\n- The Board agrees.") == ["The board of Enron hid losses."]
print("echoed-template tests pass")

# verdicts run together on one line still read; advice to the person is not a fact
assert S.parse("1: doubtful | No evidence. 2: ok | Fine. 3. N: wrong | No.", ["1", "2", "3"]) == {"1": "doubtful | No evidence.", "2": "ok | Fine.", "3": "N: wrong | No."}, S.parse("1: doubtful | No evidence. 2: ok | Fine. 3. N: wrong | No.", ["1", "2", "3"])
assert S.claim_lines("- The split turns on your ability to manage two sites.\n- You should keep the first location.\n- The SBA 7(a) program is run by the Small Business Administration.") == ["The SBA 7(a) program is run by the Small Business Administration."]
assert S.claim_lines("- Atoms split during nuclear fission.\n- Employers must keep payroll records for three years.") == ["Atoms split during nuclear fission.", "Employers must keep payroll records for three years."]   # facts that use the words split and must are still checked
print("one-line verdict and advice tests pass")

# the number follows the words: yes at its certainty, no mirrored, undecided at 50, old SCORE as fallback
assert S.verdict_score({"VERDICT": "No, it did not.", "SURE": "95"}) == 5 and S.verdict_score({"VERDICT": "yes", "SURE": "80"}) == 80
assert S.verdict_score({"VERDICT": "Undecided", "SURE": "90"}) == 50 and S.verdict_score({"VERDICT": "no", "SURE": "20"}) == 50   # sure clamps to 50..100
assert S.verdict_score({"SCORE": "30"}) == 30 and S.verdict_score({}, 64) == 64
print("verdict score tests pass")

# numbered claim lists read like dashed ones; a fact that mentions "your" is still a fact; errors log the type only
assert S.claim_lines("1. The resolution passed in 1964.\n2) The vote was 88 to 2.\n- Insulin is made in your pancreas.") == ["The resolution passed in 1964.", "The vote was 88 to 2.", "Insulin is made in your pancreas."]
assert S.claim_lines("- You should wait.\nNONE") == []
import io, contextlib
_buf = io.StringIO()
with contextlib.redirect_stderr(_buf):
    try:
        raise ValueError("secret question text")
    except ValueError:
        S.Server.handle_error(None, None, ("127.0.0.1", 1))
assert "secret" not in _buf.getvalue() and "ValueError" in _buf.getvalue(), _buf.getvalue()
print("claim list and error-log tests pass")
