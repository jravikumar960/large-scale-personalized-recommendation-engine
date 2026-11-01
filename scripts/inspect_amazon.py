import gzip, json
rev_asin=set(); rev_parent=set(); n=0
with gzip.open("data/raw/amazon/Amazon_Fashion.jsonl.gz","rt") as f:
    for line in f:
        o=json.loads(line); n+=1
        rev_asin.add(o.get("asin")); rev_parent.add(o.get("parent_asin"))
print("reviews",n,"distinct asin",len(rev_asin),"parent_asin",len(rev_parent))
meta_asin=set(); m=0
with gzip.open("data/raw/amazon/meta_AMAZON_FASHION.json.gz","rt") as f:
    for line in f:
        o=json.loads(line); m+=1
        meta_asin.add(o.get("asin"))
print("meta",m,"distinct asin",len(meta_asin))
print("overlap review asin vs meta:", len(rev_asin & meta_asin))
print("overlap review parent_asin vs meta:", len(rev_parent & meta_asin))
