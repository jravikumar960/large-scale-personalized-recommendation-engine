import os
import sys
try:
    import tritonclient.http as httpclient
except Exception as exc:
    print("tritonclient not installed:", exc)
    sys.exit(0)
client = httpclient.InferenceServerClient(url=os.getenv("TRITON_URL", "localhost:8000"))
print("server live:", client.is_server_live())
