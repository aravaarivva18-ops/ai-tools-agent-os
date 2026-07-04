import os
import sys
from unittest.mock import MagicMock, patch

# Add tools to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.competitive_analysis_agent import analyze_competitors
from tools.social_media_agent import generate_posts


@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
def test_social_media_agent(mock_configure, mock_model_class):
    # Set mock API key
    os.environ["GEMINI_API_KEY"] = "mock_key"

    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Mocked post content"

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    # Run agent function
    res = generate_posts("Test Topic", brand="TestBrand", platforms=["telegram", "linkedin"])

    # Assertions
    assert "telegram" in res
    assert "linkedin" in res
    assert res["telegram"] == "Mocked post content"
    assert res["linkedin"] == "Mocked post content"

    # Verify mock calls
    mock_configure.assert_called_once_with(api_key="mock_key")
    assert mock_model_instance.generate_content.call_count == 2

@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
def test_competitive_analysis_agent(mock_configure, mock_model_class):
    os.environ["GEMINI_API_KEY"] = "mock_key"

    # Mock behavior: first call for competitors, second call for final report
    mock_response_identify = MagicMock()
    mock_response_identify.text = "CompetitorA, CompetitorB, CompetitorC"

    mock_response_report = MagicMock()
    mock_response_report.text = "Mocked Strategic Report"

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = [mock_response_identify, mock_response_report]
    mock_model_class.return_value = mock_model_instance

    # Run analysis
    report = analyze_competitors("MyCompany", "MyIndustry")

    # Assertions
    assert report == "Mocked Strategic Report"
    assert mock_model_instance.generate_content.call_count == 2
