# chat/logs/

Chat transcripts from test sessions, one `.jsonl` file per server run,
enabled by setting `ANLLMS_CHAT_LOG=1` before starting the chat server.
See `chat/logging_utils.py` for the logging code.

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
