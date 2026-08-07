"""
Chat server -- runs the Claude tool-use loop and serves a simple local
web chat page.

Requires an ANTHROPIC_API_KEY environment variable (get one at
console.anthropic.com). This app runs OUTSIDE claude.ai, so it needs its
own API credentials.

Run with:
    export ANTHROPIC_API_KEY=sk-ant-...
    python -m chat.server
Then open http://localhost:5000 in a browser.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

from chat.logging_utils import blocks_to_dicts, log_turn
from chat.tools import TOOL_DEFINITIONS, ChatSession

SYSTEM_PROMPT = """You are a dairy nutrition assistant built on the NASEM \
(2021) Nutrient Requirements of Dairy Cattle model.

SCOPE: You can ONLY answer questions about LACTATING dairy cows using the \
tools available to you: dry matter intake, energy (NEL) requirement and \
supply, protein (MP) requirement and supply, all 13 NASEM minerals, \
vitamins A/D/E, and water requirement. You do NOT cover dry cows, \
heifers, or other species. If asked about any of these, say clearly and \
plainly that this is not yet supported, rather than guessing or estimating.

IMPORTANT: mineral and vitamin "balance" numbers come directly from the \
underlying reference model's own supply calculation, NOT from \
independently-cited supply equations the way requirements are. If a user \
asks specifically how mineral/vitamin supply is calculated, say this \
plainly rather than implying the same level of citation-backed detail as \
the requirement side.

RULES:
- Never state a number that didn't come from a tool call. If you don't \
have a tool for something, say so.
- When you give a numeric answer, mention the underlying equation number \
if the tool result includes one (e.g. "via Equation 2-2").
- If the user asks "why" a number is what it is, use explain_component \
to get the real citation/assumptions rather than making up a reason. For \
minerals use component='mineral_<Symbol>' (e.g. 'mineral_Ca'), for \
vitamins use 'vitamin_<Symbol>' (e.g. 'vitamin_E'), for water use 'water'.
- Use search_feed_ingredient before calculate_lactating_cow_requirements \
if you are not certain an ingredient name matches the feed library exactly.
- Keep answers concise and in plain language -- this is a chat interface, \
not a report.
- If no ration is given, the calculation tool falls back to a standard \
reference diet -- say so plainly and offer to use the user's real diet \
instead, rather than presenting the placeholder result as if it were \
based on their actual ration.
"""

app = Flask(__name__, static_folder="static")

# NOTE: single global session -- fine for a local single-user chat window,
# not a multi-user deployment. See ChatSession docstring.
session = ChatSession()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY environment variable is not set."}), 500

    client = anthropic.Anthropic(api_key=api_key)

    body = request.get_json()
    history = body.get("history", [])  # list of {role, content}
    user_message = body["message"]

    messages = history + [{"role": "user", "content": user_message}]

    # Tool-use loop: keep calling Claude until it stops requesting tools.
    for _ in range(10):  # hard cap to avoid a runaway loop
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            reply_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            messages.append({"role": "assistant", "content": blocks_to_dicts(response.content)})
            log_turn(user_message, response.content, [])
            return jsonify({"reply": reply_text, "history": messages})

        messages.append({"role": "assistant", "content": blocks_to_dicts(response.content)})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = session.dispatch(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
        log_turn(user_message, response.content, tool_results)
        messages.append({"role": "user", "content": tool_results})

    return jsonify({"error": "Too many tool-use steps without a final answer."}), 500


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY is not set. The chat endpoint will fail.")
    app.run(debug=True, port=5000)
