#!/usr/bin/env python3
"""Render the manuscript as linked HTML, one page per chapter, every sentence anchored.

  python3 build_book.py     # -> site/text/index.html + site/text/ch-NN.html

Each sentence carries id="<claim id>", so a review card links straight to the
sentence in its chapter and the page highlights it on arrival. Flagged sentences
are underlined in the running text, with priority-1 marked more strongly, so a
reader of the book can see what the register caught without leaving the prose.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'site', 'text')

CSS = """
/* Same tokens as the reviewer desk (Claude Design spec v1) so the two surfaces are one product.
   ⛔ --p1 was red and --p2 orange: on a page of continuous prose that reads as "these sentences
   are WRONG", which is a verdict nobody has reached yet. Priority only means "a reviewer should
   look at this one first". It is now weight, not hue. */
:root{--bg:#F4F2EE;--paper:#FFFFFF;--surface-2:#ECE9E3;--ink:#1C1C1A;--ink-2:#55534E;
  --muted:#8A867E;--line:#DDD9D1;--line-2:#B8B3A9;--hit:#F3E9B8;--link:#3B5B7A;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:17px/1.68 Georgia,"Iowan Old Style","Times New Roman",serif}
header{background:var(--paper);color:var(--ink);padding:14px 20px;
  border-bottom:1px solid var(--line);font-family:var(--sans)}
header a{color:var(--link);text-decoration:none;font-size:13px}
header a:hover{text-decoration:underline}
header h1{margin:3px 0 0;font-size:17px;font-weight:600}
.banner{background:var(--surface-2);border-bottom:1px solid var(--line);color:var(--ink-2);
  padding:9px 20px;font:13px/1.5 var(--sans)}
.wrap{max-width:720px;margin:0 auto;padding:26px 20px 70px;background:var(--paper);
  border-left:1px solid var(--line);border-right:1px solid var(--line);min-height:100vh}
h2.chap{font-size:22px;line-height:1.3;margin:0 0 6px}
h3.sec{font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  margin:30px 0 8px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
p.para{margin:0 0 15px}
.num{font:11px/1 -apple-system,BlinkMacSystemFont,sans-serif;color:#b8b3a8;
  float:left;margin-left:-44px;width:34px;text-align:right;padding-top:6px}
s-1,s-2,s-3,s-4{display:inline}
.f1{border-bottom:1px solid var(--ink)}
.f2{border-bottom:1px solid var(--line-2)}
/* A known factual error is outlined, not tinted: dashed means "still open" across this design. */
.known{outline:1px dashed var(--line-2);outline-offset:2px}
:target{background:var(--hit);box-shadow:0 0 0 3px var(--hit);border-radius:2px}
nav.toc{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15px}
nav.toc a{display:block;padding:9px 0;border-bottom:1px solid var(--line);
  color:var(--ink);text-decoration:none}
nav.toc a:hover{color:var(--link)}
nav.toc .n{color:var(--muted);font-size:12.5px}
.pager{display:flex;justify-content:space-between;gap:12px;margin:34px 0 0;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:14px}
.pager a{color:var(--link);text-decoration:none}
.legend{font:12.5px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;color:var(--muted);
  border-top:1px solid var(--line);padding-top:12px;margin-top:26px}
@media (max-width:760px){.num{display:none}.wrap{padding:20px 16px 60px}}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#141311;--paper:#1C1B19;--surface-2:#242220;--ink:#E9E5DD;--ink-2:#A9A49B;
  --muted:#78746C;--line:#2F2D29;--line-2:#4A4741;--hit:#5A4A12;--link:#8FB0CF}}
"""


def esc(s):
    return html.escape(s, quote=False)


def main():
    data = json.load(open(os.path.join(HERE, 'claims.json')))
    claims = data['claims']
    paras = data['paras']

    # group claims by chapter, preserving book order
    chapters, order = {}, []
    for c in claims:
        if c['chapter'] not in chapters:
            chapters[c['chapter']] = []
            order.append(c['chapter'])
        chapters[c['chapter']].append(c)

    os.makedirs(OUT, exist_ok=True)
    files = []
    for i, ch in enumerate(order):
        files.append(('ch-%02d.html' % (i + 1), ch, chapters[ch]))

    for i, (fn, ch, cs) in enumerate(files):
        # rebuild paragraphs from their sentences so every sentence gets an anchor
        by_para, seq = {}, []
        for c in cs:
            if c['para'] not in by_para:
                by_para[c['para']] = []
                seq.append(c['para'])
            by_para[c['para']].append(c)

        body, cur_sec = [], None
        for pnum in seq:
            group = sorted(by_para[pnum], key=lambda c: c['sent'])
            sec = group[0]['section']
            if sec and sec != cur_sec:
                body.append('<h3 class="sec">%s</h3>' % esc(sec))
                cur_sec = sec
            out = ['<p class="para"><span class="num">%d</span>' % pnum]
            for c in group:
                cls = []
                if c['priority'] == 1:
                    cls.append('f1')
                elif c['priority'] == 2:
                    cls.append('f2')
                if c.get('correction'):
                    cls.append('known')
                title = ', '.join(c['kinds']) if c['kinds'] else ''
                out.append('<span id="%s" class="%s"%s>%s</span> ' % (
                    c['id'], ' '.join(cls),
                    (' title="%s"' % esc(title)) if title else '',
                    esc(c['text'])))
            out.append('</p>')
            body.append(''.join(out))

        prev = '<a href="%s">← %s</a>' % (files[i - 1][0], esc(files[i - 1][1][:44])) if i else '<span></span>'
        nxt = '<a href="%s">%s →</a>' % (files[i + 1][0], esc(files[i + 1][1][:44])) if i + 1 < len(files) else '<span></span>'
        p1 = sum(1 for c in cs if c['priority'] == 1)
        page = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>%s — Sample Manuscript</title><style>%s</style></head><body>
<header><a href="index.html">← All chapters</a> · <a href="../index.html">Claim review</a>
<h1>%s</h1></header>
<div class="banner">Sample manuscript. Every sentence here is invented for design work —
not medical advice.</div>
<div class="wrap">
<h2 class="chap">%s</h2>
%s
<p class="legend">%d sentences on this page, %d of them priority&nbsp;1.
A <span class="f1">solid underline</span> marks a priority-1 claim, a
<span class="f2">fainter underline</span> a priority-2 claim, and a
<span class="known">dashed outline</span> a sentence carrying a known factual error.
<b>Priority means &ldquo;read this one first&rdquo;, not &ldquo;this one is wrong&rdquo;</b> — nothing
on this page has been judged yet. Hover a sentence to see why it was flagged.
Every sentence has its own link — copy the address after clicking one.</p>
<div class="pager">%s %s</div>
</div></body></html>""" % (esc(ch[:60]), CSS, esc(ch[:60]), esc(ch), '\n'.join(body),
                           len(cs), p1, prev, nxt)
        with open(os.path.join(OUT, fn), 'w') as f:
            f.write(page)

    rows = []
    for fn, ch, cs in files:
        p1 = sum(1 for c in cs if c['priority'] == 1)
        known = sum(1 for c in cs if c.get('correction'))
        rows.append('<a href="%s">%s<span class="n"> — %d sentences · %d priority 1%s</span></a>'
                    % (fn, esc(ch), len(cs), p1,
                       ' · <b>%d known error%s</b>' % (known, '' if known == 1 else 's') if known else ''))
    idx = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Sample Manuscript — manuscript</title><style>%s</style></head><body>
<header><a href="../index.html">← Claim review</a><h1>Sample Manuscript — the manuscript</h1></header>
<div class="banner">Sample manuscript. Every sentence here is invented for design work —
not medical advice. Source file <code>%s</code> (md5 <code>%s</code>).</div>
<div class="wrap"><nav class="toc">%s</nav>
<p class="legend">%s sentences across %d chapters. Every sentence is individually
addressable, so a claim in the review tool links straight to the sentence in its
chapter.</p></div></body></html>""" % (
        CSS, esc(data['source']), data['source_md5'], '\n'.join(rows),
        '{:,}'.format(len(claims)), len(files))
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(idx)

    # tell the review tool where each claim lives
    href = {}
    for fn, ch, cs in files:
        for c in cs:
            href[c['id']] = 'text/%s#%s' % (fn, c['id'])
    data['href'] = href
    with open(os.path.join(HERE, 'claims.json'), 'w') as f:
        json.dump(data, f, indent=1)

    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print('wrote %d chapter pages + index into %s (%d bytes total)'
          % (len(files), OUT, total))
    print('claims.json now carries href for %d claims' % len(href))


if __name__ == '__main__':
    main()
