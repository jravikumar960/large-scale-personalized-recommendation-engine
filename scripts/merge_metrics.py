import json
m = json.load(open("models/metrics.json"))
r = json.load(open("models/ranking_metrics.json"))
m["ranking_comparison"] = r["ranking_comparison"]
m["ranking_evaluation_protocol"] = r["evaluation_protocol"]
open("models/metrics.json", "w").write(json.dumps(m, indent=2))
print("done")
