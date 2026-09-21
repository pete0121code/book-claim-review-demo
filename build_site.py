#!/usr/bin/env python3
"""Build the book claim checker from claims.json.

  python3 build_site.py     # -> site/index.html + site/claims.json

The page is a reviewer tool: every sentence of the book, filterable, each with a
verdict and a note. Verdicts save in the browser and export as JSON/CSV. No
network calls, no third-party scripts.
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, 'site')

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Book claim review — Sample Manuscript</title>
<style>
/* Claude Design style spec v1, 2026-09-20.
   ⛔ THERE ARE NO VERDICT COLOURS AND THERE MUST NEVER BE. The previous palette carried
   --ok(green) --bad(red) --warn(amber) --p1(red) --p2(orange), and .v.sel painted each of the
   eight verdict buttons a different colour -- green for Verified, red for Disputed. A page that
   colours the answer is telling the reviewer what to think before they have read the sentence,
   and the reviewer's judgement is the entire product. Emphasis is BORDER COLOUR and WEIGHT
   (line -> line-2 -> ink), never hue and never thickness.
   --hit is the only tinted surface in the design and appears only for a typed search query. */
:root{
  --bg:#F4F2EE; --surface:#FFFFFF; --surface-2:#ECE9E3;
  --ink:#1C1C1A; --ink-2:#55534E; --ink-3:#8A867E;
  --line:#DDD9D1; --line-2:#B8B3A9; --link:#3B5B7A; --hit:#F3E9B8;
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,Menlo,Consolas,monospace;
  --r-card:8px; --r-ctl:6px; --r-chip:4px; --r-key:3px;
  /* kept as aliases so any rule not yet ported degrades to neutral rather than breaking */
  --card:var(--surface); --muted:var(--ink-2); --accent:var(--ink); --accent-ink:#fff;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:var(--surface);color:var(--ink);padding:18px 20px;border-bottom:1px solid var(--line)}
header h1{margin:0 0 4px;font:600 19px var(--sans);letter-spacing:-.01em}
header p{margin:0;color:var(--ink-2);font-size:13px}
/* "WORKING DRAFT" is dashed because dashed means "still open" everywhere in this design. */
.draftchip{display:inline-block;border:1px dashed var(--line-2);border-radius:var(--r-chip);
  padding:2px 8px;font:11px var(--sans);text-transform:uppercase;letter-spacing:.06em;
  color:var(--ink-2);margin-left:10px;vertical-align:middle}
/* The amber banner read as a warning about the CONTENT. It is a status about the DOCUMENT. */
.banner{background:var(--surface-2);border-bottom:1px solid var(--line);color:var(--ink-2);
  padding:10px 20px;font-size:13px}
.wrap{max-width:1180px;margin:0 auto;padding:16px 20px 80px}
.controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 0;
  border-bottom:1px solid var(--line);margin-bottom:14px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}
select,input[type=text],input[type=search]{padding:7px 9px;border:1px solid var(--line);
  border-radius:7px;background:#fff;font:inherit;color:inherit}
input[type=search]{flex:1;min-width:200px}
.chip{border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 11px;
  font-size:12.5px;cursor:pointer;user-select:none}
.chip.on{background:var(--ink);border-color:var(--ink);color:#fff}
.stat{font-size:12.5px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:13px 15px;margin-bottom:10px}
.card .meta{font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:8px;
  align-items:center;margin-bottom:7px}
.pri{font-weight:700;letter-spacing:.3px}
.jump{color:var(--accent);text-decoration:none;font-weight:600}
.jump:hover{text-decoration:underline}
.toplinks{font-size:13px}
.toplinks a{color:var(--link);text-decoration:none;margin-right:14px}
.toplinks a:hover{text-decoration:underline}
/* Priority by WEIGHT, not colour -- red P1 / orange P2 read as "danger", which is a verdict. */
.p1{background:var(--ink);color:#fff;border-radius:999px;padding:1px 7px;font-weight:600}
.p2{border:1px solid var(--ink);border-radius:999px;padding:0 6px;font-weight:600}
.p3{color:var(--ink-2);font-weight:600} .p4{color:var(--ink-3)}
/* The sentence under review is the only serif on the page: it is the thing being read, and
   everything else is apparatus around it. */
.sent{font:19px/1.6 var(--serif);color:var(--ink);margin:0 0 9px;text-wrap:pretty}
.kinds{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:9px}
/* Claim-type chips were tinted clinical blue, which reads as a status. They are a taxonomy. */
.kind{font-size:11px;background:transparent;border:1px solid var(--line);border-radius:var(--r-chip);
  padding:2px 7px;color:var(--ink-3)}
.why{font-size:12px;color:var(--muted);margin:0 0 9px}
/* ===== AI SUGGESTIONS =========================================================
   Never "engine review" and never "verdict" for machine output: the heading reads
   "Suggests:", every block carries an AI chip, and the word VERDICT is reserved for the one
   block the human fills in. the project owner, on the first mock: "its not very clear what the AIs are
   suggesting". It was not clear because the block said "verdict" and was collapsed.
   OPEN BY DEFAULT -- this is the research, and it is the one thing a reviewer cannot
   reconstruct for themselves. */
.eng{border-top:1px solid var(--line);padding:12px 0;margin:0 0 4px}
/* ⛔ THE SYNTHESIS BLOCK. Read the comment on synthesise() before changing any of this.
   The label is TEXT, in the markup, always rendered. The tint and the accent bar are
   reinforcement only: strip every colour from this rule set and the block still says
   "AI synthesis · N models · not a clinical decision" and still reads as machine output.
   That is the test. If a restyle makes the tint load-bearing, the restyle is wrong. */
.synth{border:1px solid var(--line);border-left:3px solid var(--ink-2);
  background:var(--surface-2);padding:12px 14px;margin:0 0 14px;border-radius:2px}
.synthlab{font:600 10.5px/1 var(--sans);letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-2);margin-bottom:8px}
.synthhead{font:600 14px/1.45 var(--sans);color:var(--ink);margin:0 0 5px}
.synthbody{font:400 13.5px/1.62 var(--sans);color:var(--ink);margin:0 0 8px}
.synthsrc{font:400 12.5px/1.6 var(--sans);color:var(--ink-2);margin:0 0 8px}
.synthfoot{font:italic 12px/1.55 var(--sans);color:var(--ink-3);margin:0;
  padding-top:8px;border-top:1px dotted var(--line)}
.synthrow{font:400 13.5px/1.62 var(--sans);color:var(--ink);margin:0 0 9px}
.synthk{display:block;font:600 10.5px/1 var(--sans);letter-spacing:.08em;
  text-transform:uppercase;color:var(--ink-2);margin-bottom:3px}
.synthnote{color:var(--ink-3)}
.synthcite{font:400 12.5px/1.6 var(--sans);color:var(--ink);border-left:2px solid var(--line-2);
  padding:2px 0 2px 10px;margin:0 0 8px}
.whycite{display:block;font:400 12px/1.55 var(--sans);color:var(--ink-2);margin-top:3px}
.engdet{margin:2px 0 0;border-top:1px dotted var(--line);padding-top:8px}
.engdet>summary{font:500 12.5px var(--sans);color:var(--ink-2);cursor:pointer;
  list-style:none;padding:4px 0;min-height:32px}
.engdet>summary::-webkit-details-marker{display:none}
.engdet>summary::before{content:"\25B8 ";color:var(--ink-3)}
.engdet[open]>summary::before{content:"\25BE "}
.engdetnote{color:var(--ink-3);font-weight:400;margin-left:6px}
@media print{ .synth{background:none;border-left-width:4px} }
.eng h4{margin:0 0 10px;font:600 16px var(--sans);color:var(--ink)}
.eng h4 .sum{font:400 12px var(--sans);color:var(--ink-3);margin-left:8px}
.ai{border:1px solid var(--line);border-radius:var(--r-ctl);padding:14px 16px;margin-bottom:8px}
.ai .hd{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;margin-bottom:8px}
.aichip{font:11px var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);
  border:1px solid var(--line);border-radius:var(--r-key);padding:1px 6px}
.ai .vd{font:600 16px var(--sans);color:var(--ink)}
.ai .conf{font:12px var(--sans);color:var(--ink-3)}
.ai .why{font:13.5px/1.55 var(--sans);color:var(--ink-2);margin:0 0 10px}
.ai .src{font:12.5px var(--sans);color:var(--ink-3)}
/* Research list -- one row per source, under every AI suggestion, prior finding and known error */
.rlab{font:11px var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);
  margin:10px 0 6px}
.rsrc{border-left:2px solid var(--line);padding:2px 12px;margin-bottom:8px;font:13px/1.5 var(--sans)}
.rsrc a.t{color:var(--link);font-weight:600;text-decoration:none}
.rsrc a.t:hover{text-decoration:underline}
.rsrc .jr{color:var(--ink-2)}
.rsrc .ids{font:11.5px var(--mono)}
.rsrc .ids a{color:var(--link);text-decoration:none;margin-right:10px}
.rsrc .shows{display:block;color:var(--ink-3);margin-top:2px}
/* No source offered: dashed, so a suggestion with no research is visibly weaker BY STRUCTURE.
   A substantial minority of suggestions land here. */
.rsrc.none{border-left-style:dashed;border-left-color:var(--line-2);color:var(--ink-3)}
.eng .triagebad,.eng .flagbad{display:block;margin-top:8px;font:12.5px/1.5 var(--sans);
  color:var(--ink);border:1px dashed var(--line-2);border-radius:var(--r-chip);padding:8px 10px}
/* Disagreement is the most interesting card on the page, so it is marked -- by an outline and a
   dashed chip, never by colour, and never with an answer pre-selected. */
.eng.split .ai{border-color:var(--line-2);border-style:dashed}
.prior{border-top:1px solid var(--line);padding:12px 0;margin:0 0 4px}
.prior h4{margin:0 0 6px;font:600 16px var(--sans);color:var(--ink);text-transform:none;letter-spacing:0}
.prior .lede{margin:0 0 9px;font-size:13.5px;line-height:1.55}
.prior .q{margin:0 0 8px;font-size:13px;line-height:1.55;background:var(--card);border:1px solid var(--line);
  border-radius:6px;padding:8px 10px}
.prior .q b{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.3px;color:var(--muted);margin-bottom:3px}
.prior .q i{color:var(--muted);font-style:normal;font-weight:600}
.prior .caveat{margin:0;font:italic 12.5px/1.5 var(--sans);color:var(--ink-3)}
.corr{border-top:1px solid var(--line);padding:12px 0;margin:0 0 4px}
.corr h4{margin:0 0 5px;font:600 16px var(--sans);color:var(--ink);text-transform:none;letter-spacing:0}
.corr p{margin:0 0 7px;font-size:13.5px}
.corr .rep{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:9px 10px;
  font-size:13.5px;line-height:1.55}
.corr .prov{font-size:12px;color:var(--muted);margin:-2px 0 8px}
.corr .prov a{color:var(--link);font-weight:600}
.corr .rep b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.3px;
  color:var(--muted);margin-bottom:4px}
/* A known factual error is marked by border WEIGHT, not by red. */
.card.known{border-color:var(--ink)}
/* The card a number key will answer. It must be VISIBLE, because the previous version inferred
   it from scroll position and could answer a sentence the reviewer could not see. */
.card.active{outline:2px solid var(--link);outline-offset:2px}
/* Two rows by frequency, not by severity: row 1 is what gets pressed most, row 2 is the
   qualifications. Row 1 is heavier ONLY because it is used more often -- it says nothing about
   which answer is right. */
.verdicts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:10px}
.v{display:flex;align-items:center;gap:8px;border:1px solid var(--line-2);
  background:var(--surface);border-radius:var(--r-ctl);padding:0 12px;min-height:44px;
  font:14px/1.3 var(--sans);color:var(--ink);cursor:pointer;text-align:left}
.v.r2{min-height:40px;border-color:var(--line);font-size:13.5px;color:var(--ink-2)}
.v .key{flex:none;min-width:18px;padding:1px 4px;border:1px solid var(--line);
  border-radius:var(--r-key);font:600 11px var(--mono);color:var(--ink-3);text-align:center}
.v:hover{background:var(--surface-2);border-color:var(--ink)}
.v:focus-visible{outline:2px solid var(--link);outline-offset:2px}
/* ⛔ ONE selected state for all eight, and it must be IDENTICAL.
   The first version set only colour, so .r2's smaller height and type survived selection --
   a chosen "Verified" stayed 44px/14px while a chosen "Disputed" stayed 40px/13.5px. Codex
   measured it. Row height is meant to signal FREQUENCY, which is a fact about how often a
   button is pressed; once an answer is CHOSEN, any remaining difference in prominence is the
   page editorialising about the answer. So selection normalises size and weight too. */
.v.sel,.v.r2.sel{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600;
  min-height:44px;font-size:14px}
.v.sel .key{background:#fff;color:var(--ink);border-color:var(--ink)}
.notes{display:none;gap:6px;flex-direction:column}
.notes.show{display:flex}
.notes textarea,.notes input{width:100%;padding:7px 9px;border:1px solid var(--line);
  border-radius:7px;font:inherit}
.notes textarea{min-height:56px;resize:vertical}
/* The ONLY tinted surface in the design, and it marks a query the reviewer typed themselves --
   so it says "you searched for this", never "this is the problem". */
mark{background:var(--hit);color:var(--ink);padding:0 2px;border-radius:2px}
.pager{display:flex;gap:8px;align-items:center;justify-content:center;margin:18px 0}
button.pg{border:1px solid var(--line);background:#fff;border-radius:7px;padding:7px 13px;
  font:inherit;cursor:pointer}
button.pg[disabled]{opacity:.45;cursor:default}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--surface);color:var(--ink);
  border-top:1px solid var(--line);
  padding:9px 20px;font-size:13px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.bar button{border:1px solid var(--line-2);background:var(--surface);color:var(--ink);
  border-radius:var(--r-ctl);padding:6px 11px;font:inherit;cursor:pointer}
.bar button:hover{background:var(--surface-2);border-color:var(--ink)}
.bar .sp{flex:1}
@media (max-width:640px){.wrap{padding:12px 16px 96px}.sent{font-size:15px}}
@media (prefers-color-scheme:dark){
 :root:not([data-theme=light]){
   --bg:#141311; --surface:#1C1B19; --surface-2:#242220;
   --ink:#E9E5DD; --ink-2:#A9A49B; --ink-3:#78746C;
   --line:#2F2D29; --line-2:#4A4741; --link:#8FB0CF; --hit:#5A4A12;
 }
 :root:not([data-theme=light]) select,:root:not([data-theme=light]) input,
 :root:not([data-theme=light]) textarea,:root:not([data-theme=light]) .chip,
 :root:not([data-theme=light]) .v,:root:not([data-theme=light]) button.pg{
   background:var(--surface);color:var(--ink)}
 :root:not([data-theme=light]) .kind{background:var(--surface-2);color:var(--ink-2)}
 :root:not([data-theme=light]) mark{background:var(--hit);color:var(--ink)}
 :root:not([data-theme=light]) .v.sel{background:var(--ink);color:var(--bg)}
 :root:not([data-theme=light]) .p1{background:var(--ink);color:var(--bg)}
}
/* Failure text is ink, not red: a damaged file is not a verdict either, and red here was the
   last coloured state left on the page. */
.loadmsg{padding:28px 4px;color:var(--ink-2);font-size:15px;line-height:1.6}
.loadmsg small{color:var(--ink-3)}
.loadmsg.err{color:var(--ink);border:1px dashed var(--line-2);border-radius:var(--r-ctl);padding:18px}</style>
</head>
<body>
<header>
  <h1>Book claim review — <em>Sample Manuscript</em><span class="draftchip">Working draft · nothing here is approved</span></h1>
  <p>A. Author · every sentence, flagged by claim type · __COUNT__ sentences from __PARAS__ paragraphs</p>
  <p class="toplinks" style="margin-top:7px">
    <a href="text/index.html">📖 Read the manuscript (anchored by sentence)</a>
    <a href="corrections/index.html">📄 Factual Corrections Sheet (A. Author')</a>
    <a href="sources.html">🔗 Every source cited</a>
    <a href="questions.html">❓ Questions for the author</a>
    <a href="decide/pancreatic.html">Pancreatic evidence decisions</a>
    <a href="evidence/pancreatic.html">Pancreatic evidence register</a>
  </p>
</header>
<div class="banner">
  Internal draft review. Not published, not indexed, not medical advice. Source file
  <code>__SRC__</code> (md5 <code>__MD5__</code>). Verdicts are stored in this browser only —
  export before you close the tab.
</div>
<div class="wrap">
  <div class="controls">
    <div class="row">
      <select id="chapter"><option value="">All chapters</option></select>
      <select id="status">
        <option value="">Any status</option>
        <option value="none">Not reviewed</option>
        <option value="engine">Engine flagged it (not ok)</option>
        <option value="split">Engines disagree</option>
        <option value="ok">Verified</option>
        <option value="source">Needs source</option>
        <option value="disputed">Disputed</option>
        <option value="misleading">True but misleading</option>
        <option value="preclinical">Animals / lab only</option>
        <option value="population">Wrong patients</option>
        <option value="rewrite">Rewrite</option>
        <option value="notclaim">Not a claim</option>
      </select>
      <input type="search" id="q" placeholder="Search the text (e.g. curcumin, 500 mg, FDA)">
    </div>
    <div class="row" id="prio"></div>
    <div class="row" id="kinds"></div>
    <div class="row"><span class="stat" id="stat"></span></div>
  </div>
  <div id="list"></div>
  <!-- Every sentence, every AI suggestion and every citation, embedded. type="application/json"
       means the browser stores it and never executes it. This is what makes the page work from
       a file:// URL with no server and no network. -->
  <script id="claims-data" type="application/json">__CLAIMS_JSON__</script>
  <div class="pager">
    <button class="pg" id="prev">← Previous</button>
    <span class="stat" id="page"></span>
    <button class="pg" id="next">Next →</button>
  </div>
</div>
<div class="bar">
  <span>Reviewer: <input type="text" id="who" placeholder="your name" style="width:130px"></span>
  <span id="progress"></span>
  <span class="sp"></span>
  <button id="exportJson">Export JSON</button>
  <button id="exportCsv">Export CSV</button>
  <button id="importBtn">Import</button>
  <input type="file" id="importFile" accept="application/json" style="display:none">
</div>
<script>
const PER = 50;
const KINDS = ['team-prior','known-error','unit-error','dose','product','protocol','insteadof','anecdote','regulatory','statistic','outcome','safety','study','advice','mechanism','adjacent','firstperson','narrative'];
const KIND_LABEL = {'team-prior':'the review team already reviewed this topic', 'known-error':'known error', 'unit-error':'arithmetic error', dose:'dose', product:'named drug', protocol:'drug cocktail',
  insteadof:'instead of standard care', anecdote:'patient outcome', regulatory:'regulatory',
  statistic:'number', outcome:'result', safety:'safety', study:'research', advice:'advice',
  mechanism:'mechanism', adjacent:'next to a P1 claim', firstperson:'own experience',
  narrative:'narrative'};
const PLAIN_V = {SUPPORTED:'held up', PARTLY:'held up only in part', UNSUPPORTED:'were not supported',
  CONTRADICTED:'were contradicted', 'TEAM-RECORD':'needed the review team\u2019s own records', POLICY:'were policy choices'};
const VERDICT_LABEL = {ok:'Verified', source:'Needs source', disputed:'Disputed',
  misleading:'True but misleading', preclinical:'Animals / lab only',
  population:'Wrong patients', rewrite:'Rewrite', notclaim:'Not a claim'};
let CLAIMS = [], HREF = {}, view = [], page = 0;
const KEY = 'team-book-review-v1';
let saved = {};
try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { saved = {}; }
function persist(){ try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch(e){} }

const state = {chapter:'', status:'', q:'', prio:new Set([1,2]), kinds:new Set()};

/* String(s) first: a numeric year or PMID coming out of the snapshot data has no .replace, and
   an exception here aborts the render of the whole card, not just that one field. */
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
// Every identifier becomes a real link: a reviewer should never have to retype a
// PMID to check a citation. PubMed for PMIDs, doi.org for DOIs, clinicaltrials.gov
// for NCT ids, and bare URLs as themselves.
function linkify(s){
  let out = esc(s);
  out = out.replace(/\b(https?:\/\/[^\s<>"')\]]+)/g,
    '<a href="$1" target="_blank" rel="noopener">$1</a>');
  out = out.replace(/\bPMID[:\s]*(\d{6,9})\b/gi,
    '<a href="https://pubmed.ncbi.nlm.nih.gov/$1/" target="_blank" rel="noopener">PMID $1</a>');
  out = out.replace(/(?<!["=\/])\b(10\.\d{4,9}\/[^\s<>,;)\]]+)/g,
    '<a href="https://doi.org/$1" target="_blank" rel="noopener">$1</a>');
  // Only linkify an NCT id that is NOT already inside generated markup. The URL rule above runs
  // first, so a clinicaltrials.gov URL has already become <a href="...NCT12345678">...</a>; this
  // rule then matched the id INSIDE that href and nested a second anchor in it, producing a
  // broken link and mangled citation text wherever that pattern occurred.
  out = out.replace(/\b(NCT\d{8})\b(?![^<]*<\/a>)/g,
    '<a href="https://clinicaltrials.gov/study/$1" target="_blank" rel="noopener">$1</a>');
  return out;
}
function hl(s, q){
  if(!q) return esc(s);
  try { return esc(s).replace(new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + ')','ig'), '<mark>$1</mark>'); }
  catch(e){ return esc(s); }
}
function shortChapter(c){ return c.replace(/^(CHAPTER|Chapter)\s*(\d+)\s*/, 'Ch $2 · ').slice(0,60); }

/* Say what is actually there. Most reviewed sentences carry exactly ONE suggestion; only a
   minority carry two or more. The first mock's summary read "2 engines · same verdict", which
   describes a small subset and implies a consensus the majority do not have. A single opinion
   presented as agreement is the one error that would actively mislead a clinician, so the
   wording is derived from the data on each card, never assumed. */
/* ⛔ DERIVE DISAGREEMENT, DO NOT TRUST THE PRECOMPUTED FLAG.
   When this was measured, the precomputed `engines_split` flag disagreed with the actual
   verdicts on a meaningful share of multi-suggestion cards -- those cards would have told a
   clinician "same suggestion" while one reviewer said "true but misleading" and another said
   "disputed". A page that manufactures consensus is worse than one that shows none, and the
   verdicts are right there in the object -- there is no reason to take a stale boolean's
   word for it. */
function enginesDisagree(c){
  // Guarded: a null or non-object engine value would throw on e.verdict and abort the whole
  // card render. The current corpus has none, but "it does not throw today" is not a property
  // of the code. A missing verdict is dropped rather than counted, so two assessments that BOTH
  // failed to record one cannot masquerade as a disagreement.
  const vs = Object.values(c.engines || {})
    .filter(e => e && typeof e === 'object' && e.verdict)
    .map(e => e.verdict);
  return new Set(vs).size > 1;
}
/* ⛔ THIS BLOCK IS WRITTEN FOR A CLINICIAN, NOT FOR US.

   The first version failed review in one sentence: "this is AI slop gobbledygook
   for a doctor." It said "The models split 1-1", named codex and grok, printed
   bare PMIDs, and spent its last line on epistemics. Every one of those is a
   fact about OUR pipeline. A reviewing physician does not know what codex is,
   has no reason to learn, and did not come here to audit our tooling.

   WHAT A DOCTOR GETS, in this order, and nothing else:
     ISSUE       one line: what is wrong with the sentence
     WHAT WE FOUND  plain English, no engine names, no tallies
     SUGGESTED   the concrete change, or "no change needed"
     PAPERS      counted and linked, never a bare identifier
   The engine-by-engine detail still exists -- it is collapsed below, for Pete.
   Granularity was never the problem; granularity in the DOCTOR'S path was.

   ⛔ NO MODEL NAMES ABOVE THE FOLD. If you are about to write "codex", "grok",
   "2 models" or "the models split", you are writing for the wrong reader.
   "The automated reviews disagreed" carries the same information and needs no
   glossary. Disagreement is a FACT ABOUT THE SENTENCE -- it means borderline --
   so say that, rather than reporting a scoreboard and leaving them to infer it. */

/* ⛔ COUNT USABLE ENGINE BLOCKS, NOT KEYS. {a:null, b:{verdict:'ok'}} has two keys and one
   opinion; counting keys reported "2 suggestions - same suggestion", which asserts an agreement
   that never happened. Codex caught this in r4 and it has been reintroduced twice since, so it
   lives in ONE helper that every counter calls. */
function usableEngines(c){
  const out = {};
  Object.entries((c && c.engines) || {}).forEach(([k, v]) => {
    if (v && typeof v === 'object' && v.verdict) out[k] = v;
  });
  return out;
}

/* Plain-English issue + suggested change per verdict. The doctor-facing copy
   lives here so it is changed in ONE place, not inside a template string. */
const PLAIN = {
  ok:          {issue:'Nothing found — the sentence stays inside what its source supports.',
                fix:'No change needed.'},
  source:      {issue:'States something checkable but does not say where it came from.',
                fix:'Add a citation for the figure, or take the figure out.'},
  population:  {issue:'Applies a finding more broadly than the patients it was studied in.',
                fix:'Say which patients it applies to.'},
  preclinical: {issue:'Describes laboratory or animal work in language that reads as proven in people.',
                fix:'Say the evidence is early-stage.'},
  misleading:  {issue:'Every part is accurate, but together they imply more than the evidence shows.',
                fix:'Rewrite it so the caveat is not buried at the end.'},
  disputed:    {issue:'Presents a contested point as settled.',
                fix:'Note that sources disagree, or pick a side and say so.'},
  rewrite:     {issue:'Several problems at once — adding a citation will not fix it.',
                fix:'Rewrite the sentence.'},
  notclaim:    {issue:'Not a factual claim — nothing here to check.',
                fix:'No change needed.'}
};

function synthesise(c){
  const eng = usableEngines(c);      // same guard as engSummary -- never Object.keys(c.engines)
  const names = Object.keys(eng);
  if(!names.length) return '';

  // Derived from the verdicts present, never a stored flag. A stale synthesis
  // would be worse than none.
  const tally = {};
  names.forEach(n => { tally[eng[n].verdict] = (tally[eng[n].verdict] || 0) + 1; });
  /* ⛔ ON A DISAGREEMENT, LEAD WITH THE CONCERN -- NEVER THE CLEAN READING.
     The first version ranked by COUNT and took the winner. On a 1-1 split that
     picks arbitrarily, and it picked 'ok': the card told a reviewing physician
     "Issue: nothing found. Suggested: no change needed" on a sentence another
     reviewer had flagged for a missing source. That is not a cosmetic bug. It
     is the tool actively suppressing the only finding on the card, in the exact
     situation the tool exists for.
     So ties break by SEVERITY, and a concern always outranks a clean verdict.
     A doctor can dismiss a concern in two seconds; they cannot act on one they
     were never shown. */
  /* NOTE ON THE TWO BOTTOM VALUES: 'ok' and 'notclaim' are both NON-CONCERNS.
     notclaim ranks above ok only so that "nothing here to check" beats "nothing
     found" when those two are the whole disagreement -- it is the more specific
     statement, not a more serious one. Anything at source(2) or above IS a
     concern and must lead. A test that treats notclaim as a concern will report
     a false suppression; ask whether the verdict names a PROBLEM, not whether
     its number is above zero. */
  const SEVERITY = {rewrite:7, misleading:6, disputed:5, population:4,
                    preclinical:3, source:2, notclaim:1, ok:0};
  const ranked = Object.entries(tally).sort((a,b) =>
    (b[1] - a[1]) || ((SEVERITY[b[0]]||0) - (SEVERITY[a[0]]||0)));
  if(!ranked.length) return '';
  const split = ranked.length > 1;
  // On a split the concern leads, whatever the tally says.
  const top = split
    ? ranked.map(r => r[0]).sort((a,b) => (SEVERITY[b]||0) - (SEVERITY[a]||0))[0]
    : ranked[0][0];

  const plain = PLAIN[top] || {issue:'Flagged for review.', fix:'Read it yourself.'};

  /* Disagreement is reported as what it MEANS, not as a score. A doctor needs
     "this one is borderline"; the 1-1 tally is our business, and it is in the
     collapsed detail below for anyone who wants it. */
  let found;
  if(split){
    const others = ranked.map(r => r[0]).filter(v => v !== top);
    const altTxt = others.map(v => esc((PLAIN[v]||{}).issue || v).replace(/\.$/,'')).join('; also: ');
    found = 'The reviews <b>did not agree</b>. The concern above was raised by one of them. ' +
            'Another read the same sentence as: ' + altTxt + '. ' +
            '<b>Disagreement usually means the sentence is borderline</b>, so this one is worth ' +
            'your eye more than one they agree on — the concern is shown first deliberately, ' +
            'because it is easier to dismiss a flag than to notice one you were never shown.';
  } else if(names.length > 1){
    found = 'The automated reviews <b>independently agreed</b>. Agreement is a reason to look, ' +
            'not a reason to skip — they can be wrong in the same way.';
  } else {
    found = 'One automated review looked at this sentence. Nothing has cross-checked it.';
  }

  // Papers are COUNTED and LINKED. A bare "PMID 00000023" means nothing to a reader.
  const refs = [], seen = {};
  names.forEach(n => {
    (eng[n].resolved || []).forEach(r => {
      const k = r.pmid || r.title;
      if(k && !seen[k]){ seen[k] = 1; refs.push(r); }
    });
  });
  /* ⛔ NAME THE PAPERS. An earlier version rendered these as "paper 1 · paper 2",
     which is not a simplification -- it is a REGRESSION. The reader loses the one
     thing that lets them judge the citation without opening it. Simplify the
     LANGUAGE, never the EVIDENCE. */
  const papers = refs.length
    ? '<p class="synthsrc"><b>What this is based on</b></p>' + refs.map(r =>
        '<div class="synthcite"><a href="https://pubmed.ncbi.nlm.nih.gov/' + esc(r.pmid || '') +
        '/" target="_blank" rel="noopener">' + esc(r.title || ('PMID ' + (r.pmid||''))) + '</a>' +
        (r.journal || r.year ? ' <span class="synthnote">' + esc([r.journal, r.year].filter(Boolean).join(' ')) + '</span>' : '') +
        (r.design ? '<br><span class="synthnote">' + esc(r.design) + '</span>' : '') +
        (r.shows  ? '<br><b>Found:</b> ' + esc(r.shows) : '') +
        (r.why    ? '<br><b>Why it is here:</b> ' + esc(r.why) : '') +
        '</div>').join('') +
      '<p class="synthnote">These were found automatically. A paper being listed does not ' +
      'prove it supports the sentence — open it if the suggestion matters to you.</p>'
    : '<p class="synthsrc"><b>Nothing was found to support this one.</b> <span class="synthnote">The ' +
      'suggestion rests on the wording of the sentence alone, which is the weakest case it can make.</span></p>';

  return '<div class="synth">' +
    '<div class="synthlab">AI review · a suggestion, not a decision</div>' +
    '<p class="synthrow"><span class="synthk">Issue</span>' + esc(plain.issue) + '</p>' +
    '<p class="synthrow"><span class="synthk">What we found</span>' + found + '</p>' +
    '<p class="synthrow"><span class="synthk">Suggested</span><b>' + esc(plain.fix) + '</b></p>' +
    papers +
    '<p class="synthfoot">You decide. Nothing here changes the manuscript on its own.</p>' +
  '</div>';
}

function engSummary(c){
  const n = Object.keys(usableEngines(c)).length;
  /* Plain English. The old version printed "2 suggestions", which invites the
     question "two of what" and answers it nowhere a doctor can see. */
  if(n === 0) return 'nothing usable';
  if(n === 1) return 'one review, not cross-checked';
  return enginesDisagree(c) ? 'the reviews disagree — worth your eye'
                            : 'the reviews agree';
}

/* One research row per source, under every AI suggestion.
   ⚠️ "Resolves" is NOT "supports". A resolved identifier proves the paper EXISTS; whether it
   backs the sentence is a separate human judgement. A title-level pass over a resolved set will
   turn up topic mismatches, and papers reporting the OPPOSITE direction to the sentence citing
   them. So the TITLE is printed next to the claim, where a human can see the mismatch, and
   never a tick.
   A suggestion with no source gets a DASHED rule and a PubMed search link: weaker by structure,
   not by colour. A substantial minority of suggestions land there. */
function researchRows(e){
  const rows = (e.resolved || []).map(r => {
    const pm = esc(r.pmid || '');
    const t  = r.title ? esc(r.title) : ('PMID ' + pm);
    const jr = [r.journal, r.year].filter(Boolean).map(esc).join(' ');
    return '<div class="rsrc">' +
      '<a class="t" href="https://pubmed.ncbi.nlm.nih.gov/' + pm + '/" target="_blank" rel="noopener">' + t + '</a>' +
      (jr ? ' <span class="jr">' + jr + '</span>' : '') +
      '<div class="ids"><a href="https://pubmed.ncbi.nlm.nih.gov/' + pm + '/" target="_blank" rel="noopener">PMID ' + pm + '</a></div>' +
      (r.design ? '<span class="shows">' + esc(r.design) + '</span>' : '') +
      (r.shows  ? '<span class="shows"><b>What it found:</b> ' + esc(r.shows) + '</span>' : '') +
      /* ⛔ THE RATIONALE IS THE POINT. A title tells a reviewer WHICH paper; only this
         tells them WHY it was attached to THIS sentence. Without it there is no way to
         tell a well-matched citation from a keyword collision -- which is how a paper on
         the wrong subject ends up under a drug claim and nobody notices. */
      (r.why    ? '<span class="whycite"><b>Why it is here:</b> ' + esc(r.why) + '</span>' : '') +
      '</div>';
  });
  /* ⛔ THE PROSE SOURCE IS ALWAYS SHOWN, EVEN WHEN SOMETHING RESOLVED.
     The first version of this returned early the moment one citation resolved, which threw away
     e.source entirely. Codex reproduced the consequence on a claim whose assessment cited two
     different papers: the resolver matched one identifier, returned early, and the rest of what
     the engine actually relied on vanished from the page. A restoration that hides evidence is worse than the gap it filled,
     because the gap was visible and this was not. Resolution status is per-source, never a
     switch on the whole list. */
  if(e.source && e.source.trim()){
    rows.push('<div class="rsrc none">' + linkify(e.source) +
      '<span class="shows">' + (rows.length
        ? 'Also cited here, and not matched to a resolved identifier — check it before relying on it.'
        : 'Not resolved against PubMed — check it before relying on it.') +
      '</span></div>');
  }
  if(rows.length) return rows.join('');
  return '<div class="rsrc none">No source offered · unresolved</div>';
}

function filtered(){
  const q = state.q.toLowerCase();
  return CLAIMS.filter(c => {
    if(state.chapter && c.chapter !== state.chapter) return false;
    if(state.prio.size && !state.prio.has(c.priority)) return false;
    if(state.kinds.size){
      const ks = (c.kinds.length ? c.kinds : ['narrative']).concat(c.prior_review ? ['team-prior'] : []);
      if(![...state.kinds].some(k => ks.includes(k))) return false;
    }
    if(state.status === 'engine'){
      const e = c.engines || {};
      if(!Object.values(e).some(x => x.verdict !== 'ok' && x.verdict !== 'notclaim')) return false;
    } else if(state.status === 'split'){
      // Derived, not the stale flag: the "Engines disagree" queue was driven by the stored
      // boolean, which had drifted from the verdicts. Most sentences where the reviewers
      // actually disagree were unreachable by the one filter built to find exactly those.
      if(!enginesDisagree(c)) return false;
    } else if(state.status){
      const v = (saved[c.id]||{}).verdict || 'none';
      if(v !== state.status) return false;
    }
    if(q && !c.text.toLowerCase().includes(q)) return false;
    return true;
  });
}

function render(){
  view = filtered();
  if(page * PER >= view.length) page = 0;
  const slice = view.slice(page*PER, page*PER + PER);
  const list = document.getElementById('list');
  list.innerHTML = slice.map(c => {
    const rec = saved[c.id] || {};
    const ks = (c.kinds.length ? c.kinds : ['narrative']);
    return `<div class="card ${c.correction?'known':''}" data-id="${c.id}">
      <div class="meta">
        <span class="pri p${c.priority}">P${c.priority}</span>
        <span>${esc(shortChapter(c.chapter))}</span>
        ${c.section ? `<span>› ${esc(c.section.slice(0,50))}</span>` : ''}
        <span>¶${c.para}</span><span>${c.id}</span>
        ${HREF[c.id] ? `<a class="jump" href="${HREF[c.id]}" target="_blank" rel="noopener">read in the book ↗</a>` : ''}
      </div>
      <p class="sent">${hl(c.text, state.q)}</p>
      <div class="kinds">${ks.map(k => `<span class="kind">${KIND_LABEL[k]||k}</span>`).join('')}</div>
      ${c.why.length ? `<p class="why">Flagged because it ${esc(c.why.join('; it '))}.</p>` : ''}
      ${c.unit_error ? `<div class="corr"><h4>Arithmetic error — checkable with no source</h4>
        <p>${esc(c.unit_error.note)}</p></div>` : ''}
      ${c.prior_review?`<div class="prior">
        <h4>the review team has already looked at this topic — ${esc(c.prior_review.topic)}</h4>
        <p class="lede">When the review team reviewed its own website it worked through
          <b>${c.prior_review.topic_claims} claim${c.prior_review.topic_claims==1?'':'s'}</b> on this topic
          (${Object.entries(c.prior_review.topic_spread).map(([k,v])=>`${v} ${PLAIN_V[k]||k.toLowerCase()}`).join(', ')}).
          The one closest to this sentence, <code>${esc(c.prior_review.register_id)}</code>, <b>${esc(c.prior_review.headline)}</b> — ${esc(c.prior_review.plain)}</p>
        ${c.prior_review.team_wording?`<p class="q"><b>What the website says</b>${esc(c.prior_review.team_wording)}</p>`:''}
        ${c.prior_review.why?`<p class="q"><b>Why the review team reached that</b>${linkify(c.prior_review.why)}</p>`:''}
        ${c.prior_review.rewrite?`<p class="q"><b>The wording the review team proposed instead</b>${esc(c.prior_review.rewrite)}</p>`:''}
        ${(c.prior_review.sources||[]).length?`<div class="rlab">Research behind the review team's finding</div>
        ${(c.prior_review.sources||[]).map(s=>`<div class="rsrc">
          <a class="t" href="${s.doi?`https://doi.org/${esc(s.doi)}`:`https://pubmed.ncbi.nlm.nih.gov/${esc(s.pmid)}/`}" target="_blank" rel="noopener">${esc(s.cite)}</a>
          <div class="ids">${s.pmid?`<a href="https://pubmed.ncbi.nlm.nih.gov/${esc(s.pmid)}/" target="_blank" rel="noopener">PMID ${esc(s.pmid)}</a>`:''}${s.doi?`<a href="https://doi.org/${esc(s.doi)}" target="_blank" rel="noopener">doi:${esc(s.doi)}</a>`:''}</div>
          ${(s.design||s.shows)?`<span class="shows">${esc(s.design||'')}${s.design&&s.shows?' · ':''}${s.shows?`Shows: ${esc(s.shows)}`:''}</span>`:''}
        </div>`).join('')}`:''}
        <p class="caveat">⚠️ Background, not a verdict on this sentence. This is what the review team concluded about the same
          topic <b>for its website</b> — different wording, different audience. A claim can be fine on a web page
          and wrong in a book, and the reverse. <b>None of this is a sign-off on the sentence above</b> —
          it is here so you can see what has already been looked at, not to close the question.</p>
      </div>`:''}
      ${c.engines ? `<div class="eng ${enginesDisagree(c)?'split':''}">
        <h4>AI review<span class="sum">${engSummary(c)}</span></h4>
        ${synthesise(c)}
        <details class="engdet"><summary>Show the detailed review<span class="engdetnote">— which system said what, confidence, and the raw references</span></summary>
        ${Object.entries(c.engines).map(([name,e]) => `<div class="ai">
          <div class="hd">
            <span class="aichip">AI · ${esc(name)}</span>
            <span class="vd">Suggests: ${esc(VERDICT_LABEL[e.verdict]||e.verdict)}</span>
            ${e.confidence?`<span class="conf">${esc(e.confidence)} confidence</span>`:''}
          </div>
          <p class="why">${linkify(e.why)}</p>
          ${e.triage?`<div class="triagebad">⚑ ${esc(e.triage.label)} (source triage, ${esc(e.triage.by)}): ${esc(e.triage.note)} — PMID ${esc(e.triage.pmid)}</div>`:''}
          ${e.source_flag?`<div class="flagbad">${esc(e.source_flag)}</div>`:''}
          <div class="rlab">What this AI cited
            <span style="text-transform:none;letter-spacing:0">— a resolved identifier means the
            paper <b>exists</b>, not that it supports this sentence</span></div>
          ${researchRows(e)}
        </div>`).join('')}
        </details>
        ${enginesDisagree(c)?`<p class="caveat">These are AI suggestions, shown as inputs. None is pre-selected below.</p>`:''}
      </div>` : ''}
      ${c.correction ? `<div class="corr">
        <h4>Known error #${c.correction.n} · ${esc(c.correction.severity)} · ${esc(c.correction.label)}</h4>
        <p class="prov">From A. Author' own <a href="corrections/index.html#c${c.correction.n}">Factual Corrections Sheet</a>, 20 September 2026 — prepared for him, located verbatim in this manuscript.</p>
        <p>${linkify(c.correction.problem)}</p>
        <div class="rep"><b>Suggested replacement</b>${esc(c.correction.replacement)}</div>
        ${c.correction.alternative ? `<p class="why" style="margin-top:7px">${esc(c.correction.alternative)}</p>` : ''}
      </div>` : ''}
      <div class="rlab" style="border-top:1px solid var(--line);padding-top:12px">Your verdict
        <span style="text-transform:none;letter-spacing:0;float:right">Draft · pending clinician sign-off · press a number key</span></div>
      <div class="verdicts">
        ${[['ok','Verified',1],['source','Needs source',2],['notclaim','Not a claim',3],['rewrite','Rewrite',4],
           ['disputed','Disputed',5],['misleading','True but misleading',6],
           ['preclinical','Animals / lab only',7],['population','Wrong patients',8]].map(([v,label,k]) =>
          `<button class="v ${k>4?'r2':''} ${rec.verdict===v?'sel':''}" data-v="${v}"
             ><span class="key">${k}</span>${label}</button>`).join('')}
      </div>
      <div class="notes ${rec.verdict && rec.verdict!=='notclaim' ? 'show':''}">
        <input type="text" class="src" placeholder="Source (PMID, DOI, URL) or existing claim id" value="${esc(rec.source||'')}">
        <textarea class="note" placeholder="What is wrong, or what it should say instead">${esc(rec.note||'')}</textarea>
      </div>
    </div>`;
  }).join('') || '<p class="stat">Nothing matches these filters.</p>';

  document.getElementById('stat').textContent =
    `${view.length} of ${CLAIMS.length} sentences match`;
  document.getElementById('page').textContent =
    view.length ? `${page*PER+1}–${Math.min((page+1)*PER, view.length)}` : '0';
  document.getElementById('prev').disabled = page === 0;
  document.getElementById('next').disabled = (page+1)*PER >= view.length;
  const done = Object.values(saved).filter(r => r.verdict).length;
  const p1 = CLAIMS.filter(c => c.priority===1).length;
  const p1done = CLAIMS.filter(c => c.priority===1 && (saved[c.id]||{}).verdict).length;
  document.getElementById('progress').textContent =
    `${done} reviewed · P1 ${p1done}/${p1}`;
}

document.getElementById('list').addEventListener('click', e => {
  const btn = e.target.closest('.v'); if(!btn) return;
  const card = btn.closest('.card'), id = card.dataset.id, v = btn.dataset.v;
  const rec = saved[id] || (saved[id] = {});
  rec.verdict = rec.verdict === v ? '' : v;
  rec.at = new Date().toISOString();
  rec.by = document.getElementById('who').value || '';
  persist();
  card.querySelectorAll('.v').forEach(b => b.classList.toggle('sel', b.dataset.v === rec.verdict));
  card.querySelector('.notes').classList.toggle('show', !!rec.verdict && rec.verdict !== 'notclaim');
  render();
});
/* Keys 1-8 set the verdict on whichever card the reviewer is looking at. A reviewer works
   through thousands of these, and reaching for the mouse eight times a sentence is the
   difference between an afternoon and a week. Ignored while typing in a note or a filter. */
/* ⛔ THREE DEFECTS CODEX REPRODUCED IN THE FIRST VERSION OF THIS, ALL FIXED HERE:
   1. It picked the card whose MIDPOINT was nearest the viewport centre. On a tall card that
      fills the screen, the NEXT card's midpoint can be closer -- so the reviewer answers a
      sentence they cannot see. There is now an explicit ACTIVE card, outlined on screen, and
      the key only ever answers that one.
   2. It routed through .click(), and the click handler TOGGLES -- so pressing the key for a
      verdict already recorded silently cleared it. A shortcut must set, never unset.
   3. It ignored e.repeat and isContentEditable: holding a key fired repeatedly (toggling on and
      off), and typing in a contenteditable region was treated as a shortcut.
   Button order is also no longer positional -- the key maps to an explicit data-v value, so
   re-ordering the buttons cannot silently remap the keys. */
const KEY_VERDICT = {1:'ok',2:'source',3:'notclaim',4:'rewrite',
                     5:'disputed',6:'misleading',7:'preclinical',8:'population'};
let activeCard = null;
function setActive(card){
  if(activeCard === card) return;
  document.querySelectorAll('.card.active').forEach(c => c.classList.remove('active'));
  activeCard = card;
  if(card) card.classList.add('active');
}
/* The active card is chosen by the reviewer -- clicking anywhere in one, or moving with J/K --
   never inferred from scroll position. */
document.getElementById('list').addEventListener('mousedown', e => {
  const card = e.target.closest('.card'); if(card) setActive(card);
});
document.addEventListener('keydown', e => {
  if(e.metaKey || e.ctrlKey || e.altKey || e.repeat) return;
  const t = e.target;
  if(t.isContentEditable) return;
  const tag = t.tagName;
  if(tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

  const cards = [...document.querySelectorAll('.card')];
  if(!cards.length) return;
  if(e.key === 'j' || e.key === 'k'){            // move the active card, do not answer
    const i = activeCard ? cards.indexOf(activeCard) : -1;
    const next = e.key === 'j' ? Math.min(i + 1, cards.length - 1) : Math.max(i - 1, 0);
    setActive(cards[i === -1 ? 0 : next]);
    activeCard.scrollIntoView({block:'center'});
    e.preventDefault();
    return;
  }
  const v = KEY_VERDICT[parseInt(e.key, 10)];
  if(!v) return;
  /* ⛔ THE ACTIVE CARD MUST STILL BE IN THE DOCUMENT AND STILL ON SCREEN.
     render() replaces the whole list via innerHTML, which DETACHES the node activeCard points
     at without clearing the variable. Codex reproduced the consequence: select card A, filter or
     page so B is shown, press a verdict key -> the verdict is written to A, a claim the reviewer
     can no longer see. Scrolling away armed an offscreen card the same way. A stale reference is
     not a selection, so both are re-checked at the moment the key is pressed, not when it was
     chosen. */
  if(activeCard && !document.contains(activeCard)) setActive(null);
  if(activeCard){
    const r = activeCard.getBoundingClientRect();
    if(r.bottom <= 0 || r.top >= window.innerHeight) setActive(null);
  }
  if(!activeCard){                                // nothing valid chosen: select, never guess
    setActive(cards[0]); activeCard.scrollIntoView({block:'center'}); e.preventDefault(); return;
  }
  const id = activeCard.dataset.id;
  const rec = saved[id] || (saved[id] = {});
  if(rec.verdict === v) { e.preventDefault(); return; }   // already set: no-op, never a toggle
  rec.verdict = v;
  rec.at = new Date().toISOString();
  rec.by = document.getElementById('who').value || '';
  persist();
  activeCard.querySelectorAll('.v').forEach(b => b.classList.toggle('sel', b.dataset.v === v));
  activeCard.querySelector('.notes').classList.toggle('show', v !== 'notclaim');
  // The mouse path calls render(); this one did not, so the progress counter and the verdict
  // filters went stale after every keyboard verdict -- the reviewer saw "0 reviewed" while
  // recording answers. Re-render, then restore the selection by ID, because render() rebuilds
  // the DOM and the old node reference dies with it.
  render();
  const again = document.querySelector('.card[data-id="' + id + '"]');
  if (again) setActive(again); else setActive(null);
  e.preventDefault();
});
document.getElementById('list').addEventListener('input', e => {
  const card = e.target.closest('.card'); if(!card) return;
  const rec = saved[card.dataset.id] || (saved[card.dataset.id] = {});
  if(e.target.classList.contains('note')) rec.note = e.target.value;
  if(e.target.classList.contains('src')) rec.source = e.target.value;
  rec.by = document.getElementById('who').value || rec.by || '';
  persist();
});

function mkChips(el, items, set, labelFn){
  el.innerHTML = items.map(i =>
    `<span class="chip ${set.has(i)?'on':''}" data-v="${i}">${labelFn(i)}</span>`).join('');
  el.addEventListener('click', e => {
    const c = e.target.closest('.chip'); if(!c) return;
    let v = c.dataset.v; if(!isNaN(parseInt(v)) && el.id === 'prio') v = parseInt(v);
    set.has(v) ? set.delete(v) : set.add(v);
    c.classList.toggle('on'); page = 0; render();
  });
}

function dl(name, text, type){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type}));
  a.download = name; a.click();
}
document.getElementById('exportJson').onclick = () => {
  const out = CLAIMS.filter(c => saved[c.id] && saved[c.id].verdict).map(c =>
    Object.assign({id:c.id, chapter:c.chapter, section:c.section, para:c.para,
      priority:c.priority, kinds:c.kinds, text:c.text}, saved[c.id]));
  dl('book-review-verdicts.json', JSON.stringify({exported:new Date().toISOString(),
    reviewer:document.getElementById('who').value, count:out.length, verdicts:out}, null, 1),
    'application/json');
};
document.getElementById('exportCsv').onclick = () => {
  const q = s => '"' + String(s==null?'':s).replace(/"/g,'""') + '"';
  const rows = [['id','priority','chapter','section','para','kinds','verdict','source','note','by','at','text']];
  CLAIMS.forEach(c => { const r = saved[c.id]; if(!r || !r.verdict) return;
    rows.push([c.id,c.priority,c.chapter,c.section,c.para,c.kinds.join('|'),
      r.verdict,r.source||'',r.note||'',r.by||'',r.at||'',c.text]); });
  dl('book-review-verdicts.csv', rows.map(r => r.map(q).join(',')).join('\n'), 'text/csv');
};
document.getElementById('importBtn').onclick = () => document.getElementById('importFile').click();
document.getElementById('importFile').onchange = e => {
  const f = e.target.files[0]; if(!f) return;
  const rd = new FileReader();
  rd.onload = () => { try {
      const d = JSON.parse(rd.result);
      (d.verdicts || []).forEach(v => { saved[v.id] = {verdict:v.verdict, note:v.note,
        source:v.source, by:v.by, at:v.at}; });
      persist(); render();
    } catch(err){ alert('Could not read that file: ' + err.message); } };
  rd.readAsText(f);
};
document.getElementById('prev').onclick = () => { page--; render(); window.scrollTo(0,0); };
document.getElementById('next').onclick = () => { page++; render(); window.scrollTo(0,0); };
['chapter','status'].forEach(id => document.getElementById(id).onchange = e => {
  state[id] = e.target.value; page = 0; render(); });
document.getElementById('q').oninput = e => { state.q = e.target.value; page = 0; render(); };
const who = document.getElementById('who');
who.value = localStorage.getItem(KEY + '-who') || '';
who.oninput = () => localStorage.setItem(KEY + '-who', who.value);

/* \u26d4 THE DATA IS EMBEDDED IN THIS FILE. There is no fetch and no loading state, because there is
   nothing to wait for.
   This page used to fetch('claims.json'). Two consequences, both found by review:
     - From file:// that fetch is blocked in every current browser, so a clinician who saved the
       page and opened it from disk got the header, the filters, the pager and NO SENTENCES. The
       page promised to work offline and did not.
     - Over http it was a ~0.2 MB request with no affordance, so a slow load looked exactly like a
       deleted tool. the project owner hit precisely that and reasonably concluded the thing was gone.
   Inlining was assumed too large. Measured: 0.23 MB, which is SMALLER than the file it replaced,
   because compact serialisation saves 12%. The assumption was wrong and the measurement was
   cheap. Now the sentences are present the moment the HTML is, from disk or from a server. */
(function(){
  const el = document.getElementById('claims-data');
  let d = null;
  try { d = JSON.parse(el.textContent); }
  catch (err) {
    document.getElementById('list').innerHTML =
      '<p class="loadmsg err">The review data in this file could not be read.<br><small>'
      + String(err).replace(/[<>&]/g, '') + '</small><br><small>This page is self-contained, so a '
      + 'reload will not help \u2014 the file itself is damaged. Ask for a fresh copy rather than '
      + 'reviewing from an empty page.</small></p>';
    throw err;
  }
  CLAIMS = d.claims; HREF = d.href || {};
  const sel = document.getElementById('chapter');
  [...new Set(CLAIMS.map(c => c.chapter))].forEach(c => {
    const o = document.createElement('option'); o.value = c; o.textContent = shortChapter(c);
    sel.appendChild(o); });
  mkChips(document.getElementById('prio'), [1,2,3,4], state.prio,
    p => ({1:'P1 doses & approval',2:'P2 results & research',3:'P3 mechanism',4:'P4 narrative'})[p]);
  mkChips(document.getElementById('kinds'), KINDS, state.kinds, k => KIND_LABEL[k]);
  render();
})();
</script>
</body>
</html>
"""


def _gate(page):
    """Refuse to write a page that is syntactically valid but semantically dead.

    ⛔ WHY SYNTAX CHECKING WAS NOT ENOUGH. An edit to this file once removed
    usableEngines() while leaving two calls to it. `node --check` passed --
    the syntax is perfectly legal -- and the page would have thrown
    ReferenceError on the first card render. Every card. Silently, because
    nothing on the page reports a thrown handler.

    That is the same shape as every other failure this project has paid for:
    the check that ran was not the check that mattered. So this gate does three
    things in order, and ANY of them failing stops the write:
      1. there is an executable script at all (not just the JSON data island)
      2. it parses
      3. every function it CALLS is actually DEFINED somewhere reachable
    """
    import re as _re, subprocess as _sp, tempfile as _tf

    all_blocks = _re.findall(r'<script([^>]*)>(.*?)</script>', page, _re.S | _re.I)
    blocks = [body for attrs, body in all_blocks
              if not _re.search(r'\btype\s*=\s*["\']application/json["\']', attrs, _re.I)
              and body.strip()]
    if not blocks:
        raise SystemExit('⛔ BUILD GATE: no executable script in the page. Not written.')

    for i, body in enumerate(blocks):
        with _tf.NamedTemporaryFile('w', suffix='.js', delete=False) as fh:
            fh.write(body); tmp = fh.name
        r = _sp.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit('⛔ BUILD GATE: script block %d does not parse:\n%s'
                             % (i, r.stderr[:600]))

    # --- the check node --check cannot do -----------------------------------
    js = '\n'.join(blocks)

    # ⛔ DEAD END, KEPT AS A WARNING -- see _smoke() below for what replaced it.
    #    I tried to find undefined references by pattern-matching the source, and
    #    spent four rounds fighting my own parser: prose in comments ("fired
    #    repeatedly (toggling...)") looked like calls, CSS inside template literals
    #    made `var(--ink)` look like a call, and a stray backtick mis-paired the
    #    template matcher and swallowed the region where linkify() was defined --
    #    reporting a DEFINED function as missing. Every fix produced a new false
    #    positive on correct code.
    #
    #    The lesson is the one this project keeps paying to relearn: EXERCISE THE
    #    CODE, DO NOT PATTERN-MATCH IT. A regex approximation of a JS scope analyser
    #    is a second, worse implementation of something node already does perfectly
    #    by running the file. _smoke() runs it.
    _smoke(page)


SMOKE_JS = r"""
// Minimal DOM so the page's script can load and its render path can run.
// This is NOT a browser -- it is just enough surface that a ReferenceError,
// a TypeError or a thrown handler surfaces instead of being swallowed.
const mkEl = () => ({
  style:{}, dataset:{}, classList:{add(){},remove(){},toggle(){},contains(){return false}},
  appendChild(){}, removeChild(){}, remove(){}, insertBefore(){},
  addEventListener(){}, removeEventListener(){}, setAttribute(){}, getAttribute(){return null},
  querySelector(){return null}, querySelectorAll(){return []},
  getBoundingClientRect(){return {top:0,bottom:10,left:0,right:10,height:10,width:10}},
  scrollIntoView(){}, focus(){}, click(){}, closest(){return null},
  get innerHTML(){return ''}, set innerHTML(v){}, textContent:'', value:'', checked:false,
  files:[], disabled:false, children:[], parentNode:null,
});
// The page reads its data from an embedded JSON island. The stub has to SERVE that
// island for real -- an empty textContent makes JSON.parse throw, which would fail
// every build for a reason that has nothing to do with the code being checked.
let DATA_JSON = '';
const document = {
  addEventListener(){}, removeEventListener(){}, createElement:mkEl,
  getElementById(id){ const el = mkEl(); if (id === 'claims-data') el.textContent = DATA_JSON; return el; },
  querySelector(sel){ const el = mkEl(); if (String(sel).includes('claims-data')) el.textContent = DATA_JSON; return el; },
  querySelectorAll(){return []},
  body:mkEl(), documentElement:mkEl(), readyState:'complete',
};
const window = { addEventListener(){}, removeEventListener(){}, innerHeight:900,
                 scrollTo(){}, location:{hash:'',href:''}, matchMedia(){return {matches:false,addEventListener(){}}} };
const localStorage = { _d:{}, getItem(k){return this._d[k]||null}, setItem(k,v){this._d[k]=v}, removeItem(k){delete this._d[k]} };
const navigator = { userAgent:'smoke' };
globalThis.document = document; globalThis.window = window;
globalThis.localStorage = localStorage; globalThis.navigator = navigator;
globalThis.requestAnimationFrame = f => f();
globalThis.alert = () => {}; globalThis.confirm = () => true;

const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');
const island = page.match(/<script id="claims-data"[^>]*>([\s\S]*?)<\/script>/i);
if (island) DATA_JSON = island[1].replace(/\\u003c/g, '<');
const blocks = [...page.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)]
  .filter(m => !/\btype\s*=\s*["']application\/json["']/i.test(m[1]) && m[2].trim())
  .map(m => m[2]);
if (!blocks.length) { console.error('SMOKE: no executable script'); process.exit(2); }

// 1. LOAD. Catches ReferenceError on any top-level call, and any syntax the parser took
//    but the engine rejects.
let scope;
try {
  scope = new Function(blocks.join('\n') + '\n; return typeof render === "function" ? {render, CLAIMS: (typeof CLAIMS!=="undefined"?CLAIMS:null)} : {};')();
} catch (e) {
  console.error('SMOKE: script threw on load -> ' + e.constructor.name + ': ' + e.message);
  process.exit(2);
}

// 2. EXERCISE THE RENDER PATH. Loading proves the file parses and its top level runs;
//    it does NOT prove a function called only from render() exists. That was the exact
//    bug: usableEngines was deleted while two calls to it survived, and nothing at load
//    time touched them.
if (typeof scope.render === 'function') {
  try { scope.render(); }
  catch (e) { console.error('SMOKE: render() threw -> ' + e.constructor.name + ': ' + e.message); process.exit(3); }
  console.log('SMOKE: loaded and render() ran clean');
} else {
  console.log('SMOKE: loaded clean (no render() exported -- load-only check)');
}
"""


def _smoke(page):
    """Run the page in node. Do not pattern-match it -- run it.

    ⛔ WHY THIS EXISTS. `node --check` proves a file PARSES. It does not prove the
    file WORKS. An edit here once deleted usableEngines() and left two calls to it:
    legal syntax, clean --check, and ReferenceError on every single card render.
    Nothing on the page reports a thrown handler, so the failure is silent and looks
    like an empty list.

    I then spent four rounds writing a regex scope analyser to catch it, and each
    round produced a new false positive on CORRECT code -- prose in comments, CSS
    inside template literals, a stray backtick swallowing the region where linkify()
    was defined. A gate that fires on correct code gets switched off, which is worse
    than no gate.

    So: node already has a perfect JS implementation. Use it. This loads the real
    script and calls the real render path, which is the only thing that proves the
    functions render() needs are actually there.
    """
    import subprocess as _sp, tempfile as _tf
    with _tf.NamedTemporaryFile('w', suffix='.html', delete=False) as fh:
        fh.write(page); html = fh.name
    with _tf.NamedTemporaryFile('w', suffix='.cjs', delete=False) as fh:
        fh.write(SMOKE_JS); js = fh.name
    try:
        r = _sp.run(['node', js, html], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(html); os.unlink(js)
    if r.returncode != 0:
        raise SystemExit('⛔ BUILD GATE: %s\n   Page NOT written.'
                         % (r.stderr.strip() or r.stdout.strip() or 'node exited %d' % r.returncode))
    print('   gate: %s' % r.stdout.strip())


def main():
    data = json.load(open(os.path.join(HERE, 'claims.json')))
    os.makedirs(SITE, exist_ok=True)
    # claims.json is still written beside the page: sources.html links into it, and having the
    # data separately readable is useful. The PAGE no longer depends on it.
    shutil.copy(os.path.join(HERE, 'claims.json'), os.path.join(SITE, 'claims.json'))

    # ⛔ The ONLY safe way to put JSON inside <script>: the parser ends the element at the first
    # literal "</script" regardless of JSON quoting, so a claim containing that text would
    # terminate the block early and spray the rest of the manuscript into the document as markup.
    # Escaping the slash keeps the JSON byte-identical in meaning while making that impossible.
    # "<!--" is escaped for the same reason.
    # ⛔ ESCAPE THE '<' ITSELF, AS <. My first version wrote '<\\!--', and "\!" IS NOT A
    # VALID JSON ESCAPE -- JSON.parse rejects it outright, so a single claim containing "<!--"
    # would have stopped the whole page loading. Codex tested it. '\\/' happens to be legal JSON
    # so that half worked, but mixing a legal and an illegal escape to solve one problem is
    # exactly the kind of near-miss that reads as fine. < is valid JSON, decodes back to
    # '<' byte-for-byte, and neutralises BOTH '</script' and '<!--' with one rule.
    blob = json.dumps(data, separators=(',', ':')).replace('<', '\\u003c')
    page = (PAGE.replace('__COUNT__', '{:,}'.format(len(data['claims'])))
                .replace('__PARAS__', '{:,}'.format(data['paragraphs']))
                .replace('__SRC__', data['source'])
                .replace('__MD5__', data['source_md5'])
                .replace('__CLAIMS_JSON__', blob))
    # ⛔ VALIDATE BEFORE WRITING. A broken page must never reach disk, because a
    #    stale-but-working index.html is a better artifact than a fresh broken one.
    _gate(page)

    with open(os.path.join(SITE, 'index.html'), 'w') as f:
        f.write(page)
    size = os.path.getsize(os.path.join(SITE, 'index.html'))
    print('wrote %s (%.2f MB, data EMBEDDED — no fetch, works from file://) '
          '+ claims.json (%d claims)' % (
              os.path.join(SITE, 'index.html'), size / 1048576.0, len(data['claims'])))


if __name__ == '__main__':
    main()
