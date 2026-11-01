from pathlib import Path
import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import numpy as np
import tensorflow as tf
from src.deep_ranker import load_deep_ranker

def test_triton_repository_files_exist():
    root = Path("triton/model_repository/deep_ranker")
    assert (root / "config.pbtxt").is_file()
    assert (root / "1" / "model.savedmodel" / "saved_model.pb").is_file()

def test_saved_model_matches_keras():
    keras_model = load_deep_ranker("models/deep_ranker/deep_ranker.keras")
    saved_model = tf.saved_model.load("triton/model_repository/deep_ranker/1/model.savedmodel")
    X = np.array([[4.0, 3.5, 2.0, 1.0], [1.0, 1.0, 1.0, 0.0]], dtype="float32")
    expected = keras_model.predict(X, verbose=0).reshape(-1)
    actual = saved_model(tf.constant(X))["score"].numpy().reshape(-1)
    assert np.allclose(expected, actual, atol=1e-5)
    assert np.all(np.isfinite(actual))
