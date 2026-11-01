import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import numpy as np
import tensorflow as tf
from src.deep_ranker import load_deep_ranker
keras_model = load_deep_ranker("models/deep_ranker/deep_ranker.keras")
saved = tf.saved_model.load("triton/model_repository/deep_ranker/1/model.savedmodel")
X = np.array([[4.0, 3.5, 2.0, 1.0], [1.0, 1.0, 1.0, 0.0], [0.0, 0.0, 0.0, 0.0]], dtype="float32")
keras_pred = keras_model.predict(X, verbose=0).reshape(-1)
saved_output = saved(tf.constant(X))
saved_pred = saved_output["score"].numpy().reshape(-1)
print("keras", keras_pred.tolist())
print("savedmodel", saved_pred.tolist())
print("max_abs_diff", float(np.max(np.abs(keras_pred - saved_pred))))
assert np.allclose(keras_pred, saved_pred, atol=1e-5)
assert np.all(np.isfinite(saved_pred))
print("artifact validation passed")
