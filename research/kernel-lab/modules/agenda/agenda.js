// agenda: a module in JavaScript that brings a council agenda into the world as things, and walks it on the night.
//
//   agenda.load [file]   do:  the meeting, its items in order, and a public-comment list on the hearing item
//   agenda.next <meeting>  do:  move the meeting's "now speaking" to its next item
//   agenda.now [meeting]   see: what the meeting is on now, and what is next
//
// It speaks newline-separated JSON on stdin and stdout (SHAPE section 11). It keeps no storage: it reads the posted
// agenda (a file beside it, standing in for the city's agenda page) and the world through see words, and it changes
// the world only by handing back lines, which the kernel admits as one act for the leader who asked.
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");

let answered = 0;
let grants = [];
let lastLoaded = null;
const waiting = new Map();

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

function see(use, line) {
  return new Promise((resolve) => {
    waiting.set(use, resolve);
    send({ t: "see", use, line });
  });
}

function q(text) {
  // a value for k="..." in a line: its own quotes and backslashes escaped, as the line language asks
  return '"' + String(text).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
}

// a UTC time (2026-10-29T00:45Z) as the town says it: "5:45 pm" in its own zone
function said(utc, zone) {
  const d = new Date(String(utc).replace(/Z$/, ":00Z"));
  return d.toLocaleTimeString("en-US", { timeZone: zone, hour: "numeric", minute: "2-digit" }).toLowerCase();
}

function readAgenda(name) {
  const file = path.resolve(__dirname, path.basename(name || "agenda-oct28.json"));
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

// the meeting named, or else the newest one that has not ended
async function currentMeeting(use, named) {
  const found = await see(use, "find kind=meeting");
  if (found.refused) return { refused: "could not read the meetings: " + found.refused };
  if (named) {
    const m = (found.rows || []).find((r) => r.id === named);
    return m ? { meeting: m } : { refused: `${named} is not a meeting` };
  }
  const open = (found.rows || []).filter((m) => m.ended !== "yes");
  if (!open.length) return { refused: "no meeting is open; agenda.load brings one in" };
  return { meeting: open[open.length - 1] };
}

async function items(use, meeting) {
  const found = await see(use, `find kind=item meeting=${meeting.id}`);
  if (found.refused) return { refused: "could not read the items: " + found.refused };
  return { items: found.rows || [] };          // in their `order`, as find gives them
}

async function call(msg) {
  const { use, word, args } = msg;
  if (word === "agenda.load") {
    let a;
    try {
      a = readAgenda((args.words || "").trim());
    } catch (e) {
      return { t: "answer", use, refused: `could not read the posted agenda (${e.code || e.message})` };
    }
    const m = a.meeting;
    const zone = a.zone || "America/Los_Angeles";
    const inGroup = args.kv && args.kv.in ? ` in=${args.kv.in}` : "";     // where the leader asked for it
    const lines = [`make kind=meeting title=${q(m.title)} at=${m.at} at_said=${q(said(m.at, zone))} ` +
                   `where=${q(m.where)}${inGroup} as=m`];
    a.items.forEach((it, i) => {
      let line = `make kind=item meeting=$m order=${it.order} title=${q(it.title)}`;
      if (it.number) line += ` number=${q(it.number)}`;
      if (it.comment) {
        line += ` seats=${it.comment.seats} minutes=${it.comment.minutes} closes=${it.comment.closes}` +
                ` closes_said=${q(said(it.comment.closes, zone))}`;
      }
      lines.push(line + inGroup + ` as=i${i + 1}`);
    });
    lastLoaded = m.title;
    return { t: "answer", use, lines };
  }
  if (word === "agenda.next" || word === "agenda.now") {
    const cm = await currentMeeting(use, args.target);
    if (cm.refused) return { t: "answer", use, refused: cm.refused };
    const its = await items(use, cm.meeting);
    if (its.refused) return { t: "answer", use, refused: its.refused };
    const list = its.items;
    const at = list.findIndex((it) => it.id === cm.meeting.now);
    if (word === "agenda.now") {
      const now = list[at];
      const next = list[at + 1];
      return {
        t: "answer", use,
        text: (now ? `now: ${now.title}` : "the meeting has not started") + (next ? `\nnext: ${next.title}` : "\nnothing after this"),
        rows: [{ meeting: cm.meeting.id, now: now ? now.id : "", next: next ? next.id : "" }],
      };
    }
    const next = list[at + 1];
    // what it read, by rev: the kernel admits the move only if the meeting has not moved since (two reporters
    // pressing Next at once move it one item, not two)
    const saw = { [cm.meeting.id]: cm.meeting.rev };
    if (!next) return { t: "answer", use, lines: [`set ${cm.meeting.id} now= ended=yes`], saw };
    return { t: "answer", use, lines: [`set ${cm.meeting.id} now=${next.id}`], saw };
  }
  return { t: "answer", use, refused: `agenda has no word ${word}` };
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
        { word: "agenda.load", kind: "do", takes: "[<words>] [in=<group>]", may: "leaders",
          help: "agenda.load: bring the posted council agenda in: the meeting, its items in order, and the " +
                "public-comment list on the hearing item." },
        { word: "agenda.next", kind: "do", takes: "<id>", may: "leaders",
          help: "agenda.next <meeting>: move the meeting on to its next item, so everyone following sees what is " +
                "being heard now. Its group's leaders may." },
        { word: "agenda.now", kind: "see", takes: "[<id>]", may: "anyone",
          help: "agenda.now [meeting]: what the meeting is on now, and what comes next." },
      ],
    });
  } else if (msg.t === "rows") {
    const resolve = waiting.get(msg.use);
    if (resolve) {
      waiting.delete(msg.use);
      resolve(msg);
    }
  } else if (msg.t === "call") {
    let answer;
    try {
      answer = await call(msg);
    } catch (e) {
      answer = { t: "answer", use: msg.use, refused: "agenda failed: " + e.message };
    }
    answered += 1;
    send(answer);
  } else if (msg.t === "status?") {
    send({ t: "status", use: msg.use,
           doing: `idle; ${answered} call${answered === 1 ? "" : "s"} answered; last loaded: ${lastLoaded || "nothing"}; grants: ${grants.join(", ") || "none"}` });
  } else if (msg.t === "off") {
    process.exit(0);
  }
});
rl.on("close", () => process.exit(0));
