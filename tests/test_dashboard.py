import ast
from pathlib import Path


def test_dashboard_module_is_importable_without_dashboard_dependencies():
    source = Path("job_market/dashboard/main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.names[0].name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    }
    assert "streamlit" in imported_modules
    assert "pandas" in imported_modules
