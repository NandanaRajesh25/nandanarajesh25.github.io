"""Move the molecules section ahead of the abstract, and reorder the contents bar."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "template.html")
html = open(P).read()

START = "<!-- ============ MOLECULES ============ -->"
END = "<!-- ============ RESULTS ============ -->"
ANCHOR = "<!-- ============ ABSTRACT ============ -->"

i = html.index(START)
j = html.index(END)
block = html[i:j]
rest = html[:i] + html[j:]

k = rest.index(ANCHOR)
out = rest[:k] + block + rest[k:]

# contents bar: Molecules first
old_nav = """    <a href="#abstract">Abstract</a>
    <a href="#contributions">Contributions</a>
    <a href="#background">Background</a>
    <a href="#method">Method</a>
    <a href="#respacing">Respacing</a>
    <a href="#diversity">Diversity</a>
    <a href="#molecules">Molecules</a>
"""
new_nav = """    <a href="#molecules">Molecules</a>
    <a href="#abstract">Abstract</a>
    <a href="#contributions">Contributions</a>
    <a href="#background">Background</a>
    <a href="#method">Method</a>
    <a href="#respacing">Respacing</a>
    <a href="#diversity">Diversity</a>
"""
assert old_nav in out, "nav block not found"
out = out.replace(old_nav, new_nav)

assert out.count(START) == 1 and out.count(END) == 1
assert out.index(START) < out.index(ANCHOR), "molecules did not move ahead of abstract"
open(P, "w").write(out)

order = []
for tag in ("MOLECULES", "ABSTRACT", "CONTRIBUTIONS", "BACKGROUND", "METHOD",
            "RESPACING", "DIVERSITY", "RESULTS", "CONDITIONAL", "ABLATIONS",
            "LIMITATIONS", "CITE"):
    m = "<!-- ============ %s ============ -->" % tag
    if m in out:
        order.append((out.index(m), tag))
order.sort()
print("section order:", " -> ".join(t for _, t in order))
