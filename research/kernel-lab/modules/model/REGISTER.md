# Model registration for Claude

Builder handoff; no live installation has been performed. Do not restart or
write the live world while Alex is gaming. No kernel-desktop files were edited.

Use `register.specs()` in this folder for the exact genesis/module specifications
tested by the scratch proof. Both are ordinary SHAPE 11 processes:

```python
{
  'name': 'model',
  'run': ['C:/Projects/Agora4/.venv/Scripts/python.exe',
          'C:/Projects/Agora4/research/kernel-lab/modules/model/model.py'],
  'publishes': 'model.*',
  'grants': 'model.* look rows help set',
}
```

The model is deliberately **not** installed `for=steward`: each request gets its
caller's rights. It makes no autonomous world reads or writes. Its grants contain
no make, role, forget, off, external desktop or unrelated module words.

For an existing world, this exact steward line installs it (the run value is JSON):

```text
module model run='["C:/Projects/Agora4/.venv/Scripts/python.exe", "C:/Projects/Agora4/research/kernel-lab/modules/model/model.py"]' grants="model.* look rows help set"
```

Wait for `help model.status` to answer. Then call `register.configure(door)` using
an authenticated steward Door; it uses only ordinary rows, look, word-set and
make. It adds this setting if absent:

```text
make kind=model-settings name=model model=qwen2.5:3b
```

For **each** offered model word (`ask`, `summarize`, `classify`, `status`,
`preview`), configure looks at its dictionary entry and says:

```text
word-set <entry returned by rows word bound=model.ask> may=members once="at most 60 per day per person"
```

Substitute each word's entry. This second step is necessary: the kernel currently
ignores `once` in offers. Do not substitute an hourly clause: the kernel refuses
unsupported clauses on do words. `configure` is repeatable but restores the
initial daily policy; do not rerun it over a steward's deliberate custom limits.

Keep the existing summarize process and its existing entries. Add `model.preview`
to its grant, keeping `only=kind:taskboard-task`, `for=steward`, and its current
argv. Its exact new grant words are:

```text
summarize.* model.preview rows make set
```

Find the existing module with `rows module name=summarize`, its grant with
`rows grant to=<module>`, then `look <grant>` and
`set <grant> words="summarize.* model.preview rows make set"`.
Restart **only summarize**, when safe, to load its reviewed adapter code; existing
processes do not reload Python files. Let the desktop owner handle lifecycle.
There must be only one model process per world.

Use the task-board installer to refresh its authored lens help. The model name
now belongs to `model-settings`; `taskboard-settings.model` is legacy and ignored.
Existing summarize dictionary help is world-held, not overwritten by an offer;
refresh those two entries' help with `word-set` from summarize.py's new offer.

Acceptance after review: `model.status`; summarize one existing card; ask the
board question with its explicit `model_kind=taskboard-task` board thing. No
live windows need to be opened for registration or these line checks. The feed
example in uses.lines is optional demo content, not an installer.
