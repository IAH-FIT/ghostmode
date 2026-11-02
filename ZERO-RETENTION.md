# Ghost Mode: zero retention, what is true and how it is checked

Michael's spec (2026-11-02) against the machine, item by item. Ghost Mode only; the rest of AskBoard is untouched.
Re-check after any change to server.py, start-engine.sh, start-board.sh or the tunnel.

| Spec item | State | Evidence |
|---|---|---|
| 1. In-memory only, never disk | True on our machine. The question, attachment, seat answers and page live in one Python process and die when the run ends. No database, no cache, no temp file. | `grep -n "open(" server.py` writes nothing; `/root/qb.log` holds the start line and numbers only. Swap: an 8 GB host swap file we cannot switch off (container, not superuser); 0 bytes used, 950 GB RAM free, so it is not reached in practice. |
| 2. Metadata stripped | The origin never reads or stores IP, user agent or any account; there are no accounts. In transit, askboard.ai's host and the tunnel provider see the connection metadata of every request, as the privacy page says. We cannot strip headers inside a rewrite; we can only not keep them, and we do not. | `log_message` is a no-op in server.py; `/root/qb.log` has no addresses. |
| 3. Logs off for this route | Board: access log off, errors logged as type names only, never text. Engine: content never logged (0 question words in engine.log across every run so far); `--log-disable` is set for the next engine restart. Tunnel: connection events only, no request lines. Host side (askboard.ai request logs): not ours to switch off; the route is a rewrite, so no function runs and no runtime log line carries the body. | `grep -c -i "<question words>" /root/engine.log` = 0; `grep -cE "POST \|/api/" /root/cf-tunnel.log` = 0 real lines. |
| 4. Overwrite buffers with garbage | Not done, on purpose. Python strings cannot be overwritten in place, so a "wipe" would be theatre. What is true: every reference is dropped when the run returns, and the engine's slot memory is overwritten by the next request. We say "held in memory for this run only", not "wiped". | server.py `run()` returns; no module-level state holds a question. |
| 5. Upstream provider zero retention | There is no upstream provider. The engine is on this machine and the server refuses any engine address that is not loopback. | server.py startup guard on `QB_ENGINE`; `ps` shows `--host 127.0.0.1`. |

What a visitor is told: privacy.html and the "When privacy matters" block. Both say the question passes through the website host and network providers encrypted, is answered on one machine, and is never saved. Keep those sentences and this table in step.
