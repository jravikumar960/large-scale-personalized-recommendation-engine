import json
m=json.load(open("models/metrics.json"))
m["cf_pop_deep_validation"] = {"candidate_universe": "cf_svd item vocabulary (40420 items)", "users": 100, "cf_svd": {"recall@10": 0.04552393948462466, "recall@20": 0.06375943739883846, "ndcg@10": 0.03858012823104144, "hit_rate@10": 0.16, "precision@10": 0.023}, "popularity": {"recall@10": 0.015860585487986904, "recall@20": 0.022976864557754342, "ndcg@10": 0.015345745371002705, "hit_rate@10": 0.07, "precision@10": 0.01}, "deep_ranker": {"recall@10": 0.009077639751552796, "recall@20": 0.009347910021823065, "ndcg@10": 0.010772340913090872, "hit_rate@10": 0.05, "precision@10": 0.005}}
open("models/metrics.json","w").write(json.dumps(m, indent=2))
print("done")
