import json
import time
from functools import wraps

from deepdiff import DeepDiff
from rustdeepdiff import compare as rust_compare


def time_elapsed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time} seconds")
        return result

    return wrapper


def load_json(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@time_elapsed
def test_rust_deep_diff():
    # Пример 1: Сравнение словарей
    dict1 = load_json("dict1.json")
    dict2 = load_json("dict2.json")

    diff = rust_compare(dict1, dict2)
    return diff


@time_elapsed
def test_python_deep_diff():
    dict1 = load_json("dict1.json")
    dict2 = load_json("dict2.json")

    diff = DeepDiff(dict1, dict2)
    return diff


def generate_large_json_examples():
    """Генерирует два больших JSON-файла с некоторыми различиями для тестирования."""
    # Создаем базовую структуру данных
    base_data = {
        "users": [],
        "products": [],
        "transactions": [],
        "settings": {
            "notification_preferences": {},
            "system_config": {
                "timeout": 30,
                "retry_attempts": 3,
                "logging_level": "info"
            }
        }
    }
    
    # Заполняем первый словарь
    dict1 = base_data.copy()
    
    # Генерируем пользователей
    for i in range(1000):
        user = {
            "id": i,
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "age": 20 + (i % 50),
            "active": i % 7 != 0,
            "metadata": {
                "last_login": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "preferences": {
                    "theme": "light" if i % 2 == 0 else "dark",
                    "language": "en" if i % 3 == 0 else ("fr" if i % 3 == 1 else "de"),
                    "notifications": ["email", "sms"] if i % 4 == 0 else ["email"]
                }
            }
        }
        dict1["users"].append(user)
    
    # Генерируем продукты
    for i in range(500):
        product = {
            "id": i,
            "name": f"Product {i}",
            "price": 10.0 + (i % 100),
            "stock": i * 5,
            "categories": [f"category_{j}" for j in range(1, (i % 5) + 2)],
            "attributes": {
                "color": ["red", "blue", "green"][i % 3],
                "size": ["S", "M", "L", "XL"][i % 4],
                "weight": 0.5 + (i % 10) / 10
            }
        }
        dict1["products"].append(product)
    
    # Генерируем транзакции
    for i in range(2000):
        transaction = {
            "id": i,
            "user_id": i % 1000,
            "product_ids": [(i + j) % 500 for j in range(1, (i % 5) + 2)],
            "total": 50.0 + (i % 200),
            "date": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "status": ["completed", "pending", "failed"][i % 3]
        }
        dict1["transactions"].append(transaction)
    
    # Настройки уведомлений
    for i in range(20):
        dict1["settings"]["notification_preferences"][f"event_{i}"] = {
            "email": i % 2 == 0,
            "sms": i % 3 == 0,
            "push": i % 4 == 0
        }
    
    # Создаем второй словарь с некоторыми изменениями
    dict2 = json.loads(json.dumps(dict1))  # Глубокое копирование через сериализацию
    
    # Вносим изменения в dict2
    
    # 1. Изменяем некоторых пользователей
    for i in range(0, 1000, 10):
        if i < len(dict2["users"]):
            dict2["users"][i]["active"] = not dict2["users"][i]["active"]
            dict2["users"][i]["age"] += 1
            dict2["users"][i]["metadata"]["preferences"]["theme"] = "custom"
    
    # 2. Добавляем новых пользователей
    for i in range(1000, 1050):
        user = {
            "id": i,
            "name": f"New User {i}",
            "email": f"newuser{i}@example.com",
            "age": 25 + (i % 40),
            "active": True,
            "metadata": {
                "last_login": f"2023-12-{(i % 28) + 1:02d}",
                "preferences": {
                    "theme": "system",
                    "language": "es",
                    "notifications": ["email", "push"]
                }
            }
        }
        dict2["users"].append(user)
    
    # 3. Удаляем некоторых пользователей
    dict2["users"] = [user for user in dict2["users"] if user["id"] % 97 != 0]
    
    # 4. Изменяем цены некоторых продуктов
    for product in dict2["products"]:
        if product["id"] % 5 == 0:
            product["price"] *= 1.1  # Увеличиваем цену на 10%
            product["stock"] -= 2    # Уменьшаем запас
    
    # 5. Добавляем новую категорию настроек
    dict2["settings"]["performance_tuning"] = {
        "cache_size": 1024,
        "worker_threads": 8,
        "compression": True
    }
    
    # 6. Изменяем некоторые системные настройки
    dict2["settings"]["system_config"]["timeout"] = 45
    dict2["settings"]["system_config"]["new_option"] = "enabled"
    
    # Сохраняем словари в файлы
    with open("dict1.json", "w", encoding="utf-8") as f:
        json.dump(dict1, f, indent=2)
    
    with open("dict2.json", "w", encoding="utf-8") as f:
        json.dump(dict2, f, indent=2)
    
    print(f"Сгенерированы файлы dict1.json и dict2.json")
    print(f"Размер dict1.json: {len(json.dumps(dict1))} байт")
    print(f"Размер dict2.json: {len(json.dumps(dict2))} байт")


def run_benchmarks(iterations=3, output_file=None):
    """Запускает тесты производительности несколько раз и выводит среднее время."""
    results = []  # Для сохранения результатов
    
    header = "\n" + "="*50 + "\nЗАПУСК ТЕСТОВ ПРОИЗВОДИТЕЛЬНОСТИ\n" + "="*50
    print(header)
    results.append(header)
    
    rust_times = []
    python_times = []
    
    for i in range(iterations):
        iter_result = f"\nИтерация {i+1}/{iterations}:"
        print(iter_result)
        results.append(iter_result)
        
        # Тест Rust deep_diff
        start_time = time.time()
        diff1 = test_rust_deep_diff()
        end_time = time.time()
        rust_time = end_time - start_time
        rust_times.append(rust_time)
        
        # Тест Python DeepDiff
        start_time = time.time()
        diff2 = test_python_deep_diff()
        end_time = time.time()
        python_time = end_time - start_time
        python_times.append(python_time)
        
        # Вывод результатов итерации
        iter_results = [
            f"  Rust deep_diff: {rust_time:.4f} сек",
            f"  Python DeepDiff: {python_time:.4f} сек",
            f"  Ускорение: {python_time/rust_time:.2f}x"
        ]
        
        for line in iter_results:
            print(line)
            results.append(line)
    
    # Вычисляем средние значения
    avg_rust = sum(rust_times) / len(rust_times)
    avg_python = sum(python_times) / len(python_times)
    
    summary_header = "\n" + "="*50 + "\nИТОГОВЫЕ РЕЗУЛЬТАТЫ\n" + "="*50
    print(summary_header)
    results.append(summary_header)
    
    summary_results = [
        f"Среднее время Rust deep_diff: {avg_rust:.4f} сек",
        f"Среднее время Python DeepDiff: {avg_python:.4f} сек",
        f"Среднее ускорение: {avg_python/avg_rust:.2f}x"
    ]
    
    for line in summary_results:
        print(line)
        results.append(line)
    
    # Сохраняем результаты в файл, если указан
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
            f.write('\n\n')
            
            # Добавляем информацию о системе
            import platform
            import sys
            
            f.write("="*50 + "\n")
            f.write("ИНФОРМАЦИЯ О СИСТЕМЕ\n")
            f.write("="*50 + "\n")
            f.write(f"Операционная система: {platform.system()} {platform.release()}\n")
            f.write(f"Python версия: {sys.version}\n")
            f.write(f"Процессор: {platform.processor()}\n")
            f.write(f"Архитектура: {platform.architecture()[0]}\n")
            f.write(f"Дата и время теста: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Возвращаем последние результаты для анализа
    return diff1, diff2


def analyze_differences(diff1, diff2, output_file=None):
    """Анализирует и выводит информацию о различиях, найденных обоими алгоритмами."""
    results = []
    
    header = "\n" + "="*50 + "\nАНАЛИЗ РАЗЛИЧИЙ\n" + "="*50
    print(header)
    results.append(header)
    
    # Анализ результатов Rust deep_diff
    rust_header = "\nRust deep_diff:"
    print(rust_header)
    results.append(rust_header)
    
    if hasattr(diff1, "keys"):
        rust_summary = f"Обнаружено категорий различий: {len(diff1.keys())}"
        print(rust_summary)
        results.append(rust_summary)
        
        for key in diff1.keys():
            if isinstance(diff1[key], dict):
                line = f"  - {key}: {len(diff1[key])} элементов"
            elif isinstance(diff1[key], list):
                line = f"  - {key}: {len(diff1[key])} элементов"
            else:
                line = f"  - {key}: {type(diff1[key])}"
            print(line)
            results.append(line)
    else:
        line = f"Тип результата: {type(diff1)}"
        print(line)
        results.append(line)
    
    # Анализ результатов Python DeepDiff
    python_header = "\nPython DeepDiff:"
    print(python_header)
    results.append(python_header)
    
    if hasattr(diff2, "to_dict"):
        diff2_dict = diff2.to_dict()
        python_summary = f"Обнаружено категорий различий: {len(diff2_dict.keys())}"
        print(python_summary)
        results.append(python_summary)
        
        for key in diff2_dict.keys():
            if isinstance(diff2_dict[key], dict):
                line = f"  - {key}: {len(diff2_dict[key])} элементов"
            elif isinstance(diff2_dict[key], list):
                line = f"  - {key}: {len(diff2_dict[key])} элементов"
            else:
                line = f"  - {key}: {type(diff2_dict[key])}"
            print(line)
            results.append(line)
    else:
        line = f"Тип результата: {type(diff2)}"
        print(line)
        results.append(line)
    
    # Сохраняем результаты в файл, если указан
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(results))


if __name__ == "__main__":
    output_file = "result.txt"
    
    try:
        generate_large_json_examples()
        diff1, diff2 = run_benchmarks(iterations=3, output_file=output_file)
        analyze_differences(diff1, diff2, output_file=output_file)
        
        print(f"\nРезультаты сохранены в файл: {output_file}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
