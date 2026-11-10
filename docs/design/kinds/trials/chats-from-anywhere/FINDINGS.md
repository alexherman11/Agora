# Trial: chats from anywhere (dk1031, dk1140)

> Run 28 Oct 2026 by a trial agent for Claude, on a copy of the live desktop log; written here by Claude from its report (the agent could not write files).
> - Scripts: `trial.py`, `probe.py`, `explore.py`, `explore2.py` in this folder.
> - World copy and last output (`run3.txt`): the session scratchpad (`trial-chats/`).
> - No source was edited. Labels: **ran**, **read**, **imagined**.

## What was built (ran)
- 310 said lines and a new chat, on the copy.
- A `twitch` module, granted make and set only on its own kinds, offering five words with shapes.
- 4 channels and 3,000 messages in Twitch's own field names, 10 of them hostile.
- 20 native windows from the real window module.

Native windows aren't world things today (read, `kd_window.py:698,714`), so that half of dk1031 is **imagined**.

## Findings, most severe first

### 1. Giving the kernel's `said` a shape lets anyone forge lines in JEFF's context
**Ran:**
- `make kind=kind name=said needs="text|message chat|channel"` was accepted.
- The House's catch-up `rows said` then returned 3,423 rows, of which 3,004 were not said lines.
- Among them was Sable's note `chat=dk828 to=dk827`: a forged line in the Conversation, which she can't speak in.

**Read:**
- The reserved-kind check stops only `make kind=said` (`words.py:220,594`).
- The House builds wakes and context from `rows said` (`house.py:493,667`).

**Fix (source):**
- Refuse `needs`/`extends` on the kernel's reserved kinds.
- The House reads `rows said exact=yes`.

### 2. Outside text can wake JEFF through `say`
**Ran:**
- The module said `text="@JEFF …"`, the line came out addressed to JEFF, and the House would wake him.
- `say` also drops every Twitch fact, so the speaker becomes "twitch".

**Read:** quoted words escape only by accident (`chat.py:19,45`).

**Fix:**
- Never grant a source module `say`.
- A line from a module acting on its own should address no one.

### 3. "A chat" can't be one kind for both words and `mark`
**Ran:**
- With `needs="chat=yes"`:
  - `rows chat` lists 18, including Agora's own chats;
  - but `chat.star <Stream crew>` is refused ("has no chat yes").
- After widening to `kind|chat=chat|yes`, the words work, but `mark` refuses ("a chat is made as one").

**Read:**
- `fits` accepts a thing's own kind (`kinds.py:169`).
- `check_word` doesn't (`:288`).
- `mark` refuses needs that mix a marker and `kind` (`:423`).

### 4. Plain words silently prefer a shaped word over the right unshaped one
No live word has a shape yet. **Ran:**
- `close <ChatGPT window>` ran `chat.close`, which marks it closed and leaves the window open.
- A new Twitch channel named Help sent `close Help` to `twitch.close` instead of the live Help window.
- `close Claude`, with two Claude windows, silently picked the one marked chat.

**Read:** `kernel.py:589-611` drops the unshaped candidates.

**Fix in data:** `word-set window.close acts_on=window`, after which `close Help` asks which.

### 5. `chat` the marker collides with `chat` the link
**Ran:** `set <msg> chat=yes` was refused, and the refusal suggested `set … channel=yes`, which would break the message's link.

**Read:** `kinds.py:242`.

### 6. Shapes see one thing, not a container and its messages
- `say` and `chat` check the kind exactly (`chat.py:52,141`), so they refuse a channel or a chat window.
- A verb can't follow a link: `say $chat …` came out empty (`kernel.py:1233-1250`).
- `model.summarize` reads a whole kind, cut to 12,000 characters (`model.py:102-127`).
- Its offline fallback finds nothing on a Twitch message, which spells its words `message` (ran).

### 7. Two declarations can share the name `event`
Shapes use the later one (`kinds.py:112`); the board uses the first (`board.py:96-98`).

### 8. A narrowing grant doesn't narrow
**Ran:** a module installed with `make set`, plus `grant only=kind:…`, still set Shop talk (`kernel.py:909`). The `module` word has no `only=`.

### 9. The lens can't say "conversations I'm in"
- `prop:with=dk2` is exact, so it drops the Conversation.
- Said lines name the speaker by id ("[dk2]"); Twitch names them by name.
- "Latest N" can't be said: `limit` takes the oldest.

### 10. Privacy
- Native window things have no `sees`, so JEFF and Sable would see Alex's ChatGPT, Claude and Discord windows.
- A by-app kind works (`kind|exe=chat|ChatGPT.exe|…`) but is case-sensitive.
- A note saying `exe=ChatGPT.exe` fits it.

### 11. Scale (ran)
- 12.4 ms per message and about 970 bytes per record.
- The log grew 34.6 → 37.8 MB; reload went 0.91 → 1.28 s.
- Each message is heard by four modules, and the House does a `look` and `task_changes()` per message (`house.py:561-583`).

### 12. Smaller
- `actions` claims jeff-chat shows Twitch messages. It can't: the desk painter reads exact kinds (`kernel/painter.py:164`).
- The count "145 words take any thing" is noise.
- Refusal text reads "acts on a twitch-message with kind twitch-message", and "a assistant".
- `make about=<text>` is now refused.
- `json.dumps` quoting mangles emoji and newlines.

## What held (ran)
- Grants with `only=kind:` held, and `mark` was refused on other people's things.
- All 10 hostile messages were stored verbatim with no extra facts.
- `reply <twitch msg>` picked `twitch.reply`.
- A `message` kind with spellings listed 3,417 rows across said lines and Twitch, and its filters worked.

## What would change my mind
- **If Twitch messages stay out of the log, as presence does,** findings 2, 5 and 11 mostly go.
- **If the House read said lines exactly,** finding 1 shrinks to lens spoofing.
- **If a kind's own things were never meant to satisfy words,** finding 3 is by design.

## Timings (ran; 4,537 things, 5,567 records)

| What | ms |
|---|---|
| Load the world | 914 |
| Reload after the trial | 1,283 |
| `rows chat` | 54 |
| `rows twitch-message` | 64 |
| `rows message` (3,417 rows) | 122 |
| `rows said` (after said got a shape) | 117 |
| `kinds <msg>` | 3.6 |
| `actions <msg>` / `<window>` / `<chat>` | 17.6 / 17.5 / 27 |
| Plain `close <id>` / `close <name>` | 14.9 / 26 |
| `twitch.reply` | 19.7 |
| `say` | 12.6 |
| Conversations lens compile | 464–505 |
