# chat/logs/

Chat transcripts from test sessions, one `.jsonl` file per server run,
enabled by setting `ANLLMS_CHAT_LOG=1` before starting the chat server.
See `chat/logging_utils.py` for the logging code.

## Combined transcript

`build_transcript.py` reads every `session_*.jsonl` file in this
directory and writes `ALL_SESSIONS_TRANSCRIPT.md`, a single
human-readable Markdown document with every test session in order,
each turn showing the user's message, the assistant's reply, any tool
calls, and their results. Run it after a test session (or several) to
refresh the combined document:

```bash
python chat/logs/build_transcript.py
```

It's a plain script (no package imports), so it runs directly -- no
`-m` flag needed, unlike `chat/server.py`. It fully rebuilds
`ALL_SESSIONS_TRANSCRIPT.md` from whatever `.jsonl` files exist each
time it's run, so it's safe to re-run after every new session and
never drifts out of sync. `ALL_SESSIONS_TRANSCRIPT.md` is generated,
not hand-edited -- treat `session_*.jsonl` as the source of truth.

**Current policy (test phase only):** these logs ARE committed to the
repository, by explicit project decision. This is only acceptable
because every test session run against this repo is verified to
contain no real farm or animal data before it happens -- see project
working agreements.

**This policy does not carry over to commercial/production use.** Once
real customer data is involved, logs must never be committed to git.
See `docs/architecture.md`'s open items for what a production logging
design needs instead (backend store, no git commit, disclosure/consent,
retention limits, access control + encryption at rest, legal review).
