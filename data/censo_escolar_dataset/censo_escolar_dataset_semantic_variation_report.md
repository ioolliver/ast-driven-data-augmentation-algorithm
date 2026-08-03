# Censo Escolar Dataset Semantic Variation Report

## Method

- Generated at: `2026-07-29T16:44:08+00:00`
- Input: `/home/ioolliver/Workspace/ast-driven-data-augmentation-algorithm/data/censo_escolar_dataset/censo_escolar_dataset_augmented_only.json`
- Rows analyzed: `107`
- Embedding model: `jinaai/jina-embeddings-v3`
- Embedding task: `text-matching`
- Score formula: `clip(1 - cosine_similarity(original, changed), 0, 1)`
- Model license: `CC BY-NC 4.0` (non-commercial use).

A score of `0` represents no detected semantic variation in embedding space; a score of `1` represents maximum variation under the clipped cosine metric.

## Overall Statistics

| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sql | 107 | 0.001542 | 0.155787 | 0.055982 | 0.050897 | 0.037435 | 0.024579 | 0.071499 | 0.115996 | 0.130058 |
| Question | 107 | 0.000000 | 0.628506 | 0.267454 | 0.262271 | 0.141846 | 0.170239 | 0.350450 | 0.476381 | 0.513259 |
| Combined | 107 | 0.000771 | 0.367276 | 0.161718 | 0.154982 | 0.084065 | 0.101667 | 0.212380 | 0.281334 | 0.304467 |

## Unchanged Text

| Comparison | Exact Unchanged Rows |
| --- | ---: |
| SQL | 0 |
| Question | 5 |

## Statistics By Level

### Média

| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sql | 29 | 0.012758 | 0.123902 | 0.048518 | 0.047129 | 0.024730 | 0.032823 | 0.063196 | 0.074440 | 0.084894 |
| Question | 29 | 0.000000 | 0.475342 | 0.241069 | 0.229697 | 0.106351 | 0.180382 | 0.307793 | 0.345627 | 0.390944 |
| Combined | 29 | 0.028384 | 0.281140 | 0.144793 | 0.137232 | 0.060670 | 0.110461 | 0.183952 | 0.210244 | 0.245545 |

### Fácil

| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sql | 46 | 0.003713 | 0.155787 | 0.076575 | 0.065546 | 0.040547 | 0.051056 | 0.106755 | 0.134684 | 0.142257 |
| Question | 46 | 0.000000 | 0.628506 | 0.347534 | 0.348223 | 0.142758 | 0.263660 | 0.464657 | 0.519565 | 0.553571 |
| Combined | 46 | 0.001857 | 0.367276 | 0.212054 | 0.216636 | 0.083578 | 0.163870 | 0.279236 | 0.308393 | 0.333573 |

### Difícil

| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sql | 8 | 0.001542 | 0.055206 | 0.023569 | 0.021752 | 0.017553 | 0.012065 | 0.030028 | 0.048175 | 0.051691 |
| Question | 8 | 0.000000 | 0.279709 | 0.146945 | 0.172888 | 0.123721 | 0.000000 | 0.273083 | 0.279174 | 0.279441 |
| Combined | 8 | 0.000771 | 0.162053 | 0.085257 | 0.106309 | 0.066905 | 0.006033 | 0.146979 | 0.155258 | 0.158656 |

### Muito Difícil

| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sql | 24 | 0.008912 | 0.091659 | 0.036337 | 0.023793 | 0.025275 | 0.016845 | 0.062019 | 0.073511 | 0.074456 |
| Question | 24 | 0.038542 | 0.393990 | 0.186021 | 0.174586 | 0.085248 | 0.139956 | 0.219298 | 0.312759 | 0.348799 |
| Combined | 24 | 0.029757 | 0.212401 | 0.111179 | 0.101667 | 0.049734 | 0.078516 | 0.141207 | 0.191354 | 0.211749 |

## Score Band Distribution

| Score Band | SQL | Question | Combined |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 91 | 10 | 26 |
| [0.1, 0.2) | 16 | 28 | 45 |
| [0.2, 0.3) | 0 | 25 | 29 |
| [0.3, 0.4) | 0 | 26 | 7 |
| [0.4, 0.5) | 0 | 10 | 0 |
| [0.5, 0.6) | 0 | 6 | 0 |
| [0.6, 0.7) | 0 | 2 | 0 |
| [0.7, 0.8) | 0 | 0 | 0 |
| [0.8, 0.9) | 0 | 0 | 0 |
| [0.9, 1.0] | 0 | 0 | 0 |

## Lowest Combined Scores

| Row Index | Level | SQL Score | Question Score | Combined Score |
| ---: | --- | ---: | ---: | ---: |
| 103 | Difícil | 0.001542 | 0.000000 | 0.000771 |
| 96 | Difícil | 0.003103 | 0.000000 | 0.001551 |
| 1 | Fácil | 0.003713 | 0.000000 | 0.001857 |
| 12 | Difícil | 0.015052 | 0.000000 | 0.007526 |
| 2 | Média | 0.056767 | 0.000000 | 0.028384 |
| 25 | Média | 0.012758 | 0.044498 | 0.028628 |
| 15 | Muito Difícil | 0.020972 | 0.038542 | 0.029757 |
| 17 | Média | 0.013292 | 0.067359 | 0.040325 |
| 39 | Muito Difícil | 0.019558 | 0.062929 | 0.041244 |
| 106 | Muito Difícil | 0.022643 | 0.076208 | 0.049425 |

## Highest Combined Scores

| Row Index | Level | SQL Score | Question Score | Combined Score |
| ---: | --- | ---: | ---: | ---: |
| 67 | Fácil | 0.106047 | 0.628506 | 0.367276 |
| 65 | Fácil | 0.155787 | 0.551995 | 0.353891 |
| 70 | Fácil | 0.064131 | 0.607832 | 0.335981 |
| 82 | Fácil | 0.138998 | 0.513701 | 0.326349 |
| 64 | Fácil | 0.070405 | 0.554096 | 0.312251 |
| 68 | Fácil | 0.118065 | 0.491005 | 0.304535 |
| 81 | Fácil | 0.142867 | 0.465751 | 0.304309 |
| 22 | Fácil | 0.114616 | 0.482784 | 0.298700 |
| 53 | Fácil | 0.155774 | 0.421310 | 0.288542 |
| 60 | Fácil | 0.062679 | 0.512227 | 0.287453 |

## Limitations

This score is an embedding-based heuristic for variation strength. It does not prove SQL behavioral equivalence or difference: a change to an operator, literal, join, or spatial predicate can be logically decisive even when the embedding distance is small.
