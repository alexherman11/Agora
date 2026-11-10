# Local model words

One SHAPE 11 process, one fixed loopback destination: `127.0.0.1:11434`. It uses
Ollama's generate, tags and ps endpoints. It never downloads a model, follows
redirects, uses proxy environment variables or accepts a host setting.

* `model.ask "what is most urgent?" about=<board>` returns labelled text.
* `model.summarize <thing> [into=short] [words=12]` writes the fact and
  `<field>_source`. Allowed length is 1–100 words.
* `model.classify <thing> options="housing meeting help other" [into=topic]`
  writes exactly one option and its source. Extra punctuation/text is refused.
* `model.status` reports the selected model, installed models and loaded models;
  selection is not misrepresented as loaded.

`model-settings name=model model=qwen2.5:3b` selects an installed model. All world
context and settings are read within the call, through see words as the caller
narrowed to the module. There is no context cache. About a normal thing means
that thing's visible facts. A board can explicitly say
`model_kind=taskboard-task` to include visible rows of that kind; for the current
single task board this means its visible cards. This is not an implicit graph
traversal or support for separate boards sharing one task kind. Context is
bounded to 12,000 JSON characters; questions to 2,000 characters.

Model output is untrusted data. Only module code constructs `set`, the target,
field, quoted value and source. Do words cannot target executable definitions,
identity/authority things or reserved policy fields. Generation may still be
factually wrong (the proof observed invented wording); no semantic reliability
claim follows from safe admission. Classification accepts only exact options.
Kernel records name the module and caller; source facts also say `model module
for <caller>`. Undo restores the output and source together; computation and
attempt counts cannot be undone.

Each dictionary entry has `may=members` and a configured daily `once` policy.
Stewards change those with word-set. Model enforces attempts, including readings,
failures and adapter calls, by canonical word and person (agents share their
person's allowance). Counts persist in `modules/model/usage.json`; no prompts or
answers are stored there. Daily windows use UTC. Do not edit usage.json to
adjust policy. Model.preview charges both preview and summarize; summarize.all
charges per card. Its own kernel entry's once, if configured, is additional.
Preview also asks kernel help whether the canonical summarize word is permitted
in the place, so disabling that word cannot be bypassed through the adapter.
This conservative bridge may refuse target-dependent maker/group policies even
where a direct model.summarize call is permitted; use the direct word there.
The module accepts the supported daily grammar only, failing closed otherwise.

If Ollama is unavailable or times out, ask/status say **the local model is not
running**, summarize writes a labelled literal trim, classify refuses. A busy
model refuses politely rather than running concurrent GPU requests. Off switch:
`off model` stops inference; `off summarize` stops task-board adapters.

**Compatibility choice:** summarize.task/all remain a thin module adapter,
delegating to model.preview, which uses the very same model.summarize planner.
Their one record is admitted by summarize for the caller, and the per-fact label
names model. Quick-add/save remain board-specific there. Before model is
registered, the board uses only deterministic literal shortening, without a
second Ollama client. Batches refuse atomically if a card fails or a deadline is
exceeded. [REGISTER.md](REGISTER.md) has the exact reviewed registration and
[NEEDS.md](NEEDS.md) records the kernel limitations.

Run the scratch HTTP/real-Ollama proof with the pinned interpreter:
`C:/Projects/Agora4/.venv/Scripts/python.exe src/agora/proof/local_model.py`.
It creates no live desktop windows. The proof-only worker instruments requests
without storing prompts and injects an outage; it never stops the user's server.
Offline unit contracts: `-m unittest discover -s src/agora/modules/model`.
See [LOCAL-MODEL.md](../../proof/LOCAL-MODEL.md) for evidence and limits.
