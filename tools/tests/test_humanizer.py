from tools.text.humanizer import LocalTextHumanizer


def test_humanizer_ru():
    humanizer = LocalTextHumanizer(p_transition=1.0, p_synonym=1.0, seed=42)
    input_text = (
        "Это очень важный бизнес. Мы хотим быстро помочь клиенту решить эту проблему."
    )
    output_text = humanizer.humanize(input_text, lang="ru")

    # Должны добавиться связки и замениться слова на синонимы
    assert (
        "весьма" in output_text
        or "крайне" in output_text
        or "Более того" in output_text
    )
    assert (
        "выручить" in output_text
        or "заказчик" in output_text
        or "потребитель" in output_text
    )


def test_humanizer_en():
    humanizer = LocalTextHumanizer(p_transition=1.0, p_synonym=0.0, seed=42)
    input_text = "I can't do this. It's not a big deal."
    output_text = humanizer.humanize(input_text, lang="en")

    # Сокращения должны раскрыться
    assert "cannot" in output_text
    assert "it is" in output_text or "It is" in output_text
