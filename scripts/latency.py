import time, statistics, urllib.request
times=[]
for _ in range(20):
    t=time.perf_counter()
    urllib.request.urlopen("http://127.0.0.1:8000/recommendations/1?k=10").read()
    times.append((time.perf_counter()-t)*1000)
print("n", len(times))
print("median_ms", round(statistics.median(times),2))
print("p95_ms", round(sorted(times)[int(0.95*len(times))-1],2))
print("min_ms", round(min(times),2), "max_ms", round(max(times),2))
