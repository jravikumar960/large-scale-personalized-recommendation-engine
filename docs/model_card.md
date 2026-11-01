Model card
Primary retrieval: CF SVD, k=38, rating>=4 implicit feedback.
Ranker: Keras deep ranker with four features.
Fallbacks: popularity and gradient boosting.
Known issue: two-tower Recall@10 = 0.0.
