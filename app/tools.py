"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
import re
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    text = text.casefold().replace(" ", "").replace("　", "")
    return re.sub(r"[、。！？：；・「」『』()（）\[\]{}【】…]", "", text)


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つ選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """
    terms = [entry for entry in load_glossary() if entry.get("lecture") == lecture]
    if not terms:
        if lecture <= 0:
            return f"第{lecture}回は存在しません。1 以上の回を指定してください。"
        return f"第{lecture}回の用語はまだありません。"

    term = random.choice(terms)
    return json.dumps(
        {
            "question": f"「{term['term']}」の意味は？",
            "answer": term["definition"],
        },
        ensure_ascii=False,
    )


def answer_quiz(statement: str, answer: str | None = None) -> str:
    """学生の説明文を入力として受け取り、用語集を検索して正誤を返す。

    例: "LoRAとは、事前学習済の重みは固定したまま、重みの更新分だけを学習する手法である"
    という形で入力される。用語名が分かれば、用語集で定義を探して正解か誤りかを返す。
    """
    if answer is not None:
        statement = f"{statement}とは、{answer}"

    if not statement or not statement.strip():
        return "誤りです。用語と説明を入力してください。"

    text = statement.strip()
    match = re.search(r"(.+?)\s*とは\s*[、:：]?\s*(.+)", text)
    if not match:
        return "誤りです。例のように「用語とは、説明」の形式で入力してください。"

    term_name = match.group(1).strip()
    user_definition = match.group(2).strip()
    if not term_name or not user_definition:
        return "誤りです。用語と説明を両方入力してください。"

    glossary_term = None
    for entry in load_glossary():
        if term_name in _names(entry):
            glossary_term = entry
            break

    if glossary_term is None:
        search_result = json.loads(search_glossary(term_name))
        if isinstance(search_result, list) and search_result:
            glossary_term = {
                "term": search_result[0]["term"],
                "definition": search_result[0]["definition"],
            }

    if glossary_term is None:
        return "用語集にその用語は見つかりませんでした。"

    expected = glossary_term.get("definition", "")
    if not expected:
        return "誤りです。用語の定義が見つかりませんでした。"

    expected_norm = _normalize(expected)
    user_norm = _normalize(user_definition)
    if user_norm == expected_norm or user_norm in expected_norm or expected_norm in user_norm:
        return "正解です"

    # 誤りの典型例: 「全重み」「全部を学習」など、定義の中心が逆転しているケース
    contradiction = ["全部", "全て", "全体", "固定しない", "全重み", "すべての重み", "すべてを学習"]
    if any(p in user_definition for p in contradiction) and "固定" not in user_definition:
        return "誤りです"

    expected_tokens = {
        token
        for token in re.findall(r"[A-Za-z0-9一-龠ぁ-んァ-ンー]+", expected)
        if len(token) >= 2 and token.casefold() not in {"llm", "が", "の", "と", "を", "は", "で", "に", "する", "ある", "こと"}
    }
    user_tokens = {
        token
        for token in re.findall(r"[A-Za-z0-9一-龠ぁ-んァ-ンー]+", user_definition)
        if len(token) >= 2 and token.casefold() not in {"llm", "が", "の", "と", "を", "は", "で", "に", "する", "ある", "こと"}
    }
    overlap = len(expected_tokens & user_tokens)
    if overlap >= max(2, len(expected_tokens) * 0.5):
        return "正解です"

    return "誤りです"