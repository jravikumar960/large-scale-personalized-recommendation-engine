import importlib.util
for m in ["onnx", "onnxruntime", "tf2onnx", "tritonclient", "tensorflow"]:
    print(m, bool(importlib.util.find_spec(m)))
