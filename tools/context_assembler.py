import os
from pathlib import Path


class ContextAssembler:
    """
    Cache-Aware Context Assembler.
    Собирает контекст для LLM в строго упорядоченном виде для максимизации
    эффективности Prompt Caching (Core System -> Mode Skills -> Dynamic Data).
    """

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            self.workspace_root = Path(os.getcwd())
        else:
            self.workspace_root = workspace_root

    def _filter_rules(self, content: str, keywords: set[str]) -> str:
        """Фильтрует правила AGENTS.md, оставляя только релевантные и критические."""
        always_keep_patterns = [
            "solo loop",
            "formatting",
            "форматирование ссылок",
            "pathjail",
            "security",
        ]
        lines = content.splitlines()
        filtered_lines = []

        # 1. Извлекаем заголовок (до первого "##")
        header_lines = []
        idx = 0
        while idx < len(lines) and not lines[idx].startswith("##"):
            header_lines.append(lines[idx])
            idx += 1
        filtered_lines.extend(header_lines)

        # 2. Обрабатываем разделы
        current_section = None
        section_buffer = []

        def flush_section():
            nonlocal current_section, section_buffer
            if not current_section:
                return

            kept_items = []
            current_item = []
            for line in section_buffer:
                if line.strip().startswith("-"):
                    if current_item:
                        kept_items.append(current_item)
                    current_item = [line]
                elif line.strip() == "" and current_item:
                    kept_items.append(current_item)
                    current_item = []
                elif current_item:
                    current_item.append(line)
                else:
                    kept_items.append([line])
            if current_item:
                kept_items.append(current_item)

            section_kept_lines = []
            for item in kept_items:
                item_text = "\n".join(item).lower()
                keep = any(pat in item_text for pat in always_keep_patterns)
                if not keep:
                    for kw in keywords:
                        if len(kw) >= 2 and kw in item_text:
                            keep = True
                            break
                # Если это не списочный элемент (например, описание раздела), оставляем
                if not keep and not any(
                    line_item.strip().startswith("-") for line_item in item
                ):
                    keep = True

                if keep:
                    section_kept_lines.extend(item)

            if section_kept_lines:
                filtered_lines.append(current_section)
                filtered_lines.extend(section_kept_lines)

        while idx < len(lines):
            line = lines[idx]
            if line.startswith("##"):
                flush_section()
                current_section = line
                section_buffer = []
            else:
                section_buffer.append(line)
            idx += 1
        flush_section()

        return "\n".join(filtered_lines)

    def assemble_context(
        self, dynamic_data: str, active_skills: list[str] | None = None
    ) -> str:
        """
        Собирает полный контекст.

        Порядок сборки (от стабильного к динамическому):
        1. Core System: системный промпт + глобальные правила AGENTS.md
        2. Mode Skills: стандарты стандарты standards.md + активные JIT-навыки
        3. Dynamic Data: текущие логи, ошибки, пользовательский ввод
        """
        import re

        # Извлекаем ключевые слова для Context Surface Hook
        task_text = dynamic_data.lower()
        keywords = set(re.findall(r"[a-zа-я0-9\-_]+", task_text))
        if active_skills:
            for skill in active_skills:
                keywords.update(re.findall(r"[a-zа-я0-9\-_]+", skill.lower()))

        blocks = []

        # === 1. CORE SYSTEM (Стабильный префикс) ===
        # Системный промпт
        sys_prompt_path = self.workspace_root / "tools" / "hermes_system_prompt.md"
        if sys_prompt_path.exists():
            try:
                blocks.append(
                    f"=== SYSTEM PROMPT ===\n{sys_prompt_path.read_text(encoding='utf-8')}"
                )
            except Exception:
                pass
        else:
            blocks.append(
                "=== SYSTEM PROMPT ===\nYou are Antigravity, a powerful AI coding assistant."
            )

        # Глобальные правила (фильтруем с помощью Context Surface Hook)
        agents_md_path = self.workspace_root / "tools" / "AGENTS.md"
        if not agents_md_path.exists():
            agents_md_path = self.workspace_root / "AGENTS.md"

        if agents_md_path.exists():
            try:
                raw_rules = agents_md_path.read_text(encoding="utf-8")
                filtered_rules = self._filter_rules(raw_rules, keywords)
                blocks.append(f"=== GLOBAL RULES ===\n{filtered_rules}")
            except Exception:
                pass

        # === 2. MODE SKILLS (Полустабильный блок) ===
        # Стандарты проекта
        standards_path = self.workspace_root / "vault" / "standards.md"
        if standards_path.exists():
            try:
                blocks.append(
                    f"=== PROJECT STANDARDS ===\n{standards_path.read_text(encoding='utf-8')}"
                )
            except Exception:
                pass

        # JIT-навыки
        if active_skills:
            skills_dir = self.workspace_root / "skills"
            for skill_name in active_skills:
                # Нормализуем имя папки
                normalized = (
                    skill_name.strip().lower().replace("_", "-").replace(" ", "-")
                )
                skill_md = skills_dir / normalized / "SKILL.md"
                if skill_md.exists():
                    try:
                        blocks.append(
                            f"=== JIT SKILL: {normalized} ===\n{skill_md.read_text(encoding='utf-8')}"
                        )
                    except Exception:
                        pass

        # === 3. DYNAMIC DATA (Полностью динамический слой) ===
        blocks.append(f"=== DYNAMIC CONTEXT & TASK ===\n{dynamic_data}")

        # Объединяем блоки с разделителями
        return "\n\n".join(blocks)
