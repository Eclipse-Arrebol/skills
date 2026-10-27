"""User-specified teaching graph. All weights are illustrative, not measurements."""
VERTICES = tuple("ABCDEF")
ORDER = tuple("ADBCEF")
RANK = {v: i for i, v in enumerate(ORDER)}
EDGES = {("A", "B"): 2, ("B", "C"): 3, ("C", "D"): 2,
         ("D", "E"): 3, ("E", "F"): 2, ("A", "F"): 4,
         ("B", "E"): 5, ("C", "F"): 6}
UPDATED_EDGES = dict(EDGES, **{})
UPDATED_EDGES[("A", "B")] = 9
# Graph occupies the left 55%; coordinates remain fixed through every elimination.
POSITIONS = {"A": (-6.1, 0.7), "B": (-4.75, 2.05), "C": (-2.05, 2.05),
             "D": (-0.7, 0.7), "E": (-2.05, -1.1), "F": (-4.75, -1.1)}
TREE_POSITIONS = {"F": (4.15, -0.12), "E": (4.15, -0.82), "C": (4.15, -1.52),
                  "B": (3.05, -2.22), "D": (5.45, -2.22), "A": (3.05, -2.92)}
EXPECTED_PARENT = {"A": "B", "D": "C", "B": "C", "C": "E", "E": "F", "F": None}


def edge(u, v):
    return tuple(sorted((u, v)))
