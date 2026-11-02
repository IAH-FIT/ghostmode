# Ghost Mode: the pipe

This is the code that handles a question on AskBoard Ghost Mode (askboard.ai/ghostmode): where it goes, what sees it, and
that nothing keeps it. It is published so anyone can check the promise instead of taking our word.

## Check it yourself

1. Open https://askboard.ai/ghostmode/verify. It reads the running machine and shows the digest of every file in this repo
   that is running right now.
2. Take the digests of the files here:

       shasum -a 256 server.py archive.py intake.py start-engine.sh start-board.sh

3. If they match, the code you are reading is the code that answered.

## What is here

- `server.py`: one process, in memory only. Receives the question, runs the board, streams the answer, keeps nothing.
  No database, no files written, access log off, errors logged by type only. It refuses to start if the AI engine is
  anywhere but this machine, or if no password is set.
- `archive.py`: offline search over public primary documents kept on the machine's own disk (declassified files,
  hearings, reports), quoted to the seats with their source. The only files the board reads.
- `intake.py`: how a public document gets into that archive, with its source in the header.
- `start-engine.sh`, `start-board.sh`: how the engine and the board are started. The engine binds to this machine only
  and its log is off.
- `verify.html`: the verification page.
- `ZERO-RETENTION.md`: the retention promise, item by item, with how each is checked.
- `brain.py` here is a stand-in with the same shape as the private one, so the pipe runs and `python3 test_board.py`
  passes. The real brain (the seats, their roles and prompts) is ours and stays private; its digest is on the verify page.

## What is not a promise

The request reaches the machine through a website host and a network provider, encrypted, as every website's traffic
does; they see connection details and we do not control their logs. The microphone on the page uses the browser's own
speech service. Both are said on the page and in the privacy notice.

Copyright Zero Point Collective LLC. Published for verification; all rights reserved.
