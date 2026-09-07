# Censo Escolar Dataset Component Matching Report

## Method

- Generated at: `2026-07-29T16:33:25+00:00`
- Input: `/home/ioolliver/Workspace/ast-driven-data-augmentation-algorithm/data/censo_escolar_dataset/censo_escolar_dataset_augmented_only.json`
- Rows analyzed: `107`
- SQL dialect: `bigquery`
- Score formula: `changed_component_count / component_total`

`component_matching_score` is the share of normalized SQL AST component slots that changed between the original and augmented SQL.

## Overall Statistics

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 107 | 0.000000 | 0.840000 | 0.298016 | 0.280000 | 0.164541 | 0.183036 | 0.394444 | 0.500000 | 0.613534 |

## Unchanged SQL

- Rows with no component changes: `4`

## Statistics By Level

### Média

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 29 | 0.121212 | 0.657143 | 0.254002 | 0.233333 | 0.112010 | 0.192308 | 0.280000 | 0.387455 | 0.455556 |

### Fácil

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 46 | 0.000000 | 0.840000 | 0.369904 | 0.333333 | 0.162747 | 0.278075 | 0.431350 | 0.598398 | 0.659091 |

### Difícil

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 0.000000 | 0.363636 | 0.139205 | 0.150000 | 0.125132 | 0.000000 | 0.212500 | 0.284091 | 0.323864 |

### Muito Difícil

| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 0.052632 | 0.571429 | 0.266350 | 0.225000 | 0.167040 | 0.095238 | 0.404167 | 0.500000 | 0.500000 |

## Score Band Distribution

| Score Band | Rows |
| --- | ---: |
| [0.0, 0.1) | 12 |
| [0.1, 0.2) | 17 |
| [0.2, 0.3) | 28 |
| [0.3, 0.4) | 23 |
| [0.4, 0.5) | 12 |
| [0.5, 0.6) | 9 |
| [0.6, 0.7) | 4 |
| [0.7, 0.8) | 1 |
| [0.8, 0.9) | 1 |
| [0.9, 1.0] | 0 |

## Most Frequently Changed Component Families

| Component Family | Changed Count |
| --- | ---: |
| aggregation | 280 |
| predicate | 258 |
| select | 48 |
| spatial_function | 36 |
| group_by | 6 |
| order_by | 1 |

## Lowest Component Scores

| Row Index | Level | Components | Changed | Score |
| ---: | --- | ---: | ---: | ---: |
| 1 | Fácil | 14 | 0 | 0.000000 |
| 12 | Difícil | 14 | 0 | 0.000000 |
| 96 | Difícil | 10 | 0 | 0.000000 |
| 103 | Difícil | 10 | 0 | 0.000000 |
| 16 | Muito Difícil | 19 | 1 | 0.052632 |
| 15 | Muito Difícil | 17 | 1 | 0.058824 |
| 8 | Fácil | 14 | 1 | 0.071429 |
| 51 | Muito Difícil | 21 | 2 | 0.095238 |
| 91 | Muito Difícil | 21 | 2 | 0.095238 |
| 92 | Muito Difícil | 21 | 2 | 0.095238 |

## Highest Component Scores

| Row Index | Level | Components | Changed | Score |
| ---: | --- | ---: | ---: | ---: |
| 62 | Fácil | 25 | 21 | 0.840000 |
| 23 | Fácil | 17 | 12 | 0.705882 |
| 3 | Fácil | 12 | 8 | 0.666667 |
| 63 | Média | 35 | 23 | 0.657143 |
| 35 | Fácil | 22 | 14 | 0.636364 |
| 22 | Fácil | 19 | 12 | 0.631579 |
| 89 | Muito Difícil | 14 | 8 | 0.571429 |
| 29 | Fácil | 23 | 13 | 0.565217 |
| 85 | Fácil | 21 | 11 | 0.523810 |
| 65 | Fácil | 21 | 11 | 0.523810 |

## Limitations

This score is a structural-change heuristic over normalized SQL AST components. It is interpretable, but it does not prove SQL correctness, behavioral equivalence, or natural-language alignment.
