import json
m=json.load(open("models/metrics.json"))
c=json.load(open("models/cf_svd_validation_metrics.json"))
m["cf_svd_validation"] = c
open("models/metrics.json","w").write(json.dumps(m, indent=2))
print("done")
