// Seed document, anchors, ten revisions and one agent-style rewrite, with the oracle:
// for every anchor after every revision, the text a careful reader would say the comment is still about.
// An oracle entry is { text, ctx } (the anchored text, found inside the first occurrence of the unique
// context string ctx), or null when the revision deliberately deleted what the comment was about.

export const SEED = `# Oak Park autumn work day

The garden club will hold its autumn work day on Saturday 18 October, starting at nine at the Elm Street gate. We expect around twenty volunteers, and the city has promised a skip for green waste. Parking on Elm Street is free before ten.

## Why this year matters

Last winter the tap by the gate froze twice, and the drip under the standpipe turned the path into a sheet of ice for most of January. Two volunteers slipped there, and one of them still talks about it. The city now says it will only repair the standpipe if we clear the drain first, so the drain is our first job.

We also lost most of the garlic in bed three to standing water. The east path is the lowest ground in the park, and after heavy rain it floods near the bottom for days. Raising the path is beyond us, but we can dig a shallow trench along the beds and fill it with gravel.

## What to bring

Bring gloves, a trowel and something warm to drink, because the east path floods and the morning will be cold. The club has spades, two wheelbarrows and a first aid kit. If you have a pair of loppers, bring them too; the hedge along the picnic lawn needs cutting back before the tables disappear into it.

## Tasks

- Clear the drain beside the standpipe
- Replace the washer on the tap by the gate
- Dig the gravel trench along beds one to four
- Plant garlic in bed three and mulch all beds
- Cut back the hedge by the picnic lawn

## After the work

We will share soup at the picnic tables around one. The running club has offered to help carry gravel on their way back from their Saturday run, which should save us an hour. Anyone who wants to stay on can help Maria sort the seed library in the shed.

Please reply to this note if you can come, and say which task you would like. New volunteers are very welcome; nobody needs experience, only a willingness to get muddy.
`;

// The five comments, placed on the seed. kind is what the brief asked for.
export const ANCHORS = [
  { id: "c1", kind: "a word", text: "Saturday", ctx: "on Saturday 18 October" },
  { id: "c2", kind: "a phrase", text: "the drip under the standpipe", ctx: "the drip under the standpipe" },
  { id: "c3", kind: "a sentence", text: "Bring gloves, a trowel and something warm to drink, because the east path floods and the morning will be cold.", ctx: "Bring gloves, a trowel and something warm to drink, because the east path floods and the morning will be cold." },
  { id: "c4", kind: "a list item", text: "Replace the washer on the tap by the gate", ctx: "- Replace the washer on the tap by the gate" },
  { id: "c5", kind: "across a paragraph break", text: "The city now says it will only repair the standpipe if we clear the drain first, so the drain is our first job.\n\nWe also lost most of the garlic in bed three to standing water.", ctx: "The city now says it will only repair the standpipe if we clear the drain first, so the drain is our first job.\n\nWe also lost most of the garlic in bed three to standing water." },
];

// Edits are applied in order. The op-level writer applies each edit as ONE splice covering the smallest
// differing run of whole word tokens between the found text and its replacement (a person selecting the
// changed words and typing), and a delete + insert for moves. Each edit is one of
//   { replace: find, with: text, all?: true }     find must occur (the first occurrence, or all)
//   { insertAfter: find, text }  { insertBefore: find, text }
// expect: oracle changes after this revision (anchors not named keep their previous oracle).
export const REVISIONS = [
  {
    name: "R1 insert a sentence",
    edits: [{ insertAfter: "starting at nine at the Elm Street gate.", text: " If it rains, we will move to the following weekend." }],
    expect: {},
  },
  {
    name: "R2 delete a clause (inside c3)",
    edits: [{ replace: ", because the east path floods and the morning will be cold", with: "" }],
    expect: { c3: { text: "Bring gloves, a trowel and something warm to drink.", ctx: "Bring gloves, a trowel and something warm to drink." } },
  },
  {
    name: "R3 reorder two list items (delete + insert)",
    edits: [
      { replace: "- Replace the washer on the tap by the gate\n", with: "" },
      { insertBefore: "- Clear the drain beside the standpipe", text: "- Replace the washer on the tap by the gate\n" },
    ],
    expect: { c4: { text: "Replace the washer on the tap by the gate", ctx: "- Replace the washer on the tap by the gate\n- Clear the drain" } },
  },
  {
    name: "R4 retitle a heading",
    edits: [{ replace: "## Tasks", with: "## Jobs for the day" }],
    expect: {},
  },
  {
    name: "R5 rewrite one paragraph (c2, start of c5)",
    edits: [
      { replace: "Last winter the tap by the gate froze twice", with: "The tap by the gate froze twice last winter" },
      { replace: "the drip under the standpipe", with: "the drip at the base of the standpipe" },
      { replace: "turned the path into a sheet of ice for most of January", with: "left a sheet of ice on the path through most of January" },
      { replace: "Two volunteers slipped there, and one of them still talks about it.", with: "Two volunteers slipped on it." },
      { replace: "The city now says it will only repair the standpipe if we clear the drain first", with: "The city will only repair the standpipe once we clear the drain" },
    ],
    expect: {
      c2: { text: "the drip at the base of the standpipe", ctx: "the drip at the base of the standpipe" },
      c5: { text: "The city will only repair the standpipe once we clear the drain, so the drain is our first job.\n\nWe also lost most of the garlic in bed three to standing water.", ctx: "The city will only repair the standpipe once we clear the drain, so the drain is our first job.\n\nWe also lost" },
    },
  },
  {
    name: "R6 replace the commented word (Saturday 18 -> Sunday 19)",
    edits: [{ replace: "on Saturday 18 October", with: "on Sunday 19 October" }],
    expect: { c1: { text: "Sunday", ctx: "on Sunday 19 October" } },
  },
  {
    name: "R7 insert a new section",
    edits: [{ insertAfter: "Parking on Elm Street is free before ten.", text: "\n\n## Who is coming\n\nThe running club and three families from Birch Street have said yes so far." }],
    expect: {},
  },
  {
    name: "R8 edit the list item in place, add an item",
    edits: [
      { replace: "Replace the washer on the tap", with: "Replace the worn washer on the tap" },
      { insertAfter: "washer on the tap by the gate", text: " and lag the pipe" },
      { insertAfter: "- Cut back the hedge by the picnic lawn", text: "\n- Sort the seed library with Maria" },
    ],
    expect: { c4: { text: "Replace the worn washer on the tap by the gate and lag the pipe", ctx: "- Replace the worn washer on the tap by the gate and lag the pipe" } },
  },
  {
    name: "R9 merge two paragraphs (inside c5)",
    edits: [{ replace: "our first job.\n\nWe also lost", with: "our first job. We also lost" }],
    expect: { c5: { text: "The city will only repair the standpipe once we clear the drain, so the drain is our first job. We also lost most of the garlic in bed three to standing water.", ctx: "The city will only repair the standpipe once we clear the drain, so the drain is our first job. We also lost" } },
  },
  {
    name: "R10 tidy: volunteers -> helpers everywhere; shorten c3",
    edits: [
      { replace: "volunteers", with: "helpers", all: true },
      { replace: "something warm to drink", with: "a hot drink" },
    ],
    expect: { c3: { text: "Bring gloves, a trowel and a hot drink.", ctx: "Bring gloves, a trowel and a hot drink." } },
  },
];

// Run (c): one agent-style rewrite of the seed that keeps the meaning and changes about 30% of the words.
export const REWRITE = `# Oak Park autumn work day

The garden club's autumn work day is on Saturday 18 October, and we start at nine by the Elm Street gate. We are expecting about twenty volunteers, and the city has agreed to send a skip for green waste. You can park free on Elm Street until ten.

## Why this year matters

The tap by the gate froze twice last winter, and the leaking standpipe covered the path in ice for most of January. Two volunteers fell there, and one of them still mentions it. According to the city, the standpipe will only be repaired once the drain is clear, which makes the drain our first job.

Standing water also killed most of the garlic in bed three. The east path sits on the lowest ground in the park, and after heavy rain it stays flooded near the bottom for days. We cannot raise the path ourselves, but we can dig a shallow trench beside the beds and fill it with gravel.

## What to bring

Please bring gloves, a trowel and a hot drink, since the east path floods and it will be a cold morning. Spades, two wheelbarrows and a first aid kit come from the club. If you own loppers, please bring them; the hedge along the picnic lawn has to be cut back before it swallows the tables.

## Tasks

- Clear the drain next to the standpipe
- Fit a new washer on the tap by the gate
- Dig the gravel trench along beds one to four
- Plant garlic in bed three and mulch every bed
- Cut back the hedge by the picnic lawn

## After the work

Around one we will eat soup together at the picnic tables. The running club has offered to carry gravel on the way back from their Saturday run, which should save us an hour. If you want to stay longer, Maria could use help sorting the seed library in the shed.

If you can make it, reply here and tell us which task you would prefer. Newcomers are very welcome; no experience is needed, just a willingness to get muddy.
`;

export const REWRITE_EXPECT = {
  c1: { text: "Saturday", ctx: "is on Saturday 18 October" },
  c2: { text: "the leaking standpipe", ctx: "the leaking standpipe" },
  c3: { text: "Please bring gloves, a trowel and a hot drink, since the east path floods and it will be a cold morning.", ctx: "Please bring gloves, a trowel and a hot drink, since the east path floods and it will be a cold morning." },
  c4: { text: "Fit a new washer on the tap by the gate", ctx: "- Fit a new washer on the tap by the gate" },
  c5: { text: "According to the city, the standpipe will only be repaired once the drain is clear, which makes the drain our first job.\n\nStanding water also killed most of the garlic in bed three." },
};
