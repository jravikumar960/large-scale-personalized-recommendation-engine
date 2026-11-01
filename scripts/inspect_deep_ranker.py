import os
os.environ.setdefault("TF_USE_LEGACY_KERAS","1")
import numpy as np
from src.deep_ranker import load_deep_ranker
m = load_deep_ranker("models/deep_ranker/deep_ranker.keras")
print("inputs", m.input_shape)
print("outputs", m.output_shape)
X = np.array([[4.0,3.5,2.0,1.0],[1.0,1.0,1.0,0.0]], dtype="float32")
print("preds", m.predict(X, verbose=0).reshape(-1))
