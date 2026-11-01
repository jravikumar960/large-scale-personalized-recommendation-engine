import os
os.environ.setdefault("TF_USE_LEGACY_KERAS","1")
import numpy as np
import tensorflow as tf
from src.deep_ranker import load_deep_ranker
model = load_deep_ranker("models/deep_ranker/deep_ranker.keras")
class ServingModule(tf.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
    @tf.function(input_signature=[tf.TensorSpec(shape=[None, 4], dtype=tf.float32, name="features")])
    def __call__(self, features):
        return {"score": self.model(features, training=False)}
module = ServingModule(model)
export_dir = "triton/model_repository/deep_ranker/1/model.savedmodel"
tf.saved_model.save(module, export_dir, signatures={"serving_default": module.__call__})
print("saved", export_dir)
