from src.cf_svd import SvdRetriever
r=SvdRetriever("models/cf_svd")
print("loaded", len(r.user_ids), len(r.item_ids), r.user_factors.shape, r.item_factors.shape)
print("sample user", r.user_ids[0], "sample item", r.item_ids[0])
