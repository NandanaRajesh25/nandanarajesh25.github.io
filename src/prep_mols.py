"""Validate QM9 sample .txt files and emit JSON for the webpage."""
import json
import math
import os
import sys

MOL_DIR = sys.argv[1]
OUT = sys.argv[2]

ALLOWED = {"H", "C", "N", "O", "F"}
ORDER = ["C", "H", "N", "O", "F"]

# Covalent-radius based bond detection, mirroring the look-up-table spirit of
# qm9/bond_analyze.py (margins are deliberately loose for display only).
RADII = {"H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57}
MAX_VALENCE = {"H": 1, "C": 4, "N": 3, "O": 2, "F": 1}


def read_xyz(path):
    with open(path) as f:
        lines = [ln.rstrip("\n") for ln in f]
    n = int(lines[0].strip())
    atoms = []
    for ln in lines[1:]:
        parts = ln.split()
        if len(parts) != 4:
            continue
        sym, x, y, z = parts[0], *map(float, parts[1:4])
        atoms.append((sym, x, y, z))
    if len(atoms) != n:
        raise ValueError(f"{path}: header says {n} atoms, parsed {len(atoms)}")
    bad = {a[0] for a in atoms} - ALLOWED
    if bad:
        raise ValueError(f"{path}: unexpected atom types {bad}")
    return atoms


def formula(atoms):
    counts = {}
    for sym, *_ in atoms:
        counts[sym] = counts.get(sym, 0) + 1
    out = []
    for sym in ORDER:
        if sym in counts:
            out.append(sym + (str(counts[sym]) if counts[sym] > 1 else ""))
    return "".join(out)


def bonds(atoms):
    """Return bond list, and per-atom degree, using covalent radii + 0.45 A slack."""
    bs = []
    deg = [0] * len(atoms)
    for i in range(len(atoms)):
        for j in range(i + 1, len(atoms)):
            si, xi, yi, zi = atoms[i]
            sj, xj, yj, zj = atoms[j]
            d = math.dist((xi, yi, zi), (xj, yj, zj))
            cutoff = RADII[si] + RADII[sj] + 0.45
            if d < cutoff:
                bs.append((i, j, d))
                deg[i] += 1
                deg[j] += 1
    return bs, deg


def connected(n, bs):
    if n == 0:
        return False
    adj = {i: set() for i in range(n)}
    for i, j, _ in bs:
        adj[i].add(j)
        adj[j].add(i)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == n


mols = []
errors = []
for name in sorted(os.listdir(MOL_DIR)):
    if not name.endswith(".txt"):
        continue
    path = os.path.join(MOL_DIR, name)
    try:
        atoms = read_xyz(path)
    except Exception as e:  # noqa: BLE001
        errors.append(str(e))
        continue
    bs, deg = bonds(atoms)
    overfull = sum(1 for k, (sym, *_) in enumerate(atoms) if deg[k] > MAX_VALENCE[sym])
    isolated = sum(1 for d in deg if d == 0)
    xyz_text = f"{len(atoms)}\n{name}\n" + "\n".join(
        f"{s} {x:.6f} {y:.6f} {z:.6f}" for s, x, y, z in atoms
    )
    mols.append(
        {
            "name": name[:-4],
            "stable_set": name.startswith("molecule_stable"),
            "n_atoms": len(atoms),
            "n_heavy": sum(1 for a in atoms if a[0] != "H"),
            "formula": formula(atoms),
            "n_bonds": len(bs),
            "connected": connected(len(atoms), bs),
            "isolated_atoms": isolated,
            "overfull_atoms": overfull,
            "xyz": xyz_text,
        }
    )

with open(OUT, "w") as f:
    json.dump(mols, f, indent=1)

n_ok = sum(1 for m in mols if m["connected"] and not m["overfull_atoms"])
print(f"parsed {len(mols)} molecules, {len(errors)} errors")
for e in errors:
    print("  ERR", e)
print(f"clean (connected, no over-valent atoms): {n_ok}")
print(f"{'name':24} {'formula':12} {'atoms':>5} {'bonds':>5}  conn  iso  overfull")
for m in mols:
    print(
        f"{m['name']:24} {m['formula']:12} {m['n_atoms']:5} {m['n_bonds']:5} "
        f"{str(m['connected']):>5} {m['isolated_atoms']:4} {m['overfull_atoms']:9}"
    )
