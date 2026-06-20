#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RULES_FILES = [
    WORKSPACE_ROOT / "CLAUDE.md",
    WORKSPACE_ROOT / "AGENTS.md",
    WORKSPACE_ROOT / ".cursorrules",
]

def check_file_links() -> bool:
    """Проверяет работоспособность всех локальных ссылок file:/// в файлах правил."""
    has_errors = False
    # Регулярное выражение для поиска ссылок file:///Users/rus/ai-tools/...
    # Пример: file:///Users/rus/ai-tools/skills/stealth-scraping/SKILL.md
    link_pattern = re.compile(r'file:///Users/rus/ai-tools/([^\s\)\#\"\'\>]+)')

    for rule_file in RULES_FILES:
        if not rule_file.exists():
            continue
        
        content = rule_file.read_text(encoding="utf-8")
        matches = link_pattern.findall(content)
        
        for rel_path_str in matches:
            # Убираем возможные trailing знаки пунктуации из регулярки
            rel_path_str = rel_path_str.split('#')[0] # Игнорируем якоря строк типа #L10
            target_path = WORKSPACE_ROOT / rel_path_str
            
            if not target_path.exists():
                print(f"[ERROR] Битая ссылка в {rule_file.name}: file:///Users/rus/ai-tools/{rel_path_str}", file=sys.stderr)
                has_errors = True
                
    return not has_errors

def check_jit_skills() -> bool:
    """Проверяет синхронизацию папок в skills/ и записей JIT-навыков в CLAUDE.md."""
    claude_file = WORKSPACE_ROOT / "CLAUDE.md"
    skills_dir = WORKSPACE_ROOT / "skills"
    
    if not claude_file.exists() or not skills_dir.exists():
        return True
        
    # Находим все папки в skills/, где есть SKILL.md
    actual_skills = set()
    for item in skills_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            actual_skills.add(item.name)
            
    # Читаем CLAUDE.md и ищем упомянутые навыки в разделе JIT-skills
    content = claude_file.read_text(encoding="utf-8")
    
    # Регулярка ищет ссылки вида [skills/имя-навыка/SKILL.md]
    mentioned_skills = set(re.findall(r'skills/([^/]+)/SKILL.md', content))
    
    has_errors = False
    # Навыки, которые есть физически, но не описаны в CLAUDE.md
    missing_in_claude = actual_skills - mentioned_skills
    if missing_in_claude:
        print(f"[ERROR] Навыки есть на диске, но отсутствуют в CLAUDE.md: {', '.join(missing_in_claude)}", file=sys.stderr)
        has_errors = True
        
    # Навыки, которые описаны в CLAUDE.md, но отсутствуют на диске
    missing_on_disk = mentioned_skills - actual_skills
    if missing_on_disk:
        print(f"[ERROR] Навыки упомянуты в CLAUDE.md, но отсутствуют в skills/: {', '.join(missing_on_disk)}", file=sys.stderr)
        has_errors = True
        
    return not has_errors

def main():
    success = True
    print("=== Проверка целостности регламентов и ссылок ===")
    
    if not check_file_links():
        success = False
        
    if not check_jit_skills():
        success = False
        
    if success:
        print("OK: Все ссылки целы, JIT-навыки синхронизированы.")
        sys.exit(0)
    else:
        print("FAIL: Найдены ошибки в регламентах.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
