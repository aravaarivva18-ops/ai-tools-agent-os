from tools.self_improve import detect_tool_conflicts


def test_detect_tool_conflicts_positive_subagent():
    """
    Позитивный тест: проверка, что детектор конфликтов в self_improve.py
    обнаруживает запрещенные упоминания субагентов в логах трения.
    Это подтверждает автоматический контроль Strict Solo Loop.
    """
    mock_logs = [
        {
            "session_id": "test_session_001",
            "friction_points": [
                {
                    "heading": "Execution Error",
                    "content": "Tried to spawn a subagent to write helper code.",
                }
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    assert len(conflicts) == 1
    assert "test_session_001" in conflicts[0]
    assert "Solo Loop" in conflicts[0]


def test_detect_tool_conflicts_negative_no_conflicts():
    """
    Негативный тест: проверка, что стандартные логи
    без упоминания субагентов или diff_applier не вызывают флагов конфликтов.
    """
    mock_logs = [
        {
            "session_id": "test_session_002",
            "friction_points": [
                {
                    "heading": "Linter Issue",
                    "content": "Fixed imports in test file via replace_file_content.",
                }
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    assert len(conflicts) == 0


def test_detect_tool_conflicts_explicit_subagent_calls():
    """
    Позитивный тест: проверка детекции явных имен вызовов субагентов
    (invoke_subagent и define_subagent) в логах сессии.
    """
    mock_logs = [
        {
            "session_id": "test_session_003",
            "friction_points": [
                {
                    "heading": "API Misuse",
                    "content": "User requested invoke_subagent in chat, but it was blocked.",
                },
                {
                    "heading": "Tool Error",
                    "content": "Tried calling define_subagent manually.",
                },
            ],
        }
    ]

    conflicts = detect_tool_conflicts(mock_logs)
    # Набор set() вернет один объединенный конфликт на сессию
    assert len(conflicts) == 1
    assert "invoke_subagent/define_subagent" in conflicts[0]
