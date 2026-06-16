#!/usr/bin/env python3
"""Lead Swarm module for automatic B2B lead aggregation, scoring, and routing."""

import re
from typing import Optional


class Lead:
    """Represents a B2B lead collected from channel or freelance platform."""

    def __init__(
        self,
        lead_id: str,
        source: str,
        title: str,
        description: str,
        budget: float,
        contacts: str = "",
        raw_data: dict | None = None,
    ):
        self.lead_id = lead_id
        self.source = source
        self.title = title
        self.description = description
        self.budget = budget
        self.contacts = contacts
        self.raw_data = raw_data or {}
        self.qualified = False
        self.score = 0.0
        self.route_target: str | None = None


class LeadScorer:
    """Scores B2B leads based on budget, target keywords, and stop words."""

    def __init__(
        self,
        min_budget: float = 5000.0,
        target_keywords: list[str] | None = None,
        stop_words: list[str] | None = None,
    ):
        self.min_budget = min_budget
        self.target_keywords = target_keywords or [
            "бот",
            "автоматизация",
            "crm",
            "парсер",
            "скрейпинг",
            "ии",
            "разработка",
            "сайт",
            "seo",
            "маркетинг",
        ]
        self.stop_words = stop_words or ["диплом", "курсовая", "бесплатно", "курсовую"]

    def score_lead(self, lead: Lead) -> tuple[float, str]:
        """Calculates relevance score and updates qualification status."""
        if lead.budget < self.min_budget:
            lead.score = 10.0
            lead.qualified = False
            return lead.score, "junk"

        text_to_check = (lead.title + " " + lead.description).lower()
        for sw in self.stop_words:
            if sw in text_to_check:
                lead.score = 15.0
                lead.qualified = False
                return lead.score, "junk"

        score = 40.0
        matched_keywords = 0
        for kw in self.target_keywords:
            if kw in text_to_check:
                matched_keywords += 1
                score += 15.0

        if lead.budget >= 50000.0:
            score += 20.0
        elif lead.budget >= 20000.0:
            score += 10.0

        score = min(score, 100.0)
        lead.score = score
        lead.qualified = score >= 60.0

        status = "qualified" if lead.qualified else "junk"
        return score, status


class LeadRouter:
    """Routes qualified leads to appropriate workspace departments."""

    def __init__(self):
        self.marketing_keywords = [
            "маркетинг",
            "seo",
            "трафик",
            "реклама",
            "продвижение",
            "smm",
            "директ",
        ]
        self.sales_keywords = [
            "разработка",
            "бот",
            "crm",
            "парсер",
            "скрейпинг",
            "код",
            "программа",
            "backend",
        ]

    def route(self, lead: Lead) -> str | None:
        """Routes a lead to ai-sales or ai-marketing based on content analysis."""
        if not lead.qualified:
            lead.route_target = None
            return None

        text_to_check = (lead.title + " " + lead.description).lower()

        marketing_hits = sum(1 for kw in self.marketing_keywords if kw in text_to_check)
        sales_hits = sum(1 for kw in self.sales_keywords if kw in text_to_check)

        if marketing_hits > sales_hits:
            lead.route_target = "ai-marketing"
        else:
            lead.route_target = "ai-sales"

        return lead.route_target


class LeadAggregator:
    """Aggregates and parses raw lead text inputs."""

    def parse_raw_text(self, raw_text: str) -> list[Lead]:
        """Parses structured text post blocks into Lead objects."""
        leads: list[Lead] = []

        source_match = re.search(r"Источник:\s*(.*)", raw_text)
        title_match = re.search(r"Заказ:\s*(.*)", raw_text)
        budget_match = re.search(r"Бюджет:\s*(\d+)", raw_text)
        contacts_match = re.search(r"Контакты:\s*(.*)", raw_text)

        description = ""
        desc_match = re.search(r"Описание:\s*(.*)", raw_text, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()

        source = source_match.group(1).strip() if source_match else "unknown"
        title = title_match.group(1).strip() if title_match else "Без названия"
        budget = float(budget_match.group(1)) if budget_match else 0.0
        contacts = contacts_match.group(1).strip() if contacts_match else ""

        lead_id = f"lead_{hash(raw_text) & 0xffffffff}"

        lead = Lead(
            lead_id=lead_id,
            source=source,
            title=title,
            description=description,
            budget=budget,
            contacts=contacts,
            raw_data={"raw_text": raw_text},
        )
        leads.append(lead)
        return leads
