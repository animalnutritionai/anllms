# Session handoff -- Sept 20, 2026

**Next session's stated focus: `solve_diet.py` (the diet optimizer), not the chat UI.**

## What this session actually did (chat UI, `anllms/chat/static/index.html`)

- Markdown rendering for assistant responses via `marked` + `DOMPurify`
  (was raw text before).
- Full semantic restructure: `<header>` (banner landmark: title, tagline,
  New Conversation button) / `<main aria-label="Conversation">` (holds
  the `#chat` log) / `<form id="composer" aria-label="Send a message">`
  (input + Send, its own landmark, native submit so iOS "Go" key works).
  Each prompt+response pair is a `<section aria-label="Exchange N">` --
  a named, individually-jumpable landmark, not a plain `<article>`.
- Skip link to the composer; visually-hidden `<label>` supplementing the
  input's placeholder.
- Per-exchange actions: Copy (prompt + response, fully working), Edit /
  Good response / Bad response (**still unwired placeholders**), and
  **Retry (fully working)** -- re-sends the original prompt against the
  exact history-length snapshot taken before that exchange was first
  sent (not a guessed slice of the returned history, which can include
  intermediate tool-call turns), replaces the response in place, and
  only ever exists on the current latest exchange.
- Conversation persistence via `localStorage` (full exchange list +
  running API history + per-exchange history-length snapshot), restored
  on page load with the live region detached during bulk-restore so a
  refresh doesn't announce the entire history at once.
- New Conversation button: fixed top-right visually; in DOM order it
  sits right after the intro paragraph, before the chat log, per your
  request to keep visual and reading order independent.
- Color scheme: dark forest green `#1B5E20` (deliberately darker than
  plain CSS `forestgreen`, which fails 4.5:1 contrast with white text),
  gold headings, white/light-gray body text, light lavender links.
- Fixed a real Safari-iOS bug: no `<meta name="viewport">` tag existed
  at all, which was the actual cause of the focus-zoom behavior you saw
  -- fixed with `width=device-width, initial-scale=1` plus a 16px
  minimum input font size, deliberately *without* `maximum-scale=1` /
  `user-scalable=no` (those "fix" the same bug by disabling pinch-zoom
  entirely, which would harm low-vision users).

## Known limitations, confirmed this session

- **VoiceOver + braille "echo" (each label/sentence read twice):**
  confirmed to be an iOS/Safari-level VoiceOver bug, not a markup issue.
  Reproduced on the live deploy; resolved by clearing conversation
  history and restarting Safari. This matches a public forum report of
  a general (not site-specific) iOS 17/18 VoiceOver bug, and lines up
  with `CONTRACTABLE`'s confirmed finding that VoiceOver injects braille
  boundary markers at the display layer rather than the DOM. Not
  fixable from this codebase. Worth a Feedback Assistant report to
  Apple, same as the Contractable one.
- **Fragmented-looking paragraphs in responses:** the whitespace-node
  bug (stray empty text nodes between `<p>` tags from `white-space:
  pre-wrap` on the response container) was found and fixed. What
  remains -- multiple real `<p>` elements when the underlying LLM
  output itself contains a blank line between every sentence -- is a
  model-output-structure issue, not a DOM bug. Deliberately left as-is
  this session per your call to deprioritize it; worth a look if it
  keeps being distracting.

## Proposed `docs/architecture.md` addition

Not yet applied -- paste this in via GitHub's web editor wherever it
fits (a new `## Chat UI (frontend)` section, e.g. after `## Deployment`,
would match the doc's existing style):

---

## Chat UI (frontend) -- Sept 2026 session

`chat/static/index.html` was restructured for accessibility and given
working Retry:

- Semantic landmarks: `<header>` (banner) / `<main aria-label=
  "Conversation">` / `<form id="composer" aria-label="Send a message">`.
  Each exchange is a `<section aria-label="Exchange N">`, individually
  navigable as its own landmark region.
- Markdown rendering (`marked` + `DOMPurify`) replaces raw-text
  responses.
- Retry is fully wired: replays the original prompt against a recorded
  pre-exchange history-length snapshot (never a guessed slice of the
  returned history, which can include intermediate tool-call turns),
  and only ever exists on the current latest exchange.
- Edit / Good response / Bad response buttons exist but are still
  unwired placeholders.
- Conversation persists across reloads via `localStorage`.
- **Known limitation, confirmed OS-level, not a code bug:** intermittent
  VoiceOver + braille "echo" (labels/sentences read twice) on iOS
  Safari. Reproduced on the live deploy; resolved by clearing history
  and restarting Safari. Matches a public report of a general iOS
  17/18 VoiceOver bug and the `CONTRACTABLE` project's confirmed finding
  that VoiceOver injects braille boundary markers at the display layer,
  not the DOM. Not fixable in this codebase; a Feedback Assistant
  report to Apple would be the appropriate next step, mirroring
  Contractable's.
- **Known limitation, deliberately deferred:** markdown responses can
  render as several `<p>` elements where one might be expected, when
  the LLM's own output places a blank line between sentences. This is
  model-output structure, not a DOM defect (a real DOM whitespace bug
  from `white-space: pre-wrap` on the response container was found and
  fixed separately).

---

## Tomorrow: `solve_diet.py`

Per `architecture.md`'s existing "On the horizon" section, this was
already the identified next major piece of work once the DMI
actual-vs-predicted mode decision was resolved (it has been). Relevant
context already in place: `diet_request.py`'s `ObjectiveSpec` /
`IngredientBound` / `NutrientBound` / `SolveRequest` types are built and
tested ahead of the solver itself; the chosen engine is
`scipy.optimize.differential_evolution`, treating `nd.nasem()` as a
black box, matching 2024 *Journal of Animal Science* precedent. Two
open design questions noted in `overview.md` that will likely come up:
relative (not just absolute) nutrient requirement floors for
`NutrientBound`, and whether a relative target recomputes fresh each
generation or locks against a baseline (flagged as a chat-tool
ask-the-specialist decision, mirroring the `dmi_mode` pattern).
