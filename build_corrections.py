#!/usr/bin/env python3
"""Render the Factual Corrections Sheet as a linked page.

  python3 build_corrections.py   # -> site/corrections/index.html

The sheet is A. Author' own reviewed document, so the claims it names carry
its provenance on their cards, and each one links to its entry here.
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'site', 'corrections')

CSS = """
/* Claude Design spec v1 tokens, shared with the desk and the chapter pages.
   ⛔ --bad/--good/--amber are gone. This page lists errors the AUTHOR HIMSELF supplied and
   approved; painting the quoted passage red and the replacement green stages an argument he has
   already settled, and the red bled onto the desk card too. The distinction that matters is
   current-wording vs proposed-wording, which is structure -- a left rule -- not hue. */
:root{--bg:#F4F2EE;--paper:#FFFFFF;--surface-2:#ECE9E3;--ink:#1C1C1A;--ink-2:#55534E;
  --muted:#8A867E;--line:#DDD9D1;--line-2:#B8B3A9;--link:#3B5B7A;--hit:#F3E9B8;
  --navy:var(--link);--bad:var(--ink);--bad-bg:var(--surface-2);
  --good:var(--ink);--good-bg:var(--surface-2);--amber:var(--ink-2)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 Georgia,"Iowan Old Style","Times New Roman",serif}
header{background:var(--paper);color:var(--ink);border-bottom:1px solid var(--line);padding:14px 20px;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header a{color:var(--link);text-decoration:none;font-size:13px;margin-right:14px}
header a:hover{text-decoration:underline}
.banner{background:var(--surface-2);border-bottom:1px solid var(--line);color:var(--ink-2);padding:9px 20px;
  font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:30px 22px 80px;background:var(--paper);
  border-left:1px solid var(--line);border-right:1px solid var(--line);min-height:100vh}
h1{color:var(--navy);font-size:34px;line-height:1.15;margin:0 0 6px;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-weight:700}
.sub{font-style:italic;color:#3d4a57;font-size:19px;margin:0 0 20px}
.meta{font-size:14.5px;margin:0 0 4px}
.meta b{font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px}
hr.rule{border:0;border-top:3px solid var(--navy);margin:22px 0 26px}
h2{color:var(--navy);font-size:22px;margin:34px 0 4px;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h2+p.note{font-style:italic;color:var(--muted);font-size:14.5px;margin:0 0 20px;
  border-bottom:1px solid var(--line);padding-bottom:12px}
h3{font-size:18px;margin:30px 0 2px;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
h3 .n{color:var(--navy)}
.loc{color:var(--muted);font-size:14px;margin:0 0 14px;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif}
.lbl{font:600 11.5px/1 -apple-system,BlinkMacSystemFont,sans-serif;letter-spacing:.08em;
  text-transform:uppercase;margin:16px 0 6px}
.lbl.cur{color:var(--bad)} .lbl.prob{color:var(--amber)} .lbl.rep{color:var(--good)}
blockquote{margin:0;padding:13px 16px;border-left:2px solid var(--line-2);
  background:transparent;font-size:15.5px}
blockquote.rep{border-left-color:var(--good);background:var(--good-bg)}
p.prob{margin:0;font-size:15.5px}
.alt{font-size:14px;color:var(--muted);border-left:3px solid var(--line);
  padding:8px 13px;margin:13px 0 0}
table{border-collapse:collapse;width:100%;font-size:14px;margin:14px 0 0;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif}
th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
td a{color:var(--good)}
.sev{font-weight:600}
.sev.substantive{color:var(--bad)} .sev.terminology{color:var(--amber)}
.sev.typographic{color:var(--muted)}
.spanish{background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:14px 16px;
  margin:30px 0 0;font-size:14.5px}
.jump{font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px}
.jump a{color:var(--link)}
:target h3{background:var(--hit);border-radius:3px;padding-left:5px;margin-left:-5px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#141311;--paper:#1C1B19;--surface-2:#242220;--ink:#E9E5DD;--ink-2:#A9A49B;
  --muted:#78746C;--line:#2F2D29;--line-2:#4A4741;--link:#8FB0CF;--hit:#5A4A12}}
"""


def esc(s):
    return html.escape(s or '', quote=False)


def main():
    sheet = json.load(open(os.path.join(HERE, 'corrections', 'corrections.json')))
    claims = json.load(open(os.path.join(HERE, 'claims.json')))
    # claim id per correction number, so the sheet links back into the review
    back = {}
    for c in claims['claims']:
        if c.get('correction'):
            back[c['correction']['n']] = (c['id'], claims['href'].get(c['id'], ''), c['text'])

    os.makedirs(OUT, exist_ok=True)
    items = []
    for it in sheet['items']:
        cid, href, current = back.get(it['n'], ('', '', ''))
        jump = ''
        if cid:
            jump = ('<p class="jump"><a href="../index.html">Open in the claim review</a> · '
                    '<a href="../%s">Read it in the manuscript ↗</a> · <code>%s</code></p>'
                    % (esc(href), esc(cid)))
        items.append("""<h3 id="c%d"><span class="n">%d.</span> %s</h3>
<p class="loc">Chapter %s</p>
<p class="lbl cur">Current text</p>
<blockquote>%s</blockquote>
<p class="lbl prob">Problem</p>
<p class="prob">%s</p>
<p class="lbl rep">Suggested replacement</p>
<blockquote class="rep">%s</blockquote>
%s%s""" % (it['n'], it['n'], esc(it['label']), esc(it['chapter_per_sheet']),
           esc(current or '(see the manuscript)'),
           esc(it['problem']), esc(it['replacement']),
           ('<p class="alt">%s</p>' % esc(it['alternative'])) if it.get('alternative') else '',
           jump))

    rows = ''.join(
        '<tr><td>%d</td><td><a href="#c%d">%s</a></td><td>%s</td><td class="sev %s">%s</td></tr>'
        % (it['n'], it['n'], esc(it['label']), esc(it['chapter_per_sheet']),
           it['severity'], it['severity'])
        for it in sheet['items'])

    page = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Factual Corrections Sheet — Sample Manuscript</title><style>%s</style></head><body>
<header><a href="../index.html">← Claim review</a><a href="../text/index.html">The manuscript</a></header>
<div class="banner">Internal review document. Not published, not indexed, not medical advice.</div>
<div class="wrap">
<h1>Factual Corrections Sheet</h1>
<p class="sub">Sample Manuscript — A. Author and B. Author</p>
<p class="meta"><b>Prepared for:</b> A. Author</p>
<p class="meta"><b>Date:</b> September 20, 2026</p>
<p class="meta"><b>Source manuscript:</b> %s</p>
<p class="meta"><b>Scope:</b> The five factual errors flagged in Manuscript_Review_Part_II.md
(Critical Issues, Section A), located verbatim in the English manuscript, plus three additional
items found during the sweep.</p>
<hr class="rule">
<h2>The eight errors</h2>
<p class="note">All eight located in the manuscript this review indexes — one sentence each, no
misses and no ambiguous matches. Every item links to the sentence in the book and to its card in
the claim review.</p>
%s
<h2>Summary</h2>
<table><tr><th>#</th><th>Error</th><th>Chapter</th><th>Severity</th></tr>%s</table>
<div class="spanish"><b>Note on the Spanish edition.</b> %s</div>
<div class="spanish"><b>Note on the source file.</b> %s</div>
</div></body></html>""" % (CSS, esc(sheet['sheet_source_manuscript']), '\n'.join(items),
                           rows, esc(sheet['spanish_note']), esc(sheet['note']))

    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(page)
    print('wrote %s (%d bytes), %d items, %d linked back to a claim'
          % (os.path.join(OUT, 'index.html'), os.path.getsize(os.path.join(OUT, 'index.html')),
             len(sheet['items']), len(back)))


if __name__ == '__main__':
    main()
