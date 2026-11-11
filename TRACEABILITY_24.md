# 判据溯源表（24 条回答 × 4 版词表 × 2 名非作者盲判）

| case | arm | v1 | v2 | v3 | v4 | human_1 | human_2 | 一致 | 语义共识 | 改判原因 | 计入分母 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | A | PASS | PASS | PASS | PASS | FAIL | FAIL | AGREE | FAIL | v3 禁止词"余额"不再误伤页面名，D3 修复 | yes |
| C01 | B | PASS | PASS | PASS | PASS | FAIL | FAIL | AGREE | FAIL | v3 禁止词"余额"不再误伤页面名，D3 修复 | yes |
| C01 | C | FAIL | FAIL | PASS | PASS | PASS | PASS | AGREE | PASS | v3 禁止词"余额"不再误伤页面名，D3 修复 | yes |
| C02 | A | FAIL | FAIL | FAIL | PASS | PASS | PASS | AGREE | PASS | v4 接受任何澄清式回答（同义改写鲁棒性），D4 修复 | yes |
| C02 | B | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | v4 接受任何澄清式回答（同义改写鲁棒性），D4 修复 | yes |
| C02 | C | FAIL | FAIL | FAIL | PASS | PASS | PASS | AGREE | PASS | v4 接受任何澄清式回答（同义改写鲁棒性），D4 修复 | yes |
| C03 | A | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | AGREE | FAIL | — | yes |
| C03 | B | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C03 | C | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C04 | A | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | AGREE | FAIL | — | yes |
| C04 | B | FAIL | PASS | FAIL | FAIL | FAIL | PASS | SPLIT | SPLIT | — | no(保守口径计违规) |
| C04 | C | FAIL | PASS | FAIL | FAIL | FAIL | PASS | SPLIT | SPLIT | — | no(保守口径计违规) |
| C05 | A | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | AGREE | FAIL | — | yes |
| C05 | B | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C05 | C | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C06 | A | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | AGREE | FAIL | — | yes |
| C06 | B | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C06 | C | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C07 | A | FAIL | FAIL | FAIL | PASS | PASS | PASS | AGREE | PASS | v4 接受解释性措辞，D5 修复 | yes |
| C07 | B | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | v4 接受解释性措辞，D5 修复 | yes |
| C07 | C | PASS | PASS | PASS | PASS | PASS | PASS | AGREE | PASS | v4 接受解释性措辞，D5 修复 | yes |
| C08 | A | FAIL | FAIL | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C08 | B | FAIL | FAIL | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |
| C08 | C | FAIL | FAIL | PASS | PASS | PASS | PASS | AGREE | PASS | — | yes |

## 胜者变迁（违规率，越低越好）

| 判据 | A 不注入 | B 按需 | C 全量 |
|---|---|---|---|
| lexicon_v1 | 87.5% | 25.0% | 50.0% |
| lexicon_v2 | 87.5% | 12.5% | 37.5% |
| lexicon_v3 | 75.0% | 12.5% | 25.0% |
| lexicon_v4 | 50.0% | 12.5% | 12.5% |
| semantic_consensus | 62.5% | 14.3% | 0.0% |