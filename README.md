# ANLLMS — Animal Nutrition Large Language Modeling System

Precision dairy cattle nutrition platform wrapping the University of
Guelph's `nasem_dairy` reference implementation of the NASEM (2021)
*Nutrient Requirements of Dairy Cattle* model. ANLLMS adds a
citation-backed explanation layer, a Flask-based chat interface, and
(eventually) a diet optimizer on top of real `nasem_dairy` calculations
-- it never reimplements the science independently. See
`docs/architecture.md` for the technical shape and open items.

## Current deployment (live)

The chat feature runs on **Render**, not PythonAnywhere -- PythonAnywhere's
free tier repeatedly hit its 512MB disk quota because of `nasem_dairy`'s
dependency tree, and that path was abandoned before ever going live (see
"Deployment history" below).

- **Live URL:** https://anllms-chat.onrender.com
- **Render service:** `anllms-chat` (service ID `srv-da7jf5jbc2fs73d2bpa0`),
  workspace `tea-d9mgsdjm8hqs73casv3g`
- **Chat model calls route through a self-hosted LiteLLM proxy** on Cloud
  Run (`https://litellm-proxy-700813965617.us-east1.run.app`), not
  directly to `api.anthropic.com`. `chat/server.py` uses the `openai`
  Python client pointed at that proxy's `base_url`.
- **Env vars set on the Render service** (Render dashboard -> service ->
  Environment tab; there is no `render.yaml` in this repo, so these are
  configured there, not in code):
  - `LITELLM_API_KEY`
  - `LITELLM_BASE_URL`
  - `ANLLMS_MODEL` -- selects which model alias the LiteLLM proxy routes
    to. Active proxy aliases: Gemini Flash, Gemini Flash Lite, Mistral
    Small, Mistral Large. **Known issue:** the `gemini-flash` alias
    currently points to a deprecated underlying model
    (`models/gemini-2.0-flash`); if chat responses start failing, check
    which alias `ANLLMS_MODEL` is set to and consider switching to a
    Mistral alias as a temporary unblock. The permanent fix is on the
    LiteLLM proxy's own Cloud Run config, outside this repo.

## Updating the live deployment

After merging changes to `main` on GitHub (or editing directly there via
GitHub's web editor):

1. Check the Render dashboard for this service -- if auto-deploy from
   GitHub is enabled, a push to `main` triggers a new deploy automatically.
   If not, trigger a manual deploy from the Render dashboard.
2. Confirm the new deploy is live by opening
   https://anllms-chat.onrender.com and running a real chat turn.

## Local/dev testing

GitHub Codespaces has been used for development (see
`docs/architecture.md`'s Codespaces session notes for the accessible,
screen-reader-friendly workflow). Correct startup command, because the
project uses absolute imports:

```bash
pip install -e ".[chat]"
python -m chat.server
```

(Not `python chat/server.py` -- that fails on the absolute imports.)

## Chat transcript logging (test phase only)

Opt-in via `ANLLMS_CHAT_LOG=1`, writing one timestamped `.jsonl` file per
server run to `chat/logs/`. **Current policy: these logs ARE committed to
the repo** (see `chat/logs/README.md`) -- an explicit, test-phase-only
decision, made because sessions are verified free of real farm/animal
data before being run. This does NOT carry over to any future commercial
use; before real customer data is ever logged, this needs a full
redesign (no git commit, a proper backend store, user disclosure/consent,
retention limits, access control, encryption at rest, legal review).

## Deployment history (for context, not a working path)

1. **PythonAnywhere** (free tier) -- explored first for a permanent,
   screen-reader-friendly URL. Repeatedly hit the free tier's 512MB disk
   quota due to `nasem_dairy`'s dependency tree; abandoned before ever
   going live. No `deploy/` directory remains in the repo -- that
   abandoned path has been fully removed, not just superseded.
2. **Render + LiteLLM proxy** (current) -- the working, live deployment
   described above.
