import sys
from importlib import import_module

# Пробуем разные способы импорта модуля Rust
try:
    # Сначала пробуем прямой импорт
    from _rustdeepdiff import DeepDiff, compare
except ImportError:
    try:
        # Затем пробуем импорт через rustdeepdiff
        from rustdeepdiff._rustdeepdiff import DeepDiff, compare
    except ImportError:
        try:
            # Пробуем импорт из основного модуля
            from rustdeepdiff import DeepDiff, compare
        except ImportError:
            # Наконец, пробуем импорт через importlib
            import importlib.util
            import os
            
            # Ищем модуль в разных местах
            module_paths = [
                os.path.dirname(__file__),  # Текущая директория
                os.path.join(os.path.dirname(__file__), "_rustdeepdiff"),  # Поддиректория
                os.path.join(sys.prefix, "lib", "python" + sys.version[:3], "site-packages"),  # site-packages
            ]
            
            module_found = False
            for path in module_paths:
                if os.path.exists(path):
                    for file in os.listdir(path):
                        if file.startswith(("_rustdeepdiff", "rustdeepdiff")) and file.endswith((".so", ".pyd")):
                            spec = importlib.util.spec_from_file_location("_rustdeepdiff", os.path.join(path, file))
                            _rust_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(_rust_module)
                            DeepDiff = _rust_module.DeepDiff
                            compare = _rust_module.compare
                            module_found = True
                            break
                if module_found:
                    break
            
            if not module_found:
                raise ImportError("Не удалось найти модуль rustdeepdiff")

# Определяем функцию deep_diff
def deep_diff(t1, t2):
    """Обертка для функции compare для совместимости"""
    return compare(t1, t2)

# Явно экспортируем все необходимые имена
__all__ = ["DeepDiff", "compare", "deep_diff"]

# Убедимся, что функция deep_diff доступна в глобальном пространстве имен
import sys
sys.modules["rustdeepdiff"].deep_diff = deep_diff
