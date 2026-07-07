# Geo Dataset Component Matching Report

## Method

- Generated at: `2026-06-23T22:19:28+00:00`
- Input: `/home/ioolliver/Workspace/ast-driven-data-augmentation-algorithm/data/geo_dataset/geo_dataset_augmented_only.json`
- Rows analyzed: `980`
- SQL dialect: `postgres`
- Score formula: `changed_component_count / component_total`

`component_matching_score` is the share of normalized SQL AST component slots that changed between the original and augmented SQL.

## Overall Statistics

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 980 | 0.000000 | 0.533333 | 0.113215 | 0.096464 | 0.086501 | 0.058824 | 0.146136 | 0.226299 | 0.307692 |

## Unchanged SQL

- Rows with no component changes: `99`

## Statistics By Level

### Facíl

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 245 | 0.000000 | 0.294118 | 0.082909 | 0.071429 | 0.066214 | 0.047619 | 0.117647 | 0.166667 | 0.230769 |

### Médio

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 245 | 0.000000 | 0.256410 | 0.095938 | 0.092593 | 0.054040 | 0.058824 | 0.130435 | 0.166667 | 0.181520 |

### Difícil

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 245 | 0.000000 | 0.448980 | 0.124436 | 0.103448 | 0.078073 | 0.071429 | 0.156250 | 0.208955 | 0.240861 |

### Muito Difícil

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 245 | 0.000000 | 0.533333 | 0.149576 | 0.107143 | 0.117747 | 0.068182 | 0.235294 | 0.350000 | 0.363636 |

## Score Band Distribution

| Score Band | Rows |
| --- | ---: |
| [0.0, 0.1) | 495 |
| [0.1, 0.2) | 351 |
| [0.2, 0.3) | 80 |
| [0.3, 0.4) | 48 |
| [0.4, 0.5) | 4 |
| [0.5, 0.6) | 2 |
| [0.6, 0.7) | 0 |
| [0.7, 0.8) | 0 |
| [0.8, 0.9) | 0 |
| [0.9, 1.0] | 0 |

## Most Frequently Changed Component Families

| Component Family | Changed Count |
| --- | ---: |
| predicate | 1408 |
| spatial_function | 1150 |
| aggregation | 556 |
| select | 540 |
| group_by | 12 |
| table | 5 |

## Lowest Component Scores

| Row Index | Level | Components | Changed | Score |
| ---: | --- | ---: | ---: | ---: |
| 3 | Facíl | 18 | 0 | 0.000000 |
| 4 | Facíl | 14 | 0 | 0.000000 |
| 9 | Facíl | 14 | 0 | 0.000000 |
| 15 | Facíl | 14 | 0 | 0.000000 |
| 16 | Facíl | 13 | 0 | 0.000000 |
| 19 | Facíl | 14 | 0 | 0.000000 |
| 105 | Muito Difícil | 23 | 0 | 0.000000 |
| 107 | Muito Difícil | 21 | 0 | 0.000000 |
| 112 | Muito Difícil | 16 | 0 | 0.000000 |
| 114 | Muito Difícil | 27 | 0 | 0.000000 |

## Highest Component Scores

| Row Index | Level | Components | Changed | Score |
| ---: | --- | ---: | ---: | ---: |
| 816 | Muito Difícil | 15 | 8 | 0.533333 |
| 815 | Muito Difícil | 12 | 6 | 0.500000 |
| 931 | Difícil | 49 | 22 | 0.448980 |
| 939 | Difícil | 52 | 22 | 0.423077 |
| 935 | Difícil | 52 | 22 | 0.423077 |
| 934 | Difícil | 52 | 22 | 0.423077 |
| 944 | Difícil | 61 | 24 | 0.393443 |
| 941 | Difícil | 58 | 22 | 0.379310 |
| 975 | Muito Difícil | 8 | 3 | 0.375000 |
| 972 | Muito Difícil | 8 | 3 | 0.375000 |
