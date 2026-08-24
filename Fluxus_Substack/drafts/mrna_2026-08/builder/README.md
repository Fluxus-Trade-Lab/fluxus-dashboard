# 预览页构建管线

`python3 charts.py && python3 gen_visuals.py && python3 render.py` → 三个 preview html。
依赖 `imgs.json`（base64 截图库，~500KB，不入库）——截图源是 Andy 2026-08-23 的录屏
`~/Desktop/Video Recordings/raw-files/2026-08-23 18-40-38.mov` 抽帧（frames/f_*.jpg、fine/m_15.jpg），
丢了就按 build 脚本里的 crop 参数重抽。SVG 图表纯代码生成，数据在脚本里，可直接重跑。
