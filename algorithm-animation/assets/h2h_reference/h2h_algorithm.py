"""Exact fill-based H2H teaching model and dependency-driven weight maintenance.

On screen SC(v) is the saved incident map to remaining neighbors, stored in
upward[v]. Neighbor-pair x-v-y proposals are called fill_candidates separately.
Losing proposals remain in the support DAG for weight increases. No pruning.
"""
from collections import defaultdict
from copy import deepcopy
from heapq import heappop, heappush
from itertools import combinations
import json
from pathlib import Path
from graph_data import *

INF = float("inf")


def distances(edges, vertices=VERTICES):
    adj = {v: {} for v in vertices}
    for (u, v), w in edges.items():
        if u in adj and v in adj:
            adj[u][v] = adj[v][u] = w
    out = {}
    for source in vertices:
        ds = {v: INF for v in vertices}
        ds[source] = 0
        queue = [(0, source)]
        while queue:
            d, v = heappop(queue)
            if d != ds[v]:
                continue
            for u, w in adj[v].items():
                if d + w < ds[u]:
                    ds[u] = d + w
                    heappush(queue, (ds[u], u))
        out[source] = ds
    return out


def build(edges):
    work = dict(edges)
    alive = set(VERTICES)
    steps, upward, parent, bags, support = [], {}, {}, {}, defaultdict(list)
    all_weights = {}
    for v in ORDER:
        degree = {x: sum(edge(x, y) in work for y in alive if y != x) for x in alive}
        assert v == min(alive, key=lambda x: (degree[x], x))
        neighbors = sorted((u for u in alive if u != v and edge(u, v) in work), key=RANK.get)
        upward[v] = {u: work[edge(v, u)] for u in neighbors}
        bags[v] = [v] + neighbors
        parent[v] = neighbors[0] if neighbors else None
        before = dict(work)
        candidates = []
        for x, y in combinations(neighbors, 2):
            k = edge(x, y)
            val = upward[v][x] + upward[v][y]
            old = work.get(k, INF)
            support[k].append(v)
            kind = "add" if old == INF else "update" if val < old else "keep"
            work[k] = min(old, val)
            candidates.append(dict(x=x, y=y, via=v, left=upward[v][x], right=upward[v][y],
                                   candidate=val, old=None if old == INF else old,
                                   value=work[k], action=kind))
        for u in neighbors:
            all_weights[edge(v, u)] = upward[v][u]
        work = {k: w for k, w in work.items() if v not in k}
        alive.remove(v)
        steps.append(dict(v=v, degree=degree, neighbors=neighbors, bag=bags[v],
                          parent=parent[v], candidates=candidates, before=before,
                          after=dict(work), alive=sorted(alive)))
    assert parent == EXPECTED_PARENT
    model = dict(steps=steps, upward=upward, bags=bags, parent=parent,
                 weights=all_weights, supports=dict(support), base=dict(edges))
    model["fill_candidates"] = {s["v"]: [dict(x=c["x"],y=c["y"],via=c["via"],
            left=c["left"],right=c["right"],candidate=c["candidate"]) for c in s["candidates"]] for s in steps}
    model["labels"] = labels_from_shortcuts(model)
    return model


def ancestors(v, parent, self_included=False):
    out = [v] if self_included else []
    while parent[v] is not None:
        v = parent[v]
        out.append(v)
    return out


def pair_label(labels, u, a):
    if u == a:
        return 0
    return labels[u][a] if a in labels.get(u, {}) else labels[a][u]


def label_terms(model, labels, v, a):
    return {u: model["weights"][edge(v, u)] + pair_label(labels, u, a)
            for u in model["upward"][v]}


def labels_from_shortcuts(model):
    labels = {}
    for v in reversed(ORDER):
        labels[v] = {v: 0}
        for a in ancestors(v, model["parent"]):
            labels[v][a] = min(label_terms(model, labels, v, a).values())
    return labels


def query(model, s, t):
    sp = ancestors(s, model["parent"], True)
    tp = ancestors(t, model["parent"], True)
    lca = next(v for v in sp if v in tp)
    terms = {h: model["labels"][s][h] + model["labels"][t][h] for h in model["bags"][lca]}
    return dict(lca=lca, hubs=model["bags"][lca], terms=terms, distance=min(terms.values()))


def dynamic_update(old, base):
    """Recompute only notified dependencies; propagate only changed values."""
    new = deepcopy(old)
    new["base"] = dict(base)
    reverse = defaultdict(set)
    for target, witnesses in new["supports"].items():
        x, y = target
        for z in witnesses:
            reverse[edge(z, x)].add(target)
            reverse[edge(z, y)].add(target)
    dirty = {k for k in base if base[k] != old["base"].get(k, INF)}
    events = []
    changed = set()
    while dirty:
        k = min(dirty, key=lambda k: min(RANK[v] for v in k))
        dirty.remove(k)
        x, y = k
        terms = {"original": base.get(k, INF)}
        for z in new["supports"].get(k, []):
            terms[z] = new["weights"][edge(z, x)] + new["weights"][edge(z, y)]
        value = min(terms.values())
        before = new["weights"][k]
        new["weights"][k] = value
        events.append(dict(edge=k, before=before, after=value, changed=before != value,
                           terms={k: v for k, v in terms.items() if v != INF}))
        if value != before:
            changed.add(k)
            dirty.update(reverse[k])
    # Historical elimination steps stay immutable. Refresh fill proposals
    # and upward edge values, including candidates that did not win the minimum.
    for v in ORDER:
        for u in new["upward"][v]:
            new["upward"][v][u] = new["weights"][edge(v,u)]
        for record in new["fill_candidates"][v]:
            record["left"] = new["weights"][edge(v,record["x"])]
            record["right"] = new["weights"][edge(v,record["y"])]
            record["candidate"] = record["left"] + record["right"]
    # Construct exact reverse label dependencies, including non-winning terms.
    edge_readers, label_readers = defaultdict(set), defaultdict(set)
    for v in ORDER:
        for a in ancestors(v, new["parent"]):
            dest = (v, a)
            for u in new["upward"][v]:
                edge_readers[edge(v, u)].add(dest)
                if u != a:
                    ref = (u, a) if a in old["labels"][u] else (a, u)
                    label_readers[ref].add(dest)
    pending = set().union(*(edge_readers[k] for k in changed))
    label_events = []
    while pending:
        v, a = max(pending, key=lambda p: (RANK[p[0]], RANK[p[1]]))
        pending.remove((v, a))
        before = new["labels"][v][a]
        terms = label_terms(new, new["labels"], v, a)
        value = min(terms.values())
        new["labels"][v][a] = value
        label_events.append(dict(v=v, ancestor=a, before=before, after=value,
                                 changed=value != before, terms=terms))
        if value != before:
            pending.update(label_readers[(v, a)])
    return new, events, label_events


def jsonable(value):
    if isinstance(value, dict):
        return {(":".join(k) if isinstance(k, tuple) else str(k)): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return value


def audit():
    old = build(EDGES)
    rebuilt = build(UPDATED_EDGES)
    new, se, le = dynamic_update(old, UPDATED_EDGES)
    checks = 0
    for model, edges in [(old, EDGES), (rebuilt, UPDATED_EDGES)]:
        truth = distances(edges)
        for step in model["steps"]:
            remain = step["alive"]
            local = distances(step["after"], remain)
            for s in remain:
                for t in remain:
                    assert local[s][t] == truth[s][t]
                    checks += 1
        for v, labs in model["labels"].items():
            for a, d in labs.items():
                assert d == truth[v][a]
                checks += 1
        for s in VERTICES:
            for t in VERTICES:
                assert query(model, s, t)["distance"] == truth[s][t]
                checks += 1
        for x in VERTICES:
            containing = {v for v in VERTICES if x in model["bags"][v]}
            for v in containing:
                if v != x:
                    assert model["parent"][v] in containing
                    checks += 1
    assert new["weights"] == rebuilt["weights"]
    assert new["labels"] == rebuilt["labels"]
    assert new["fill_candidates"] == rebuilt["fill_candidates"]
    assert new["upward"] == rebuilt["upward"]
    assert old["bags"] == rebuilt["bags"] and old["parent"] == rebuilt["parent"]
    assert old["labels"]["A"] == {"A": 0, "B": 2, "C": 5, "E": 6, "F": 4}
    assert new["labels"]["A"] == {"A": 0, "B": 9, "C": 10, "E": 6, "F": 4}
    assert query(old, "A", "D")["distance"] == 7
    assert query(new, "A", "D")["distance"] == 9
    report = dict(checks=checks + 9, before=old, after=new, rebuilt=rebuilt,
                  shortcut_events=se, label_events=le,
                  query_before=query(old, "A", "D"), query_after=query(new, "A", "D"))
    Path("model_audit.json").write_text(json.dumps(jsonable(report), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(jsonable(dict(checks=checks + 9, shortcut_events=se, label_events=le,
                                   labels_A_before=old["labels"]["A"], labels_A_after=new["labels"]["A"],
                                   query_before=query(old,"A","D"), query_after=query(new,"A","D"))), ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    audit()
