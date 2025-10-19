import json
import math
from collections import defaultdict

def compute_prereq_depths(subtopics):
    """
    Compute depth (longest chain) for each subtopic using DFS.
    Returns dict: id -> depth (0 for no prereqs).
    """
    graph = {st["id"]: st.get("prerequisites", []) for st in subtopics}
    depths = {}

    def dfs(node, visited):
        if node in depths:
            return depths[node]
        if node in visited:
            # cycle protection: treat cycle nodes as depth 0
            depths[node] = 0
            return 0
        visited.add(node)
        prereqs = graph.get(node, [])
        if not prereqs:
            depths[node] = 0
        else:
            depths[node] = 1 + max(dfs(p, visited) for p in prereqs)
        visited.remove(node)
        return depths[node]

    for st in subtopics:
        dfs(st["id"], set())

    return depths

def compute_subtopic_weights_penalize_depth(
    data,
    alpha=0.5,
    beta=0.3,
    gamma=0.2,
    lambda_depth=0.12,
    epsilon=1e-6
):
    """
    Compute subtopic weights using:
      density = pyqs / (hours + eps)
      time_share = hours / total_hours
      difficulty = log(1 + hours)
      raw = alpha*density + beta*time_share + gamma*difficulty
      adjusted = raw * exp(-lambda_depth * depth)
      normalized to sum=1 per subject
    Adds "computed_weight" to each subtopic and "computed_importance" to subject.
    """
    for subject in data.get("subjects", []):
        subtopics = subject.get("subtopics", [])
        if not subtopics:
            continue

        depth_map = compute_prereq_depths(subtopics)
        total_hours = sum(st.get("hours_required", 0.0) for st in subtopics if st.get("hours_required", 0.0) > 0)
        if total_hours <= 0:
            # fallback: equal weights
            n = len(subtopics)
            for st in subtopics:
                st["computed_weight"] = round(1.0 / n, 6)
            subject["computed_importance"] = 0.0
            continue

        raw_list = []
        for st in subtopics:
            h = float(st.get("hours_required", 0.0))
            p = float(st.get("pyqs", 0.0))
            d = int(depth_map.get(st["id"], 0))

            density = p / (h + epsilon)
            time_share = h / total_hours
            difficulty = math.log(1.0 + h)

            raw = alpha * density + beta * time_share + gamma * difficulty
            # penalize deeper dependencies using exponential decay
            adjusted = raw * math.exp(-lambda_depth * d)

            raw_list.append({
                "id": st["id"],
                "raw": raw,
                "adjusted": adjusted,
                "depth": d,
                "hours": h,
                "pyqs": p
            })

        total_adjusted = sum(x["adjusted"] for x in raw_list) or 1.0
        # attach computed weights back to subtopics
        for r in raw_list:
            weight = r["adjusted"] / total_adjusted
            # keep a few extra fields for transparency
            st = next(filter(lambda s: s["id"] == r["id"], subtopics))
            st["computed_weight"] = round(weight, 6)
            st["__debug_raw"] = round(r["raw"], 6)
            st["__debug_adjusted"] = round(r["adjusted"], 6)
            st["__debug_depth"] = r["depth"]

        # subject-level metric (mean of adjusted before normalization)
        subject["computed_importance"] = round(sum(r["adjusted"] for r in raw_list) / len(raw_list), 6)

    return data


# ------------------------- testing 
if __name__ == "__main__":
    INPUT = "syllabus.json"        
    OUTPUT = "syllabus_weighted_penalized.json"

    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = compute_subtopic_weights_penalize_depth(
        data,
        alpha=0.5,
        beta=0.3,
        gamma=0.2,
        lambda_depth=0.12   #tune here <------------------
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    print(f" Weights computed (saved to {OUTPUT}).")
    print("Tweak lambda_depth (0.08..0.18) to change how strongly deep chains are penalized.")
