#!/usr/bin/env python3
"""
Универсальный тестовый скрипт для проверки всех пайплайнов с новой конфигурацией.
Позволяет тестировать любую кнопку и подкатегорию с произвольным вопросом.
"""

import sys
import os
from typing import Optional

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.domain.enums import ButtonType, RiskCategory
from app.api.v1.schemas import AskRequest
from app.pipelines import get_pipeline, init_container
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

def test_pipeline(button: str, question: str, risk_category: Optional[str] = None):
    """
    Тестирует пайплайн для указанной кнопки и вопроса.
    
    :param button: Тип кнопки (contractors, risks, errors, processes)
    :param question: Вопрос пользователя
    :param risk_category: Категория риска (только для button=risks)
    """
    print("Тестирование пайплайна")
    print("=" * 80)
    
    try:
        # Преобразуем строки в енумы
        button_type = ButtonType(button.lower())
        risk_cat = RiskCategory(risk_category.lower()) if risk_category else None
        
        # Создаем запрос
        request = AskRequest(
            question=question,
            button=button_type,
            risk_category=risk_cat
        )
        
        print("📝 Параметры запроса:")
        print(f"   • Кнопка: {request.button.value}")
        print(f"   • Вопрос: {request.question}")
        if request.risk_category:
            print(f"   • Категория риска: {request.risk_category.value}")
        
        # Получаем пайплайн
        print("\n🔧 Создание пайплайна...")
        pipeline = get_pipeline(request.button, request.risk_category)
        print(f"   ✅ Пайплайн создан: {type(pipeline).__name__}")
        
        # Тестируем новую конфигурацию классификации
        print("\n🧪 Проверка конфигурации классификации:")
        classifier = pipeline.classifier_service
        print(f"   • Колонка для классификации: {classifier.get_column_name()}")
        print(f"   • Тип элемента: {classifier.get_item_type()}")
        
        # Запускаем обработку
        print("\n⚙️ Запуск пайплайна...")
        
        if request.button == ButtonType.RISKS:
            result = pipeline.process(request.question, risk_category=request.risk_category)
        else:
            result = pipeline.process(request.question)
        
        # Выводим результаты
        print("\n📊 Результаты обработки:")
        print(f"   • Найдено элементов: {len(result.items)}")
        print(f"   • Общее количество: {result.total_found}")
        
        if hasattr(result, 'category') and result.category:
            print(f"   • Категория: {result.category}")
        
        print("   • Текст ответа:")
        print(f"     {result.text[:300]}{'...' if len(result.text) > 300 else ''}")
        
        if result.items:
            print("\n🎯 Первые 3 найденных элемента:")
            for i, item in enumerate(result.items[:3], 1):
                print(f"   {i}. {_format_item(item, request.button)}")
                if hasattr(item, 'relevance_score') and item.relevance_score:
                    print(f"      Релевантность: {item.relevance_score:.2f}")
        
        print("\n✅ Тестирование успешно завершено!")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        print(f"❌ Ошибка: {e}")
        
        import traceback
        print("\n🔍 Подробная информация об ошибке:")
        traceback.print_exc()

def _format_item(item, button_type: ButtonType) -> str:
    """Форматирует элемент для вывода в зависимости от типа."""
    if button_type == ButtonType.CONTRACTORS:
        return f"Подрядчик: {item.name} | Виды работ: {item.work_types}"
    elif button_type == ButtonType.RISKS:
        return f"Проект: {item.project_name} | Риск: {item.risk_text[:100]}..."
    elif button_type == ButtonType.ERRORS:
        return f"Проект: {item.project_name} | Ошибка: {item.error_description[:100]}..."
    elif button_type == ButtonType.PROCESSES:
        return f"Процесс: {item.name} | Описание: {item.description[:100]}..."
    else:
        return str(item)

def show_help():
    """Показывает справку по использованию."""
    print("📖 Справка по использованию скрипта:")
    print("=" * 50)
    print()
    print("Доступные кнопки:")
    print("  • contractors  - Подрядчики")
    print("  • risks        - Риски")
    print("  • errors       - Ошибки")
    print("  • processes    - Процессы")
    print()
    print("Доступные категории рисков (только для button=risks):")
    print("  • manufacturing    - Производственные проекты")
    print("  • niokr           - НИОКР проекты")
    print("  • product_project - Продуктовые проекты")
    print()
    print("Примеры запуска:")
    print("  python test_universal_pipeline.py")
    print("  > Кнопка: risks")
    print("  > Вопрос: Основные риски производства")
    print("  > Категория риска: manufacturing")
    print()

def interactive_test():
    """Интерактивный режим тестирования."""
    print("🎮 Интерактивный режим тестирования пайплайнов")
    print("=" * 60)
    
    while True:
        try:
            # Ввод параметров
            print("\n📝 Введите параметры для тестирования:")
            
            button = input("Кнопка (contractors/risks/errors/processes): ").strip().lower()
            if not button:
                print("❌ Кнопка не может быть пустой")
                continue
                
            if button not in ['contractors', 'risks', 'errors', 'processes']:
                print("❌ Неизвестная кнопка. Доступны: contractors, risks, errors, processes")
                continue
            
            question = input("Вопрос: ").strip()
            if not question:
                print("❌ Вопрос не может быть пустым")
                continue
            
            risk_category = None
            if button == 'risks':
                risk_cat_input = input("Категория риска (manufacturing/niokr/product_project, или Enter для пропуска): ").strip().lower()
                if risk_cat_input and risk_cat_input in ['manufacturing', 'niokr', 'product_project']:
                    risk_category = risk_cat_input
                elif risk_cat_input:
                    print("❌ Неизвестная категория. Доступны: manufacturing, niokr, product_project")
                    continue
            
            print("\n" + "="*80)
            
            # Запуск теста
            test_pipeline(button, question, risk_category)
            
            # Продолжить?
            print("\n" + "="*80)
            continue_test = input("\n🔄 Продолжить тестирование? (y/n): ").strip().lower()
            if continue_test != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Тестирование прервано пользователем")
            break
        except Exception as e:
            print(f"\n❌ Ошибка во время ввода: {e}")

def main():
    """Главная функция."""
    print("🎯 Универсальный тестер пайплайнов с новой конфигурацией классификации")
    print("=" * 80)
    
    # Инициализируем контейнер зависимостей
    print("🔧 Инициализация контейнера зависимостей...")
    try:
        init_container()
        print("✅ Контейнер инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_help()
            return
        
        # Режим с аргументами
        try:
            button = sys.argv[1]
            question = sys.argv[2] if len(sys.argv) > 2 else "Тестовый вопрос"
            risk_category = sys.argv[3] if len(sys.argv) > 3 else None
            
            print("\n Режим с аргументами:")
            test_pipeline(button, question, risk_category)
        except IndexError:
            print("❌ Недостаточно аргументов. Используйте: python script.py <button> <question> [risk_category]")
            show_help()
    else:
        # Интерактивный режим
        interactive_test()
    
    print("\n🏁 Программа завершена!")

if __name__ == "__main__":
    main()
