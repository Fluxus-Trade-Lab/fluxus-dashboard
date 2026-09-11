# 两个 verifier 的原件（2026-09-12，全新上下文子 agent）

原样拷贝，**没改一行**——它们实际跑的就是这些。路径写死在当晚的 scratchpad（重启即清），复跑要先改文件头的 `OUT` / `sys.path`。

- `recompute/`：**复算视角**。只拿 `prereg.md` 文本独立重写，不读 `study.py`。`out.txt` 是它的原始输出。
- `adversarial/`：**反驳视角**。读 `study.py` 找错。`build.py` 建事件表 → `a2.py` 聚类稳健性 · `a3.py` 波动控制 · `a4.py` 崩盘窗口与 ffill。
  它的数字只写在它的回报里（results.md「验证」节原样转述），脚本当晚没有另存输出文件。
