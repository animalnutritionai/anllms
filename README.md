# Deploying anllms chat to PythonAnywhere

> **STATUS: NOT YET SET UP OR TESTED.** These steps have been written
> out and reasoned through, but nobody has walked through them yet. Do
> that before trusting this as a working deployment path -- see
> `docs/architecture.md`'s matching session-update entry for exactly
> what's unverified.

This gives you a permanent URL (`https://YOURUSERNAME.pythonanywhere.com`)
you can just open in Safari -- no Codespaces, no terminal startup ritual,
no killing terminals between sessions. Everything below happens in
PythonAnywhere's own browser dashboard (Consoles tab, Web tab, Files tab),
which uses simpler page-based screens rather than a dense live-updating
IDE.

## One-time setup

1. **Log in to PythonAnywhere**, go to the **Consoles** tab, start a new
   **Bash** console.

2. **Clone the repo:**
   ```bash
   git clone https://github.com/animalnutritionai/anllms.git
   ```

3. **Create a virtual environment** (PythonAnywhere's `mkvirtualenv` comes
   pre-installed):
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 anllms-env
   ```
   (If 3.10 isn't available on your account's Python versions list, use
   whichever 3.10+ version is offered.)

4. **Install the project into that virtualenv:**
   ```bash
   cd anllms
   pip install -e ".[chat]"
   ```

5. **Go to the Web tab**, click **Add a new web app**.
   - Choose **Manual configuration** (not the Flask template option --
     this repo already has its own app).
   - Choose the same Python version as step 3.

6. **On the Web tab, set:**
   - **Source code**: `/home/YOURUSERNAME/anllms`
   - **Virtualenv**: `/home/YOURUSERNAME/.virtualenvs/anllms-env`
     (the exact path `mkvirtualenv` created -- shown at the end of step 3's
     output if you want to double check)

7. **Click the WSGI configuration file link** (still on the Web tab). This
   opens PythonAnywhere's own editor for a file that already exists on
   your account (not part of this repo). **Delete everything in it** and
   replace with the contents of `deploy/pythonanywhere_wsgi_template.py`
   from this repo, after editing its two placeholders:
   - Your real path from step 6 in place of `project_home`
   - Your real Anthropic API key in place of the placeholder key

   Save.

8. **Back on the Web tab, click the green Reload button.**

9. **Open the URL shown at the top of the Web tab** in Safari. You should
   see the same chat page you were reaching via Codespaces port
   forwarding.

## Every time you update the code

After merging changes on GitHub (or editing directly there):

1. **Consoles tab -> open your existing Bash console** (or start a new
   one).
2. ```bash
   cd anllms
   git pull
   ```
3. **Web tab -> Reload** (green button).

That's the whole update cycle -- no rebuild, no new virtualenv, no
Codespaces.

## Chat test logging on PythonAnywhere

`ANLLMS_CHAT_LOG=1` is already set in the WSGI template above, so
sessions log the same way they did in Codespaces, to
`chat/logs/session_*.jsonl` inside your PythonAnywhere copy of the repo.
To pull those into the transcript and push them back to GitHub, use the
same Bash console:

```bash
cd anllms
bash chat/logs/publish_transcript.sh
```

## Known limitations of this setup (free PythonAnywhere tier)

- The web app may go idle after a period of no traffic and take a few
  seconds to wake up on the next request -- this is normal for the free
  tier, not a bug.
- **Free-tier network access confirmed**: `api.anthropic.com` is on
  PythonAnywhere's current allowlist for free accounts (checked directly
  against their published allowlist), so the chat bot's calls to Claude
  should work without upgrading. This is worth re-checking if it ever
  starts failing, since PythonAnywhere can change the allowlist.
