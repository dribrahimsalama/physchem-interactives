#!/usr/bin/env python3
"""Unwrap/rewrap the escaped iframe srcdoc used by each interactive's index.html.

  srcdoc.py unwrap PAGE.html OUT.html   # readable inner document
  srcdoc.py wrap   PAGE.html IN.html    # write IN.html back into PAGE.html's srcdoc (in place)
"""
import html, re, sys

PAT = re.compile(r'(srcdoc=")(.*?)("\s*>\s*</iframe>)', re.S)

def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("unwrap", "wrap"):
        sys.exit(__doc__)
    cmd, page, other = sys.argv[1:]
    src = open(page, encoding="utf-8").read()
    m = PAT.search(src)
    if not m:
        sys.exit("no srcdoc iframe found in " + page)
    if cmd == "unwrap":
        open(other, "w", encoding="utf-8").write(html.unescape(m.group(2)))
    else:
        inner = html.escape(open(other, encoding="utf-8").read(), quote=True)
        open(page, "w", encoding="utf-8").write(src[:m.start(2)] + inner + src[m.end(2):])

main()
