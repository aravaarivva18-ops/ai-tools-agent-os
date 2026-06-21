"""Unit tests for tools/wb_parser.py."""

import os
import sys
from unittest.mock import MagicMock, patch

# Ensure tools/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.scraping.wb_parser import WildberriesParser


@patch("curl_cffi.requests.get")
def test_parse_product_success(mock_get):
    """Verify raw WB response is correctly parsed and values normalized."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "products": [
                {
                    "name": "Футболка мужская спортивная",
                    "brand": "Adidas",
                    "brandId": 12345,
                    "rating": 4.8,
                    "feedbacks": 512,
                    "sizes": [
                        {
                            "price": {
                                "basic": 250000,  # 2500.00 RUB
                                "total": 125000,  # 1250.00 RUB
                                "logDiscount": 50,
                            },
                            "stocks": [{"qty": 10}],
                        }
                    ],
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    parser = WildberriesParser()
    result = parser.parse_product("12345678")

    assert result["success"] is True
    assert result["name"] == "Футболка мужская спортивная"
    assert result["brand"] == "Adidas"
    assert result["price"] == 2500.0
    assert result["discount_price"] == 1250.0
    assert result["discount_percent"] == 50
    assert result["in_stock"] is True


@patch("curl_cffi.requests.get")
def test_parse_product_not_found(mock_get):
    """Verify parser returns structured failure dict when product is not found."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"products": []}}
    mock_get.return_value = mock_response

    parser = WildberriesParser()
    result = parser.parse_product("99999999")

    assert result["success"] is False
    assert "Товар не найден" in result["error"]


def test_to_markdown():
    """Verify parser output formats correctly into Markdown."""
    parser = WildberriesParser()
    product_data = {
        "success": True,
        "article": "12345678",
        "name": "Футболка",
        "brand": "Nike",
        "brand_id": 987,
        "price": 3000.0,
        "discount_price": 1500.0,
        "discount_percent": 50,
        "rating": 4.9,
        "feedbacks": 80,
        "in_stock": True,
    }

    markdown = parser.to_markdown(product_data)

    assert "# 🛍️ Товар WB: Футболка" in markdown
    assert "**Артикул:** `12345678`" in markdown
    assert " Nike" in markdown
    assert "3,000.00" in markdown
    assert "1,500.00" in markdown
    assert "50%" in markdown
    assert "В наличии" in markdown
