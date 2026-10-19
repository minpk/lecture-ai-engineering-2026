from types import SimpleNamespace

from app import ask


def test_interactive_chat_sends_each_question_to_the_same_chat(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(text=f"回答{len(self.questions)}", usage_metadata=None)

    class FakeChats:
        def __init__(self, chat):
            self.chat = chat

        def create(self, *, model):
            assert model == ask.MODEL
            return self.chat

    chat = FakeChat()
    client = SimpleNamespace(chats=FakeChats(chat))
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    elapsed_times = iter([10.0, 11.25, 20.0, 22.5])
    monkeypatch.setattr(ask.time, "perf_counter", lambda: next(elapsed_times))
    questions = iter(["最初の質問", "続きの質問", "終了"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask.interactive_chat()

    assert chat.questions == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "AI> 回答2" in output
    assert "[応答時間] 1.25秒" in output
    assert "[応答時間] 2.50秒" in output


def test_ask_prints_token_counts_and_response_time(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=5),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    elapsed_times = iter([4.0, 5.234])
    monkeypatch.setattr(ask.time, "perf_counter", lambda: next(elapsed_times))

    assert ask.ask("質問") == "回答"

    output = capsys.readouterr().out
    assert "[トークン] 入力: 3, 出力: 5" in output
    assert "[応答時間] 1.23秒" in output
