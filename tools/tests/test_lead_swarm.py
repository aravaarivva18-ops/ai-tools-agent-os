import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lead_swarm import Lead, LeadScorer, LeadRouter, LeadAggregator


def test_lead_creation():
    """Test that a Lead object is correctly initialized with required attributes."""
    lead = Lead(
        lead_id="test_001",
        source="kwork",
        title="Нужен Telegram бот",
        description="Разработка Telegram-бота для автосалона на Python.",
        budget=15000.0,
        contacts="@client_tg",
    )
    assert lead.lead_id == "test_001"
    assert lead.source == "kwork"
    assert lead.title == "Нужен Telegram бот"
    assert lead.budget == 15000.0
    assert lead.contacts == "@client_tg"
    assert lead.qualified is False
    assert lead.score == 0.0
    assert lead.route_target is None


def test_lead_scorer_junk_detection():
    """Test that low budget leads and leads with stop words are qualified as junk."""
    scorer = LeadScorer(min_budget=5000.0, stop_words=["диплом", "курсовая", "бесплатно"])

    # Too low budget
    cheap_lead = Lead(
        lead_id="cheap",
        source="kwork",
        title="Скрипт на python",
        description="Нужно написать простой парсер за копейки",
        budget=1000.0,
    )
    score, status = scorer.score_lead(cheap_lead)
    assert score < 30
    assert status == "junk"

    # Stop words
    academic_lead = Lead(
        lead_id="academic",
        source="telegram",
        title="Написать дипломную работу",
        description="Разработка программы для диплома на Python.",
        budget=15000.0,
    )
    score, status = scorer.score_lead(academic_lead)
    assert score < 30
    assert status == "junk"


def test_lead_scorer_qualification():
    """Test that high value leads with relevant keywords are qualified properly."""
    scorer = LeadScorer(
        min_budget=5000.0,
        target_keywords=["бот", "автоматизация", "crm", "парсер", "скрейпинг", "ии"],
    )
    good_lead = Lead(
        lead_id="good_01",
        source="kwork",
        title="Интеграция CRM и AI бота",
        description="Требуется настроить автоматизацию отдела продаж и подключить OpenAI GPT-4o.",
        budget=50000.0,
    )
    score, status = scorer.score_lead(good_lead)
    assert score >= 70
    assert status == "qualified"


def test_lead_routing():
    """Test that qualified leads are routed to correct workspace channels based on keywords."""
    router = LeadRouter()

    sales_lead = Lead(
        lead_id="sales_01",
        source="kwork",
        title="Разработка CRM",
        description="Разработать backend на FastAPI для корпоративной ERP системы.",
        budget=100000.0,
    )
    sales_lead.qualified = True
    target = router.route(sales_lead)
    assert target == "ai-sales"

    marketing_lead = Lead(
        lead_id="marketing_01",
        source="telegram",
        title="Настройка SEO и лидогенерации",
        description="Необходим трафик на лендинг, запуск рекламы в Яндекс Директ и SEO-оптимизация.",
        budget=40000.0,
    )
    marketing_lead.qualified = True
    target = router.route(marketing_lead)
    assert target == "ai-marketing"


def test_lead_aggregator_parsing():
    """Test that raw text inputs are correctly parsed and aggregated as Lead structures."""
    aggregator = LeadAggregator()
    raw_kwork_post = """
Источник: Kwork
Заказ: Создать парсер сайтов недвижимости
Бюджет: 8000 руб
Контакты: @realestate_dev
Описание:
Нужно собирать данные с Циан и записывать в Excel. Ежедневный запуск.
"""
    leads = aggregator.parse_raw_text(raw_kwork_post)
    assert len(leads) == 1
    lead = leads[0]
    assert lead.source == "Kwork"
    assert "парсер" in lead.title.lower()
    assert lead.budget == 8000.0
    assert lead.contacts == "@realestate_dev"
    assert "Циан" in lead.description
