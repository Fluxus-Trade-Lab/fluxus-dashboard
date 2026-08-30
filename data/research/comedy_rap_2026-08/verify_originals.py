"""核对：A/B 里每一条 original 都必须逐字出现在已发布正文里。

为什么有这个脚本：本仓的坑账里有两条直接指向这里——「读到了源码，当成了行为」
与「我读错了自己刚打印的那张表」。A/B 的整个效力建立在「左边那版真的是他发出去的那句」
上；靠眼睛比对就等于没比对。归一化只做空白与引号/破折号的字形，不做任何词的增删。
"""
import json, re, sys, pathlib

SRC = pathlib.Path(__file__).resolve().parents[3] / \
    "Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md"


def norm(s):
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("—", "-").replace("–", "-").replace("‑", "-")
    s = re.sub(r"[*_`]", "", s)          # markdown 强调符不算正文
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main():
    body = norm(SRC.read_text())
    bad = []
    checked = 0
    for p in json.load(open("pairs_compression.json"))["pairs"]:
        checked += 1
        if norm(p["original"]) not in body:
            bad.append(("compression", p["id"]))
    for s in json.load(open("pairs_closings.json"))["slots"]:
        for c in s["candidates"]:
            if c["origin"] == "published":
                checked += 1
                if norm(c["text"]) not in body:
                    bad.append(("closing", s["id"]))
    print(f"checked {checked} originals against {SRC.name}")
    if bad:
        print("NOT VERBATIM:", bad)
        return 1
    print("all verbatim ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
