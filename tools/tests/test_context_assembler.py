from pathlib import Path

from tools.context_assembler import ContextAssembler


def test_context_assembler_ordering():
    # Создаем временную директорию внутри tools/tests, чтобы пройти PathJail
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_assembler_dir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Инициализируем структуру папок
    tools_dir = tmp_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    skills_dir = tmp_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Записываем файлы
    sys_prompt = tools_dir / "hermes_system_prompt.md"
    sys_prompt.write_text("System behavior details", encoding="utf-8")

    agents_md = tools_dir / "AGENTS.md"
    agents_md.write_text("Global styling and behavior constraints", encoding="utf-8")

    standards = vault_dir / "standards.md"
    standards.write_text("Python guidelines", encoding="utf-8")

    skill_folder = skills_dir / "test-skill"
    skill_folder.mkdir(parents=True, exist_ok=True)
    skill_md = skill_folder / "SKILL.md"
    skill_md.write_text("Skill actions here", encoding="utf-8")

    try:
        assembler = ContextAssembler(workspace_root=tmp_dir)
        context = assembler.assemble_context(
            dynamic_data="Error trace line 42", active_skills=["test-skill"]
        )

        # Проверяем наличие всех секций
        assert "=== SYSTEM PROMPT ===" in context
        assert "=== GLOBAL RULES ===" in context
        assert "=== PROJECT STANDARDS ===" in context
        assert "=== JIT SKILL: test-skill ===" in context
        assert "=== DYNAMIC CONTEXT & TASK ===" in context

        # Проверяем строгий порядок (индексы секций в строке)
        idx_sys = context.index("=== SYSTEM PROMPT ===")
        idx_rules = context.index("=== GLOBAL RULES ===")
        idx_standards = context.index("=== PROJECT STANDARDS ===")
        idx_skill = context.index("=== JIT SKILL: test-skill ===")
        idx_dynamic = context.index("=== DYNAMIC CONTEXT & TASK ===")

        # Core System -> Mode Skills -> Dynamic Data
        assert idx_sys < idx_rules
        assert idx_rules < idx_standards
        assert idx_standards < idx_skill
        assert idx_skill < idx_dynamic

        # Проверяем контент внутри секций
        assert "System behavior details" in context
        assert "Global styling and behavior constraints" in context
        assert "Python guidelines" in context
        assert "Skill actions here" in context
        assert "Error trace line 42" in context

    finally:
        # Очистка файлов
        if sys_prompt.exists():
            sys_prompt.unlink()
        if agents_md.exists():
            agents_md.unlink()
        if standards.exists():
            standards.unlink()
        if skill_md.exists():
            skill_md.unlink()
        if skill_folder.exists():
            skill_folder.rmdir()

        # Очистка папок
        for d in (tools_dir, vault_dir, skills_dir, tmp_dir):
            if d.exists():
                try:
                    d.rmdir()
                except Exception:
                    pass


def test_context_assembler_rules_filtering():
    tmp_dir = Path("/Users/rus/ai-tools/tools/tests/tmp_assembler_dir2")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    tools_dir = tmp_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    agents_md = tools_dir / "AGENTS.md"
    agents_md.write_text(
        """# 📐 Локальные правила разработки

## 📐 Регламенты
- **Solo Loop**: Критическое правило.
- **Дизайн-системы**: Правило про UI стили.
- **Другое**: Обычное правило о Typst.
""",
        encoding="utf-8",
    )

    try:
        assembler = ContextAssembler(workspace_root=tmp_dir)

        # Сценарий 1: Задача про UI
        context_ui = assembler.assemble_context(dynamic_data="Настроить красивый UI")
        assert "Solo Loop" in context_ui  # Всегда сохраняется (always_keep)
        assert "Дизайн-системы" in context_ui  # Сохраняется из-за UI совпадения
        assert "Другое" not in context_ui  # Фильтруется

        # Сценарий 2: Задача про Typst
        context_typst = assembler.assemble_context(dynamic_data="Сделать отчет Typst")
        assert "Solo Loop" in context_typst
        assert "Дизайн-системы" not in context_typst
        assert "Другое" in context_typst

    finally:
        if agents_md.exists():
            agents_md.unlink()
        for d in (tools_dir, tmp_dir):
            if d.exists():
                try:
                    d.rmdir()
                except Exception:
                    pass
