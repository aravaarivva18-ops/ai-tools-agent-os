import logging
import random
import re

# Настройка логирования
logger = logging.getLogger("humanizer")

# Базовый словарь сокращений для английского языка
ENGLISH_CONTRACTIONS = {
    "can't": "cannot",
    "won't": "will not",
    "n't": " not",
    "'re": " are",
    "'s": " is",
    "'ll": " will",
    "'ve": " have",
    "'d": " would",
    "'m": " am",
}

# Вводные фразы для придания тексту более гладкого и академического звучания
RUSSIAN_TRANSITIONS = [
    "Следовательно,",
    "Более того,",
    "Таким образом,",
    "С другой стороны,",
    "Вместе с тем,",
    "Как следствие,",
    "Разумеется,",
    "Стоит отметить, что",
]

ENGLISH_TRANSITIONS = [
    "Moreover,",
    "Additionally,",
    "Furthermore,",
    "Hence,",
    "Therefore,",
    "Consequently,",
    "Nonetheless,",
    "Nevertheless,",
]

# Простой маппер синонимов для русского языка (для базовой синонимизации)
RUSSIAN_SYNONYMS = {
    "важный": ["ключевой", "значимый", "существенный", "первостепенный"],
    "сделать": ["реализовать", "выполнить", "осуществить", "создать"],
    "быстро": ["оперативно", "в кратчайшие сроки", "стремительно"],
    "помочь": ["оказать содействие", "поспособствовать", "выручить"],
    "проблема": ["трудность", "задача", "сложность", "препятствие"],
    "очень": ["крайне", "весьма", "в значительной степени"],
    "простой": ["элементарный", "доступный", "несложный"],
    "бизнес": ["предпринимательство", "дело", "коммерция"],
    "клиент": ["заказчик", "покупатель", "потребитель"],
}


class LocalTextHumanizer:
    """
    Класс для локального 'очеловечивания' текста на русском и английском языках.
    Сглаживает ИИ-паттерны, убирает штампы и повышает читаемость без внешних API.
    """

    def __init__(
        self,
        p_transition: float = 0.3,
        p_synonym: float = 0.3,
        seed: int | None = None,
    ):
        if seed is not None:
            random.seed(seed)

        self.p_transition = p_transition
        self.p_synonym = p_synonym

    def humanize(self, text: str, lang: str = "ru") -> str:
        """Основной метод очеловечивания текста."""
        if not text or not text.strip():
            return text

        # Разделяем текст по абзацам/предложениям
        paragraphs = text.split("\n")
        processed_paragraphs = []

        for paragraph in paragraphs:
            if not paragraph.strip():
                processed_paragraphs.append("")
                continue

            # Разделяем на предложения
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            processed_sentences = []

            for sent in sentences:
                if not sent.strip():
                    continue

                # 1. Обработка сокращений (для английского)
                if lang == "en":
                    sent = self._expand_contractions(sent)

                # 2. Случайное добавление академических/вводных связок
                if random.random() < self.p_transition:
                    sent = self._add_transitions(sent, lang)

                # 3. Базовая замена слов на синонимы
                if random.random() < self.p_synonym:
                    sent = self._replace_synonyms(sent, lang)

                processed_sentences.append(sent)

            processed_paragraphs.append(" ".join(processed_sentences))

        return "\n".join(processed_paragraphs)

    def _expand_contractions(self, sentence: str) -> str:
        result = sentence
        for contraction, expansion in ENGLISH_CONTRACTIONS.items():
            pattern = re.compile(re.escape(contraction), re.IGNORECASE)
            matches = pattern.finditer(result)
            for match in reversed(list(matches)):
                original = match.group()
                if original[0].isupper():
                    replaced = expansion[0].upper() + expansion[1:]
                else:
                    replaced = expansion
                result = result[: match.start()] + replaced + result[match.end() :]
        return result

    def _add_transitions(self, sentence: str, lang: str) -> str:
        # Не добавляем к слишком коротким предложениям
        if len(sentence.split()) < 4:
            return sentence

        transitions = RUSSIAN_TRANSITIONS if lang == "ru" else ENGLISH_TRANSITIONS
        transition = random.choice(transitions)

        # Если предложение начинается с заглавной, переводим первое слово в строчную
        words = sentence.split()
        if words:
            first_word = words[0]
            clean_first = re.sub(r"[^\w]", "", first_word)
            if clean_first and clean_first[0].isupper() and not clean_first.isupper():
                words[0] = first_word[0].lower() + first_word[1:]
                sentence = " ".join(words)

        return f"{transition} {sentence}"

    def _replace_synonyms(self, sentence: str, lang: str) -> str:
        if lang != "ru":
            return sentence

        words = sentence.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r"[^\w]", "", word).lower()
            if clean_word in RUSSIAN_SYNONYMS:
                if random.random() < 0.4:
                    synonym = random.choice(RUSSIAN_SYNONYMS[clean_word])
                    if word[0].isupper():
                        synonym = synonym.capitalize()
                    prefix = re.match(r"^[^\w]+", word)
                    suffix = re.search(r"[^\w]+$", word)
                    pre = prefix.group(0) if prefix else ""
                    suf = suffix.group(0) if suffix else ""
                    words[i] = f"{pre}{synonym}{suf}"

        return " ".join(words)
