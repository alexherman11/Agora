// tally: a module in JavaScript that publishes two words to the kernel (SHAPE section 11, phase 2).
//
//   tally.top [n]      see: the most-liked posts you may see
//   tally.pin-top      do:  pin the most-liked post that is not pinned yet
//
// It speaks newline-separated JSON on stdin and stdout and nothing else. It keeps no storage: everything it knows it
// reads through see words while it answers, and it changes the world only by handing back lines. Its only state is
// momentary (how many calls it has answered), which `status tally` reports.
"use strict";
const readline = require("readline");

let answered = 0;
let grants = [];
const waiting = new Map();   // use -> resolve, for see requests in flight

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

function see(use, line) {
  return new Promise((resolve) => {
    waiting.set(use, resolve);           // one read at a time per call: the kernel answers it with the same use
    send({ t: "see", use, line });
  });
}

function ranked(rows) {
  return rows
    .filter((r) => r.kind === "post")
    .sort((a, b) => b.likes - a.likes || b.rev - a.rev);
}

async function call(msg) {
  const { use, word, args } = msg;
  const feed = await see(use, "look");
  if (feed.refused) return { t: "answer", use, refused: "could not read the feed: " + feed.refused };
  const posts = ranked(feed.rows || []);
  if (word === "tally.top") {
    const n = Math.max(1, parseInt((args.words || "").split(" ")[0], 10) || 3);
    const top = posts.slice(0, n);
    const text = top.length
      ? ["most liked:"].concat(top.map((p, i) => `  ${i + 1}. ${p.id} · ${p.by}: ${p.text} · ${p.likes} like${p.likes === 1 ? "" : "s"}`)).join("\n")
      : "no posts to tally yet";
    return { t: "answer", use, text, rows: top.map((p) => ({ id: p.id, likes: p.likes })) };
  }
  if (word === "tally.pin-top") {
    const best = posts.find((p) => !p.pinned && p.likes > 0);
    if (!best) return { t: "answer", use, text: "nothing to pin: every liked post is pinned already" };
    // what it read, by rev, so the kernel admits the pin only if that post has not changed since
    return { t: "answer", use, lines: [`pin ${best.id}`], saw: { [best.id]: best.rev } };
  }
  return { t: "answer", use, refused: `tally has no word ${word}` };
}

const rl = readline.createInterface({ input: process.stdin });
rl.on("line", async (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (e) {
    return;
  }
  if (msg.t === "hello") {
    grants = msg.grants || [];
    send({
      t: "offer",
      words: [
        { word: "tally.top", kind: "see", takes: "[<n>]", may: "anyone",
          help: "tally.top [n]: the n most-liked posts you may see (3 if you say no number)." },
        { word: "tally.pin-top", kind: "do", takes: "", may: "anyone",
          help: "tally.pin-top: pin the most-liked post that is not pinned yet. Only someone who may pin can use it." },
      ],
    });
  } else if (msg.t === "rows") {
    const resolve = waiting.get(msg.use);
    if (resolve) {
      waiting.delete(msg.use);
      resolve(msg);
    }
  } else if (msg.t === "call") {
    const answer = await call(msg);
    answered += 1;
    send(answer);
  } else if (msg.t === "status?") {
    send({ t: "status", use: msg.use, doing: `idle; ${answered} call${answered === 1 ? "" : "s"} answered; grants: ${grants.join(", ") || "none"}` });
  } else if (msg.t === "off") {
    process.exit(0);
  }
});
rl.on("close", () => process.exit(0));
