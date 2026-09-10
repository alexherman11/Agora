# JEFF's authored orientation and runtime guidance

`jeff.md` preserves Alex's original three-paragraph orientation from his September
6, 2026 request to build the VM-native version of Agora. It was recovered from
the original user message in **Review Agora architecture and docs**. The outer
`a)` list marker and HTML space escapes were removed; the wording, punctuation
and spelling are unchanged. Do not rewrite this authored text as part of runtime
maintenance without Alex's direction.

`runtime.md` contains separately maintained development guidance and current
capability constraints. The adapter's `baseInstructions` begins with the complete
unchanged `jeff.md`, followed by a labelled runtime-guidance section loaded from
`runtime.md`. Transport boundary and resident identity are also supplied through
`developerInstructions`. Neither file comes from editable world objects or tool output.
The original ambitions about notifications, agents and future devices do not
claim that the present runtime implements those facilities.

Both files are supplied on a fresh thread and when resuming the same saved
thread after a service restart. A changed prompt does not create another JEFF0 or
discard his history. The compiled-runtime test checks the actual resumed request,
not just the Python parameter dictionary.

The tested runtime applies changed base instructions on the first resumed turn
but did not apply changed supplemental developer instructions on that turn.
Loading both files through the base-instructions path avoids that omission without
rewriting Alex's file or resetting the resident conversation.
