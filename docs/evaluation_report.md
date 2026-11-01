Evaluation Report
Baseline TwoStageBaseline on MovieLens 25M held-out test (sampled 868 users):
Recall@10=0.009757 NDCG@10=0.013401 HitRate@10=0.06682 Precision@10=0.009447
Two-tower retrieval (1 epoch, 100k sample) Recall@10~0.0006 on 183 users.
Compare on 50 held-out users:
Baseline Recall@10=0.0070 NDCG@10=0.0076 HitRate@10=0.08 Precision@10=0.0080
Two-tower Recall@10=0.0 NDCG@10=0.0 HitRate@10=0.0 Precision@10=0.0
Ranking comparison (100 eligible held-out users, candidate_count=200):
popularity: R@10=0.01928 N@10=0.028221 HR@10=0.15 P@10=0.027
gradient_boosting: R@10=0.010098 N@10=0.015452 HR@10=0.07 P@10=0.012
deep_ranker: R@10=0.016916 N@10=0.030534 HR@10=0.15 P@10=0.027
Deep ranker improved NDCG vs gradient boosting but not clearly overall; popularity strongest on this candidate set.
End-to-end pipeline on 100 validation users (CF SVD retrieval top-200 then ranker):
CF SVD + deep ranker: R@10=0.017556 N@10=0.017842 HR@10=0.10 P@10=0.013
CF SVD + gradient boosting: R@10=0.022089 N@10=0.016619 HR@10=0.08 P@10=0.010
CF SVD + popularity ranking: R@10=0.035422 N@10=0.021771 HR@10=0.10 P@10=0.012
CF SVD retrieval alone remains strongest: R@10=0.05095 on 500 validation users.
Pairwise BPR experiment on 100 validation users, 100k sampled pairs, 3 epochs: Recall@10=0.014046, NDCG@10=0.007532, HitRate@10=0.04, Precision@10=0.004; did not improve popularity ranking (0.035422 Recall@10).
Root cause: current rankers use pointwise rating regression on weak features and do not improve CF SVD retrieval order.
Note: the 500-user retrieval, 100-user ranking, and 50-user two-tower evaluations use different protocols and sample sizes and are not directly comparable as one experiment.
Ranking experiment with CF score feature (100 validation users): CF retrieval R@10=0.045048 N@10=0.037729; CF+deep ranker with CF score R@10=0.043682 N@10=0.040468; CF+popularity R@10=0.035422 N@10=0.021771. Deep ranker improved NDCG but not Recall; no promotion.
## Pairwise ranking experiment (100 eligible validation users, candidate_count=200)
- Training pairs: 100,000 from training data only; relevance threshold rating >= 4; seed 42.
- Candidate generation: CF SVD top-200 after seen-item exclusion.
- CF SVD retrieval alone: R@10=0.045048 N@10=0.037729 HR@10=0.15 P@10=0.022
- CF SVD + pairwise ranker: R@10=0.046181 N@10=0.037628 HR@10=0.16 P@10=0.022
- CF SVD + popularity ranking: R@10=0.035422 N@10=0.021771 HR@10=0.10 P@10=0.012
- Conclusion: pairwise objective is not a measured improvement over CF SVD retrieval; no promotion.
- Artifact: models/pairwise_ranker/pairwise_ranker.keras and config.json; production artifacts unchanged.
