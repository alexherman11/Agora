// Do comment anchors survive whole-text writes? Sable, round 3, 23 September 2026.
//
// Five comments are anchored on a seed document as Automerge cursors (and, separately, as
// non-expanding marks). The same ten revisions are then applied to four copies by four writers:
//   op  splice operations, one per edit, covering only the changed words (what an op-emitting editor sends)
//   ut  Automerge.updateText(newText): the whole revised text, diffed by Automerge (what an agent hands back)
//   wd  a word-token diff computed here and applied as splices (a candidate middle path)
//   pr  paragraph replacement: unchanged blocks kept, every changed block deleted and reinserted
// After every revision every anchor is resolved and compared with the oracle in doc.mjs.
// Run (c) applies one agent-style rewrite (~30% of words changed) to a fresh seed with ut, wd and pr.
//
// Usage: node anchors.mjs   (writes results.md and results.json next to this file)

import * as A from "@automerge/automerge";
import { writeFileSync } from "node:fs";
import { SEED, ANCHORS, REVISIONS, REWRITE, REWRITE_EXPECT } from "./doc.mjs";

const P = ["text"];
const txt = (d) => A.toJS(d).text;

// ---------- tokens and diffs ----------
const TOK = /\s+|[A-Za-z0-9'’]+|[^\sA-Za-z0-9'’]/g;
const tokens = (s) => s.match(TOK) || [];

function lcsTable(a, b) {
  const n = a.length, m = b.length;
  const t = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      t[i][j] = a[i] === b[j] ? t[i + 1][j + 1] + 1 : Math.max(t[i + 1][j], t[i][j + 1]);
  return t;
}

// Hunks over token arrays: [{ i0, i1, newText }] meaning old tokens i0..i1 become newText.
function tokenHunks(a, b) {
  const t = lcsTable(a, b);
  const hunks = [];
  let i = 0, j = 0, cur = null;
  const flush = () => { if (cur) { hunks.push(cur); cur = null; } };
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) { flush(); i++; j++; continue; }
    if (!cur) cur = { i0: i, i1: i, newText: "" };
    if (j < b.length && (i >= a.length || t[i][j + 1] >= t[i + 1][j])) { cur.newText += b[j]; j++; }
    else { i++; cur.i1 = i; }
  }
  flush();
  return hunks;
}

// Apply token hunks to a doc as splices, last hunk first so offsets stay valid.
function applyHunks(doc, oldToks, hunks) {
  const offs = [0];
  for (const t of oldToks) offs.push(offs[offs.length - 1] + t.length);
  return A.change(doc, (d) => {
    for (const h of [...hunks].reverse()) A.splice(d, P, offs[h.i0], offs[h.i1] - offs[h.i0], h.newText);
  });
}

const wordDiffWrite = (doc, newText) => { const a = tokens(txt(doc)); return applyHunks(doc, a, tokenHunks(a, tokens(newText))); };

const blocks = (s) => s.split(/(\n\n+)/); // paragraphs and their separators
const paragraphReplaceWrite = (doc, newText) => { const a = blocks(txt(doc)); return applyHunks(doc, a, tokenHunks(a, blocks(newText))); };

const updateTextWrite = (doc, newText) => A.change(doc, (d) => A.updateText(d, P, newText));

// ---------- the op-level writer ----------
function find(text, s, from = 0) {
  const k = text.indexOf(s, from);
  if (k < 0) throw new Error(`edit target not found: ${JSON.stringify(s)}`);
  return k;
}
// One splice over the smallest differing run of whole tokens between `find` and `with`.
function wordTrimSplice(d, at, oldS, newS) {
  const a = tokens(oldS), b = tokens(newS);
  let p = 0; while (p < a.length && p < b.length && a[p] === b[p]) p++;
  let s = 0; while (s < a.length - p && s < b.length - p && a[a.length - 1 - s] === b[b.length - 1 - s]) s++;
  const pre = a.slice(0, p).join("").length;
  const delLen = a.slice(p, a.length - s).join("").length;
  A.splice(d, P, at + pre, delLen, b.slice(p, b.length - s).join(""));
}
function opWrite(doc, edits) {
  return A.change(doc, (d) => {
    for (const e of edits) {
      const cur = () => d.text.toString();
      if (e.replace !== undefined) {
        const n = e.all ? cur().split(e.replace).length - 1 : 1;
        let from = 0;
        for (let k = 0; k < n; k++) {
          const at = find(cur(), e.replace, from);
          wordTrimSplice(d, at, e.replace, e.with);
          from = at + e.with.length;
        }
      } else if (e.insertAfter !== undefined) {
        A.splice(d, P, find(cur(), e.insertAfter) + e.insertAfter.length, 0, e.text);
      } else if (e.insertBefore !== undefined) {
        A.splice(d, P, find(cur(), e.insertBefore), 0, e.text);
      }
    }
  });
}

// ---------- anchors ----------
function locate(text, o0) {
  // ctx narrows which occurrence is meant; when the anchored text is longer than ctx, the text is its own context.
  const o = o0.ctx && o0.ctx.includes(o0.text) ? o0 : { ...o0, ctx: o0.text };
  const c = text.indexOf(o.ctx);
  if (c < 0) throw new Error(`oracle context not found: ${JSON.stringify(o.ctx.slice(0, 60))}`);
  if (text.indexOf(o.ctx, c + 1) >= 0) throw new Error(`oracle context not unique: ${JSON.stringify(o.ctx.slice(0, 60))}`);
  const k = o.ctx.indexOf(o.text);
  if (k < 0) throw new Error(`oracle text not in its context: ${o.text}`);
  return [c + k, c + k + o.text.length];
}

// A comment is a pair of cursors: before its first character (resolving forward if deleted) and
// on its last character (resolving backward if deleted); the resolved range is [start, last + 1).
// This is Peritext's non-growing comment: text typed just after it is not absorbed.
function placeAnchors(doc) {
  const text = txt(doc);
  const out = {};
  for (const an of ANCHORS) {
    const [s, e] = locate(text, an);
    out[an.id] = { start: A.getCursor(doc, P, s, "after"), last: A.getCursor(doc, P, e - 1, "before") };
  }
  const marked = A.change(doc, (d) => {
    for (const an of ANCHORS) {
      const [s, e] = locate(text, an);
      A.mark(d, P, { start: s, end: e, expand: "none" }, `comment-${an.id}`, true);
    }
  });
  return { doc: marked, cursors: out };
}

function resolveCursor(doc, c) {
  try {
    const s = A.getCursorPosition(doc, P, c.start);
    const e = A.getCursorPosition(doc, P, c.last) + 1;
    return { s, e };
  } catch (err) { return { lost: String(err.message || err) }; }
}
function resolveMark(doc, id) {
  const ms = A.marks(doc, P).filter((m) => m.name === `comment-${id}`);
  if (!ms.length) return { s: 0, e: 0, segments: 0 };
  return { s: Math.min(...ms.map((m) => m.start)), e: Math.max(...ms.map((m) => m.end)), segments: ms.length };
}

const show = (s, n = 44) => { const t = s.replace(/\n/g, "⏎"); return t.length > n ? t.slice(0, n - 1) + "…" : t; };

function classify(text, r, o) {
  if (r.lost) return { cls: "lost", note: r.lost };
  const got = r.e > r.s ? text.slice(r.s, r.e) : "";
  if (o === null) return got ? { cls: "drifted", got } : { cls: "orphan-ok", got };
  if (r.e <= r.s) return { cls: "collapsed", got };
  const [es, ee] = locate(text, o);
  if (r.s === es && r.e === ee) return { cls: "intact", got };
  const inter = Math.max(0, Math.min(r.e, ee) - Math.max(r.s, es));
  const union = Math.max(r.e, ee) - Math.min(r.s, es);
  const j = inter / union;
  return { cls: j >= 0.5 ? "partial" : j > 0 ? "drifted" : "elsewhere", got, overlap: +j.toFixed(2) };
}

// ---------- runs ----------
const WRITERS = {
  op: { label: "op: splice operations", write: null },
  ut: { label: "ut: Automerge.updateText (whole text)", write: updateTextWrite },
  wd: { label: "wd: word-token diff as splices", write: wordDiffWrite },
  pr: { label: "pr: paragraph replacement", write: paragraphReplaceWrite },
};

function fresh() {
  // Every copy starts from the same change history, so all cursors are the same op ids.
  const base = A.from({ text: SEED });
  return placeAnchors(base);
}

function runSequence() {
  const seeded = fresh();
  const docs = Object.fromEntries(Object.keys(WRITERS).map((k) => [k, A.clone(seeded.doc)]));
  let oracle = Object.fromEntries(ANCHORS.map((a) => [a.id, { text: a.text, ctx: a.ctx }]));
  const rows = [];
  for (const rev of REVISIONS) {
    docs.op = opWrite(docs.op, rev.edits);
    const target = txt(docs.op);
    for (const k of ["ut", "wd", "pr"]) {
      docs[k] = WRITERS[k].write(docs[k], target);
      if (txt(docs[k]) !== target) throw new Error(`${k} produced different text at ${rev.name}`);
    }
    oracle = { ...oracle, ...rev.expect };
    const row = { rev: rev.name, cells: {} };
    for (const k of Object.keys(WRITERS)) {
      row.cells[k] = {};
      for (const an of ANCHORS) {
        row.cells[k][an.id] = {
          cursor: classify(target, resolveCursor(docs[k], seeded.cursors[an.id]), oracle[an.id]),
          mark: classify(target, resolveMark(docs[k], an.id), oracle[an.id]),
        };
      }
    }
    rows.push(row);
  }
  return rows;
}

function runRewrite() {
  const seeded = fresh();
  const a = tokens(SEED).filter((t) => /\w/.test(t)), b = tokens(REWRITE).filter((t) => /\w/.test(t));
  const kept = lcsTable(a, b)[0][0];
  const stats = { oldWords: a.length, newWords: b.length, keptInOrder: kept,
    changedShareOfOld: +(1 - kept / a.length).toFixed(3), newShareOfNew: +(1 - kept / b.length).toFixed(3) };
  const res = {};
  for (const k of ["ut", "wd", "pr"]) {
    const d = WRITERS[k].write(A.clone(seeded.doc), REWRITE);
    if (txt(d) !== REWRITE) throw new Error(`${k} rewrite text mismatch`);
    res[k] = {};
    for (const an of ANCHORS) res[k][an.id] = {
      cursor: classify(REWRITE, resolveCursor(d, seeded.cursors[an.id]), REWRITE_EXPECT[an.id]),
      mark: classify(REWRITE, resolveMark(d, an.id), REWRITE_EXPECT[an.id]),
    };
  }
  return { stats, res };
}

// ---------- report ----------
const cell = (c) => c.cls === "intact" || c.cls === "orphan-ok" || c.cls === "lost" || c.cls === "collapsed"
  ? c.cls : `${c.cls} “${show(c.got)}”`;

function report(seq, rw) {
  const L = [];
  const wc = SEED.split(/\s+/).filter(Boolean).length;
  L.push(`# Anchor survival results`, ``, `Automerge ${A.stats ? "" : ""}@automerge/automerge (version pinned in package.json). Seed: ${wc} words. Generated by anchors.mjs.`, ``);
  L.push(`Classes: **intact** = exactly the oracle span; **partial** = overlaps the oracle span with Jaccard ≥ 0.5; **drifted** = overlaps less; **elsewhere** = no overlap; **collapsed** = empty range while the intended text still exists; **orphan-ok** = empty because the intended text was deleted; **lost** = cursor could not be resolved.`, ``);
  for (const kind of ["cursor", "mark"]) {
    L.push(`## Ten revisions in sequence, anchors as ${kind === "cursor" ? "cursor pairs" : "Automerge marks (expand: none)"}`, ``);
    for (const k of Object.keys(WRITERS)) {
      L.push(`### ${WRITERS[k].label}`, ``);
      L.push(`| revision | ${ANCHORS.map((a) => `${a.id} (${a.kind})`).join(" | ")} |`);
      L.push(`|---|${ANCHORS.map(() => "---").join("|")}|`);
      for (const r of seq) L.push(`| ${r.rev} | ${ANCHORS.map((a) => cell(r.cells[k][a.id][kind])).join(" | ")} |`);
      L.push(``);
    }
  }
  L.push(`## Summary: anchor-revisions intact (of ${seq.length * ANCHORS.length})`, ``, `| writer | cursor intact | cursor partial | cursor collapsed | cursor drifted/elsewhere | mark intact |`, `|---|---|---|---|---|---|`);
  for (const k of Object.keys(WRITERS)) {
    const all = seq.flatMap((r) => ANCHORS.map((a) => r.cells[k][a.id]));
    const n = (kind, cls) => all.filter((c) => cls.includes(c[kind].cls)).length;
    L.push(`| ${WRITERS[k].label} | ${n("cursor", ["intact", "orphan-ok"])} | ${n("cursor", ["partial"])} | ${n("cursor", ["collapsed", "lost"])} | ${n("cursor", ["drifted", "elsewhere"])} | ${n("mark", ["intact", "orphan-ok"])} |`);
  }
  L.push(``, `## Run (c): one agent-style rewrite of the seed`, ``);
  L.push(`Words: ${rw.stats.oldWords} before, ${rw.stats.newWords} after; ${rw.stats.keptInOrder} kept in order; ${(rw.stats.changedShareOfOld * 100).toFixed(1)}% of the original words not kept; ${(rw.stats.newShareOfNew * 100).toFixed(1)}% of the rewrite's words new.`, ``);
  for (const kind of ["cursor", "mark"]) {
    L.push(`| writer (${kind}) | ${ANCHORS.map((a) => `${a.id} (${a.kind})`).join(" | ")} |`, `|---|${ANCHORS.map(() => "---").join("|")}|`);
    for (const k of Object.keys(rw.res)) L.push(`| ${WRITERS[k].label} | ${ANCHORS.map((a) => cell(rw.res[k][a.id][kind])).join(" | ")} |`);
    L.push(``);
  }
  return L.join("\n");
}

const seq = runSequence();
const rw = runRewrite();
const md = report(seq, rw);
writeFileSync(new URL("./results.md", import.meta.url), md + "\n");
writeFileSync(new URL("./results.json", import.meta.url), JSON.stringify({ automerge: "3.5.0", seq, rewrite: rw }, null, 1));
console.log(md);
