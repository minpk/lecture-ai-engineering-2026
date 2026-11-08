# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLM(gemini-3.5-flash-lite)では、回答をもっていないため一般的な文脈で回答が返却された。一方で、エージェントでは、用語集から回答を導き出して正確な回答が返却された。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"question": "「LoRA」の意味は？", "answer": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラメータが少なく、…
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：make_quizを追加。
docstringに書いた説明→
    """指定した回の用語から1つ選び、確認問題と答えを返す。
    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """

## 宿題

- 取り組んだレベル：基礎
- やったこと：用語の定義を入力されたら、用語集を検索したうえで正誤結果を返すanswer_quizを作成した。
docstringには以下を記載
def answer_quiz(statement: str, answer: str | None = None) -> str:
    """学生の説明文を入力として受け取り、用語集を検索して正誤を返す。

    例: "LoRAとは、事前学習済の重みは固定したまま、重みの更新分だけを学習する手法である"
    という形で入力される。用語名が分かれば、用語集で定義を探して正解か誤りかを返す。
    """

INSTRUCTIONSには以下を記載。
- 用語の定義を言われたらanswer_quizを追記。

- 結果：

(aie2026-exercises) @minpk ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent "トークンとは、LLMがテキストを扱う最小単位である。" --trace
[model] gemini-3.5-flash-lite
ご提示いただいた説明について用語集を確認したところ、「トークンとは、LLMがテキストを扱う最小単位である」という部分はその通りですが、今回は正確には用語集の定義と照らし合わせて**誤り**（あるいはより正確な定義の不足）として判定されます。

用語集における「トークン」の定義は以下の通りです：
> 「LLMがテキストを扱う最小単位。単語や文字の断片に分割される。APIの料金、レート制限、コンテキストウィンドウの大きさは、多くの場合トークン数で数える。日本語は英語より1文字あたりのトークン数が多くなりやすい。」

（第1回）

--- trace ---
[tool call]   search_glossary({'query': 'トークン'})
[tool return] search_glossary -> [{"term": "トークン", "lecture": 1, "definition": "LLMがテキストを扱う最小単位。単語や文字の断片に分割される。APIの料金、レート制限、コンテキストウィンドウの大きさは、多くの場合トークン数で数…
[tool call]   answer_quiz({'statement': 'トークンとは、LLMがテキストを扱う最小単位である。'})
[tool return] answer_quiz -> 誤りです…
[usage] RunUsage(cost=Decimal('0.0011516'), details={'text_prompt_tokens': 2272}, input_text_tokens=2272, input_tokens=2272, output_tokens=188, requests=3, tool_calls=2)

- 気づき・疑問：
用語集に内容と比較したときに、少し情報が不足しているだけで誤りではないのに「誤り」と返っていたので、answer_quizの実装の仕方に改善の余地があると感じた。
search_glossaryで2回、answer_quizで1回エージェントが呼び出されており、合計requests=3だった。無駄がある気がしているが、どう改善すればよいのかわかっていない。
