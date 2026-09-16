# 2026-09-16 分支清理（OPS Fable，Andy 原话「合，失效的分支也列出来删」）

**合进 main**：`auto/night-20260912-bb6565-protocol`（RESEARCH_PROTOCOL.md +7 行）· `auto/night-20260914-4ef60f-metric`（METRIC_SOURCES.md +1 行）→ `87d43cf8`。

**删除判据**：`git cherry origin/main <分支>` 全部是 `-`（每个 commit 都有等价补丁已在 main 上）。24 条全部满足；删前逐条核过没有被任何 worktree 占用。要恢复任何一条：`git branch <名> <sha>`（本机 reflog 约 90 天内也能找回）。

| 分支 | 本地 sha | 远端 sha |
|---|---|---|
| `auto/night-20260828-bfbf5c` | `8579079f0778f96dbae349bfd83012fb76ffc01a` | `8579079f0778f96dbae349bfd83012fb76ffc01a` |
| `auto/night-20260831-2a66fb` | `7a3352fca6426322fd36a51f70325021540b92a2` | `525194047cbe1b4b5a387614148a2c53656e060c` |
| `auto/night-20260905-805da3-fbclock` | `78e2c50ef76565578138627dc0a3a2d970d482e1` | `78e2c50ef76565578138627dc0a3a2d970d482e1` |
| `auto/night-20260906-8acfa1` | `afc06b47f652710d4b85b8768b0b582fee445c3e` | `e4661d0210c33c712689b3e412e1e29d482652ab` |
| `auto/night-20260909-7728f0` | `9fc1135e559c7a5c5c81b6e76d8ec57e5398ae0e` | `0e71456df9a281c1c9dc8aa0b496542c7b0f5281` |
| `auto/night-20260912-bb6565-protocol` | `13e558e3cf1833ca421030ea7fa868ed2bb1f180` | `13e558e3cf1833ca421030ea7fa868ed2bb1f180` |
| `auto/night-20260914-4ef60f` | `e4452e2b293425b1b9ac2890be57edfb1b5807c2` | `3f084bad8a72cf0391024d557cc105188f6a71cd` |
| `auto/night-20260914-4ef60f-metric` | `1486755ce1b8c79d05f698d5b5a13e101097cb85` | `1486755ce1b8c79d05f698d5b5a13e101097cb85` |
| `auto/night-20260915-1182f5` | `83e4e4c63f9967944c0116a5b90d979f47ccc246` | `74e8e611ff7168ee6d2e12f575ae4d70252a9766` |
| `auto/tests-and-collect-4b6905` | `33a4d469fafa3e773b320209e3efdb52cafc0a34` | `33a4d469fafa3e773b320209e3efdb52cafc0a34` |
| `auto/vol-dedup-2026-09-04` | `none` | `261b4203ea64532ac118dca3243f143fdb5841fd` |
| `feat/ops-recap-automation-2026-09-13` | `50f227a3a720e18ddeb4bd0d724bc07abf9716a1` | `50f227a3a720e18ddeb4bd0d724bc07abf9716a1` |
| `fix/fbclock-rebased-2026-09-10` | `2aa8e67cd5af81df943d2761f14fd2dd8b12ced8` | `2aa8e67cd5af81df943d2761f14fd2dd8b12ced8` |
| `fix/joe-ci-root-tests-2026-09-11` | `3e4655556383e6a02a58ba5565f166ab166b010a` | `3e4655556383e6a02a58ba5565f166ab166b010a` |
| `fix/joe-fbclock-rebased-2026-09-08` | `6e4e67041fb1d4c51f75f9039f051e0c4c63c6b3` | `6e4e67041fb1d4c51f75f9039f051e0c4c63c6b3` |
| `fix/joe-fbclock-verified-2026-09-10` | `none` | `1829671d9adc9d5259f8e7e5376deedf7e4f19b5` |
| `fix/joe-iscore-rebaseline-2026-09-11` | `391638bc7b660d1a1b335c6e029320fad3f47fee` | `391638bc7b660d1a1b335c6e029320fad3f47fee` |
| `fix/joe-ledger-evidence-2026-09-10` | `none` | `6916e8efc67795c96fd58c2f359e63fb664b2fed` |
| `fix/joe-lrow-unbound-2026-09-11` | `723f6aed77697065519022b460df107788b2c4dd` | `723f6aed77697065519022b460df107788b2c4dd` |
| `fix/joe-wf-late-dup-ledger-2026-09-11` | `adb7261658db801bf88eaa6da93234d0641d1f3d` | `adb7261658db801bf88eaa6da93234d0641d1f3d` |
| `fix/ops-strip-dollars-qty-2026-09-13` | `58610ef74a368a3a873bd950bb34b7f5bb97c436` | `58610ef74a368a3a873bd950bb34b7f5bb97c436` |
| `fix/x-watch-members-param` | `55df6f649a048aa20a651ced636a83d15be8418f` | `none` |
| `fix/x-watch-mentions-upsert` | `4a7236084647dcc3409dbfe808ad4f00610612b9` | `4a7236084647dcc3409dbfe808ad4f00610612b9` |
| `voice/deslop-ammo` | `e26af4b74125a0d5665cfbf0286c071627dac76f` | `e26af4b74125a0d5665cfbf0286c071627dac76f` |

**有意保留**（不是失效，内容不在 main 上或另有用途）：
- `auto/night-20260903-5cea87`（9 个 commit 不在 main）· `auto/night-20260905-805da3-metricsrc`（「金9银10」口径登记不在 main）· `fix/alex-stockbee-s2-prev-volume`（一条测试不在 main，归 DATA ALEX）
- `auto/night-20260819`（被 Zac 的夜间工作树占用，宪法不许碰）
- `design/marketing-visual`（Visual Vera 长期设计分支，不合）
- `archive/*`、`claude/*`、`fix/ohlc-staleness-guard`、`worktree-fluxus-data-art`（08-22 大扫除前的封存与旧工作区）
- `feat/morning-three-pages`（主工作树当前分支）

## 追记（2026-09-17）：原「有意保留」的三条也删了

Andy 原话：「这三个分支，"金9银10"这个研究分析删除，不需要了。其他两个可删除。」
`805da3-metricsrc`（金9银10 口径登记 + §七 结案行）**不合**，直接删；另两条的内容已在 main 上。

| 分支 | 本地 sha | 远端 sha |
|---|---|---|
| `auto/night-20260905-805da3-metricsrc` | `7e924be4ab6fce73cc55960147cb8c554278f7b2` | `7e924be4ab6fce73cc55960147cb8c554278f7b2` |
| `auto/night-20260903-5cea87` | `b482c89bcde73283943eeea395e405fbdd7f213d` | `b482c89bcde73283943eeea395e405fbdd7f213d` |
| `fix/alex-stockbee-s2-prev-volume` | `e3d38ecc595252482e119d759dda5e0c37cb2c84` | `e3d38ecc595252482e119d759dda5e0c37cb2c84` |

⚠️ main 上已停用的选题卡 `2026-09-06_autumn-effect-decay/RECORD.md` 引用的 `7e924be4` 从此只能靠本表的 sha 找回。
