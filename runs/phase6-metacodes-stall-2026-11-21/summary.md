# witness/stall 汇总

每格的判定计数，后面是单侧 95% Wilson 界（z=1.645，`skills/repo-quake/references/measurement.md`），分母不含 invalid。3/3 的下界只有 0.53：小样本只分三档（稳定出现、时有时无、稳定不出现），不给比率。

| 组 | N（有效） | 判定 | Wilson 界 | 等级 | invalid | 关键数字 |
|---|---:|---|---|---|---:|---|
| C0-pre | 3 | healthy 3/3 | healthy 0.53–1.00 | -,-,- | 0 | box_s 0.042/0.046/0.041; exit_s 0.010/0.013/0.013 |
| P-splash | 3 | startup_floor_seen 3/3 | startup_floor_seen 0.53–1.00 | -,-,- | 0 | box_s 1.557/1.537/1.539 |
| P-stdio5-exit | 3 | exit_paid_per_server 3/3 | exit_paid_per_server 0.53–1.00 | -,-,- | 0 | box_s 0.047/0.058/0.060; exit_s 1.045/1.032/1.029 |
| S-models-5s | 3 | startup_waited 3/3 | startup_waited 0.53–1.00 | L0,L0,L0 | 0 | box_s 5.053/5.045/5.049; exit_s 0.012/0.013/0.013 |
| S-models-stall | 3 | startup_blocked 3/3 | startup_blocked 0.53–1.00 | L0,L0,L0 | 0 |  |
| S-models-warm | 3 | no_wait 3/3 | no_wait 0.53–1.00 | -,-,- | 0 | box_s 0.043/0.045/0.040; exit_s 0.011/0.013/0.011 |
| S-kg-stall | 3 | startup_waited_kg 3/3 | startup_waited_kg 0.53–1.00 | L1,L1,L1 | 0 | box_s 35.057/35.045/35.050; exit_s 0.012/0.013/0.013 |
| K-keys-5s | 3 | prompt_frozen 3/3 | prompt_frozen 0.53–1.00 | L0,L0,L0 | 0 | box_s 0.067/0.039/0.052; echo_lag_s 4.589/4.592/4.596; exit_s 0.012/0.013/0.013 |
| K-keys-stall | 3 | frozen_until_watchdog 3/3 | frozen_until_watchdog 0.53–1.00 | L0,L0,L0 | 0 | box_s 0.050/0.041/0.049; sigterm_exit_s 45.012/45.014/45.012 |
| M-stdio-stall | 3 | first_message_waited_timeout 3/3 | first_message_waited_timeout 0.53–1.00 | L3,L3,L3 | 0 | box_s 0.049/0.041/0.049; first_request_wait_s 4.447/4.449/4.488 |
| M-stdio-stall-esc | 3 | interruptible 3/3 | interruptible 0.53–1.00 | L3,L3,L3 | 0 | box_s 0.054/0.039/0.056; interrupted_after_esc_s 0.142/0.143/0.145 |
| M-http-delete-stall | 3 | exit_blocked 3/3 | exit_blocked 0.53–1.00 | L0,L0,L0 | 0 | box_s 0.038/0.060/0.054 |
| M-https-tls-stall | 3 | unbounded 3/3 | unbounded 0.53–1.00 | L1,L1,L1 | 0 | box_s 0.037/0.077/0.068; interrupted_after_esc_s 0.142/0.142/0.143 |
| E-otlp-stall | 3 | exit_waited_export 3/3 | exit_waited_export 0.53–1.00 | L1,L1,L1 | 0 | box_s 0.039/0.041/0.061; exit_s 2.010/2.012/2.021 |
| T-edit-silent-lsp | 3 | edit_waited_both_limits 3/3 | edit_waited_both_limits 0.53–1.00 | L1,L1,L1 | 0 | box_s 0.042/0.048/0.037 |
| K-keys-0s | 3 | responsive 3/3 | responsive 0.53–1.00 | -,-,- | 0 | box_s 0.057/0.037/0.053; echo_lag_s 0.000/0.000/0.000; exit_s 0.013/0.011/0.013 |
| T-edit-nolsp | 3 | no_wait 3/3 | no_wait 0.53–1.00 | -,-,- | 0 | box_s 0.043/0.038/0.044 |
| T-edit-gopls | 3 | first_edit_pays 3/3 | first_edit_pays 0.53–1.00 | -,-,- | 0 | box_s 0.040/0.038/0.056 |
| T-bash-mixed-1 | 3 | floor_seen 3/3 | floor_seen 0.53–1.00 | -,-,- | 0 | box_s 0.043/0.043/0.045; floor_s 0.108/0.108/0.109; touch_minus_echo_s 0.084/0.061/0.063 |
| T-bash-mixed-20k | 3 | observation_paid 3/3 | observation_paid 0.53–1.00 | -,-,- | 0 | box_s 0.088/0.075/0.076; floor_s 0.109/0.106/0.107; touch_minus_echo_s 0.925/1.081/0.976 |
| C0-post | 3 | healthy 3/3 | healthy 0.53–1.00 | -,-,- | 0 | box_s 0.041/0.056/0.038; exit_s 0.013/0.013/0.012 |

invalid 的原因：


manifest `manifest-20261121T175104-87852.json`：卡片提交 `3ec9c310c3d0`（已推送：None），被测二进制前后一致：True，证人前后一致：True，偏离：无
