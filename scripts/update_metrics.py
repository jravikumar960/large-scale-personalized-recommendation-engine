import json
p = "models/metrics.json"
m = json.loads(open(p).read())
m["model"] = "TwoStageBaseline (gradient boosting ranker)"
m["evaluation_protocol"] = "held-out chronological test; users with >=1 relevant item; top-10; relevant = rating>=4"
m["users_evaluated"] = m.get("users_evaluated", 868)
m["sample_note"] = "Metrics from 868 sampled eligible users"
open(p, "w").write(json.dumps(m, indent=2))
print(json.dumps(m, indent=2))
