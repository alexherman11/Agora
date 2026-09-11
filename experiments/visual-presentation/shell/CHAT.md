# Chat presentation

Assistant messages render GitHub-flavored Markdown using vendored Marked 18.0.12
and DOMPurify 3.4.15. HTML is sanitized against a small presentation allowlist;
remote images, executable elements, styles and unsafe links are excluded.
User text remains literal. Code blocks and tables scroll within the chat panel.

chat.status.activity supplies per-message snapshots keyed by turn and item ID.
Commentary and the streaming final answer remain separate. The durable final
replaces its streamed counterpart. Activity includes a tool label and elapsed
time, never raw commands. Progress survives view reload and missed polls within
the current server session; it is transient and resets on the next request or
server restart. No raw reasoning is displayed. Existing note behavior is retained.
