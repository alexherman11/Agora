# The Seabright message board

*Draft by Claude, 26 Oct 2026, from Alex's ask: "build a fully functional community message board (supporting multiple users, upvotes, uploading of various file types (converted to world objects). Think deeply about what seabright members will want from a message board, think about matching and then exceeding functionality of other message board / feed places. It should also look good, and … mostly tweakable." Builds on [[Communities and the Dictionary]] (the feed section) and the component painter (research/kernel-lab/painter/).*

## Who is reading it

About 200 neighbours organising around a housing development, plus early Agora people. Most of them aren't AI users. Many are older, and many will read on a phone between other things. They come to the board to answer five questions:

1. **What's happening, and what changed since I last looked?** For example, a meeting on Thursday, a council vote, or a public-comment deadline.
2. **What can I do?** Show up, sign up to speak, bring flyers, write a letter.
3. **What do we know?** The planning PDFs, photos of the site, news, someone's notes.
4. **What do people think?** Questions, answers and discussion, without one loud voice drowning out the rest.
5. **Can I trust it?** Real names, visible roles, nothing quietly deleted, agents labelled.

## What other places get wrong, and what we take from them

| Place | Keep | Avoid |
|---|---|---|
| Nextdoor | neighbourhood scope, real names | rumour spreads unchecked, ads, everything at one volume |
| Facebook groups | photos, events in the group, ease | the algorithm hides things, posts get lost, no history of edits |
| Discord | channels, slowmode, roles | fast talk buries decisions, nothing is findable a week later |
| Reddit | upvotes, threaded replies, flair | anonymous pile-ons, karma games, downvote brigades |
| Discourse | categories, solved answers, good search, trust levels | heavy, admin-shaped settings |
| Group email lists | everyone sees it, simple | reply-all storms, attachments lost in inboxes |

## The design

### One board, a few channels

A board belongs to a group (Seabright first). Channels are world things that leaders make and rename:
- Announcements (leaders post; everyone can reply);
- Meetings & events;
- Research & documents;
- Asks & offers;
- Neighbours (general);
- Off-topic.

A channel says who may post and how slow it is. The slow rule is a dictionary limit (`once`), set with words, not code. The feed view merges every channel; a channel view shows one.

### A post is a living object, not a blob of text

Each post has a kind, and the kind decides the actions it carries. Kinds are world definitions, so neighbours can add new ones ("Lost pet", "Ride share") without source.
- **Discussion:** text, attachments and replies.
- **Question:** stays marked "needs an answer" until the asker or a leader marks one reply as the answer.
- **Announcement:** posted by leaders, pinnable, with an optional "until" date after which it unpins itself.
- **Event:** date, time and place.
  - People can RSVP (going / maybe) with `claim`, and sign-up slots carry seat counts.
  - It can be exported as a calendar file.
  - It shows on the map if it has a place.
  - It shows a countdown when it's soon.
- **Poll:** options and a closing time; votes are sealed (counts shown, never who voted for what).
- **Ask / offer:** "need 3 people to flyer Saturday". It has slots people claim, and it closes when filled.
- **Document:** made from an upload (below). Its text is searchable and people can quote it.
- **Decision:** a leader closes a thread with an outcome ("We'll speak at the 4 Nov council meeting"). The outcome shows at the top of the thread and in the catch-up.

### Replies

- Threaded two levels deep (reply, and reply to a reply), so threads stay readable on a phone.
- A reply can quote a selected passage from the post or from a document's page.

### Weight decides placement, never erasure

- **Upvotes are the kernel's sealed `like`:** counts are shown, voters are not. There are no downvotes. "Not useful" lowers a post only in the reader's own view (hide or mute), never for everyone.
- **Orderings are views anyone can copy and change:**
  - *New*;
  - *Top this week*;
  - *Needs answers*;
  - *Happening soon*.

  The default is a world thing Alex holds for now and can hand to the group later.
- **"Why is this here?"** Every post in the feed can say why, in words: "pinned by Maya · 14 upvotes · new reply from Dan".
- **Leaders can hide a post.** Hiding is `forget`, which undo reverses. It leaves a visible "hidden by Maya, reason" line, so nothing vanishes silently.
- **Reports go to the leaders' queue.**

### Catching up

- **A "since you were last here" line:** the board remembers, per person, where you stopped. Above the line it lists:
  - new decisions;
  - new events;
  - answered questions;
  - the busiest threads.

  This is plain data, with no AI needed.
- **An optional summary from the local model,** labelled as such, for people who want it.
- **Later, a weekly digest** by email: email is an effect a steward holds, and it waits for the email keys.

### Attachments become world objects

Every upload becomes a `file` thing plus the richer thing its contents describe. Each one inherits who may see it from its post.

| Upload | Becomes |
|---|---|
| Photo (jpg, png, webp, gif, heic if decodable) | a **photo**: dimensions, a thumbnail, alt text (written by the poster, or offered by the local model and labelled). Location and camera data are stripped by default, because homes stay private unless a member adds one. |
| PDF | a **document**: page count, per-page text (searchable and quotable), a first-page preview |
| .docx, .txt, .md | a **document** with its text |
| .csv | a **table** that a table component can show and sort |
| .ics | an **event** that people can RSVP to |
| Audio and video | a **media** thing with duration that plays inline |
| Anything else | a **file** with name, type and size, download only |

Safety rules for uploads:
- The file's type is sniffed from its bytes, not its name.
- Size is capped (25 MB at first; a steward setting).
- Nothing uploaded is ever served as a page or a script: SVG and HTML are served as downloads only.
- File contents live in a content-addressed store beside the world, never in the log. The log holds only the hash and the facts.

### Trust and fairness

- Real names, with initials avatars.
- Role badges: leader, steward, agent (an agent is always shown as "agent for Maya").
- Edits keep their history ("edited", tap for earlier versions).
- Slow posting is per channel and per person. Replies get a gentler limit than new posts.
- There's no karma and no leaderboard.

### Finding things

- **Search** covers posts, replies and document text, with filters by channel, kind, person and date.
- **Bookmarks:** save posts for later.
- **Follow a thread** to see its new replies in your catch-up.

### Comfort

- Large, calm, readable type.
- Light by default.
- Works one-handed on a phone: a single column, a bottom compose button.
- Every action is keyboard-reachable; screen-reader labels throughout.
- Spanish labels available, per person.

## Tweakable by construction

The board is a lens arranging catalogue components, with app components only where the catalogue lacks something. Everything people will want to change is a handle, not code:
- channels;
- post kinds and their fields;
- orderings;
- the slow rules;
- labels and translations;
- badge styles;
- which kinds show on the map;
- the card layout.

## How we'll know it works

1. **A realistic proof:** a scratch world where 30 neighbours and 2 leaders use the board for a simulated two weeks around a council vote:
   - they post and reply;
   - they upload the planning PDF, site photos (with location data that must come out), a CSV of signatures and an .ics for the meeting;
   - they RSVP, run a poll and claim flyering slots;
   - a leader pins, hides and decides;
   - an all-caps poster hits the slow limit;
   - someone's agent summarises the week.
2. **Tweaks:** a new frozen set of tweak requests, run by fresh agents.
3. **A phone-width check.**
4. **Alex uses it.**
