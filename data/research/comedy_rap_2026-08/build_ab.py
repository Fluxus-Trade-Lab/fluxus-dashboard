"""渲染盲选卷 + 答案卷。

散文里不许出现手打的数字（pitfall: i_misread_my_own_table）——所有词数、通过/未通过
判定都由本脚本从 pairs_*.json 现算，README 里的表整段是本脚本的输出。

打乱用 zlib.crc32 而不是 hash()：Python 对字符串哈希每进程随机化
（pitfall: 08-26 那份 smoke fixture 就栽在这里），crc32 逐位可复现。

用法：python3 build_ab.py   （在本目录下跑，写出 4 个 .md）
"""
import json
import zlib

COMPRESS_BAR = 0.30  # 任务书 §二 目标 A：词数 −30% 以上


def words(s):
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


def perm(key, n):
    """由 key 决定的确定性置换（Fisher-Yates，随机源=crc32 链）。"""
    idx = list(range(n))
    seed = zlib.crc32(key.encode())
    for i in range(n - 1, 0, -1):
        seed = zlib.crc32(str(seed).encode())
        j = seed % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    return idx


def build_compression(data):
    blind = ["# 盲选卷 A · 压缩（目标 A）\n",
             "> 每组两版，**不标哪版是哪版**。只回一个字母。判据是任务书 §二：",
             "> 「读完之后我更愿意把哪一版发出去」。词数在答案卷里，选的时候别算。\n"]
    key = ["# 答案卷 A · 压缩 —— ⚠️ 盲选前不要打开\n",
           "| 组 | 类别 | 原句词数 | 改写词数 | 减幅 | 过 −30% 线 | A 是 | 用了什么 device |",
           "|---|---|---|---|---|---|---|---|"]
    n_pass = n_exp = 0
    for p in data["pairs"]:
        wo, wr = words(p["original"]), words(p["rewrite"])
        drop = (wo - wr) / wo
        passed = drop >= COMPRESS_BAR
        if p["class"] == "expository":
            n_exp += 1
            n_pass += int(passed)
        flip = perm(p["id"], 2)[0] == 1
        a, b = (p["rewrite"], p["original"]) if flip else (p["original"], p["rewrite"])
        blind.append(f"\n### {p['id']}\n\n**A.** {a}\n\n**B.** {b}\n\n**你选：____**")
        key.append(f"| {p['id']} | {p['class']} | {wo} | {wr} | {drop:.0%} | "
                   f"{'✅' if passed else '❌'} | {'改写' if flip else '原句'} | "
                   f"{', '.join(p['devices'])} |")
    key.append(f"\n**expository 组 {n_pass}/{n_exp} 过 −30% 词数线。**"
               f" tight 组是对照组，不计入这条线。")
    return "\n".join(blind) + "\n", "\n".join(key) + "\n"


def build_closings(data):
    blind = ["# 盲选卷 B · 收口（目标 B）\n",
             "> 每个位置 4 个候选，**其中一个是已经存在的版本**（正在用的、或曾经写过的），不标记。只回一个字母。",
             "> 判据是你自己 08-24 定的：**要一读就懂的重话，不要要回味的巧话。**\n"]
    key = ["# 答案卷 B · 收口 —— ⚠️ 盲选前不要打开\n",
           "**S10 是校准位。** 它的选项里有一句是 **Andy 2026-08-24 自己从 MRNA 长文里删掉的收口**",
           "（`origin = deleted-by-andy-2026-08-24`，理由是他当时说的「不怎么通顺」）。",
           "判读：**若他这次选中了那一句**，说明本研究对他偏好的读法（「要一读就懂的重话，不要要回味的巧话」）",
           "理解错了，S1–S9 的结论一并打折，下一轮先重建对他偏好的读法再谈 device。\n",
           "| 位 | 选项 | 来源 | 词数 | device |", "|---|---|---|---|---|"]
    for s in data["slots"]:
        blind.append(f"\n### {s['id']} · {s.get('context_blind', s['context'])}\n")
        order = perm(s["id"], len(s["candidates"]))
        for letter, ci in zip("ABCD", order):
            c = s["candidates"][ci]
            blind.append(f"**{letter}.** {c['text']}\n")
            key.append(f"| {s['id']} | {letter} | {c['origin']} | {words(c['text'])} | "
                       f"{', '.join(c['devices']) or '—'} |")
        blind.append("**你选：____**")
    flagged = sum(1 for s in data["slots"] for c in s["candidates"]
                  if c["origin"] == "study" and "mirrored-FLAGGED" in c["devices"])
    study = sum(1 for s in data["slots"] for c in s["candidates"] if c["origin"] == "study")
    key.append(f"\n**本研究产出的候选 {study} 条，其中 {flagged} 条是对仗结构（⚠️对仗，"
               f"任务书 §四要求标记后进盲选、不预先排除）。**")
    return "\n".join(blind) + "\n", "\n".join(key) + "\n"


if __name__ == "__main__":
    cb, ck = build_compression(json.load(open("pairs_compression.json")))
    lb, lk = build_closings(json.load(open("pairs_closings.json")))
    open("BLIND_A_compression.md", "w").write(cb)
    open("BLIND_B_closings.md", "w").write(lb)
    open("ANSWER_KEY_A.md", "w").write(ck)
    open("ANSWER_KEY_B.md", "w").write(lk)
    print("wrote 4 files")
