# Richer chat — body-only staged changes

Draft for JEFF, 20 October. No active lenses changed. Source must land first.

Read both live lenses; save their complete text and revisions before writing. Check both OLD passages occur exactly once before either edit. Preserve all other text. If drifted, stop and refresh these hunks. The existing view verb handles named links; opening a link must not attach chat context. No composer, recipient, Reply or context hunk.

For each lens replace OLD with NEW using ordinary do replace after read. Reverse by replacing NEW with OLD, after checking both fresh passages. Do not use the older lens.desk as an unreviewed activation shortcut.

## jeff-chat

OLD (no trailing newline):

```text
    body : text "$s.said"
      marks
      role words
      media
```

NEW (no trailing newline):

```text
    body : text "$s.said"
      markdown
      role words
      media
      on link do view $value
```

## conversation

OLD (no trailing newline):

```text
  body : text "$said"
    marks
    role body
    media
```

NEW (no trailing newline):

```text
  body : text "$said"
    markdown
    role body
    media
    on link do view $value
```

Acceptance remains gated on fresh guarded disposable-feed proof at 320/420/600px and the full HUD, including selection/copy, keyboard links, media playback/Pop out, draft/caret/explicit context through incoming updates, and original-place replies. No live Conversation sends, Alex-screen input or restart.
