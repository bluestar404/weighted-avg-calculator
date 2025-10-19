import json
import math
from collections import defaultdict

def compute_prereq_depths(subtopics):
    """
    Compute the prerequisite depth (dependency level) for each subtopic.
    Depth = longest chain from root to node.
    """
    graph = {st["id"]: st.get("prerequisites", []) for st in subtopics}
    depths = {}

    def dfs(node):
        if node in depths:
            return depths[node]
        prereqs = graph.get(node, [])
        if not prereqs:
            depths[node] = 0
        else:
            depths[node] = 1 + max(dfs(p) for p in prereqs)
        return depths[node]

    for st in subtopics:
        dfs(st["id"])

    return depths


def compute_subtopic_weights(data, alpha=0.5, beta=0.3, gamma=0.2, epsilon=1e-6):
    """
    Compute subtopic weights using the composite formula:
      raw_i = α*density + β*time_share + γ*difficulty
      adjusted_i = raw_i * (1 + 0.1*depth)
      normalized across all subtopics in a subject
    """
    for subject in data.get("subjects", []):
        subtopics = subject.get("subtopics", [])
        if not subtopics:
            continue

        
        depth_map = compute_prereq_depths(subtopics)

        total_hours = sum(st["hours_required"] for st in subtopics if st["hours_required"] > 0)
        if total_hours == 0:
            continue

        raw_weights = []
        for st in subtopics:
            h = st.get("hours_required", 0.0)
            p = st.get("pyqs", 0.0)
            d = depth_map.get(st["id"], 0)

            density = p / (h + epsilon)
            time_share = h / total_hours
            difficulty = math.log(1 + h)

            raw = alpha * density + beta * time_share + gamma * difficulty
            adjusted = raw * (1 + 0.1 * d)
            raw_weights.append(adjusted)

        # Normalize
        total_raw = sum(raw_weights)
        for st, raw in zip(subtopics, raw_weights):
            st["computed_weight"] = round(raw / total_raw, 4) if total_raw > 0 else 0.0

        
        subject["computed_importance"] = round(sum(raw_weights) / len(raw_weights), 4)

    return data



# -------------------------------- testing code
if __name__ == "__main__":
    input_file = "algorithms.json"
    output_file = "algorithms_weighted.json"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated_data = compute_subtopic_weights(
        data,
        alpha=0.5,  # PYQ density weight
        beta=0.3,   # time share weight
        gamma=0.2   # difficulty weight
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2)

    print(f"weights saved to '{output_file}'")
