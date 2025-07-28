#!/usr/bin/env python3
# test_tool_filtering.py

import pandas as pd
import sys
import os

# Добавляем путь к модулям приложения
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.adapters.llm_client import LLMClient
from app.tools.tool_selector import SimpleToolSelector
from app.tools.keyword_search_tool import filter_risks_by_keywords


def create_test_dataframe() -> pd.DataFrame:
    """
    Создает тестовый DataFrame с примерами рисков проектов.
    """
    test_data = [
        {
            'project_id': 'PROJ-001',
            'project_type': 'niokr',
            'project_name': 'Разработка ИИ системы',
            'risk_text': 'Задержка в разработке алгоритма машинного обучения может привести к срыву сроков проекта',
            'risk_priority': 'высокий',
            'status': 'активный'
        },
        {
            'project_id': 'PROJ-002', 
            'project_type': 'product_project',
            'project_name': 'Мобильное приложение',
            'risk_text': 'Недостаток тестирования может привести к багам в продакшене и потере пользователей',
            'risk_priority': 'средний',
            'status': 'активный'
        },
        {
            'project_id': 'PROJ-003',
            'project_type': 'manufacturing',
            'project_name': 'Производство компонентов',
            'risk_text': 'Поломка оборудования может остановить производственную линию на несколько дней',
            'risk_priority': 'критический',
            'status': 'активный'
        },
        {
            'project_id': 'PROJ-004',
            'project_type': 'niokr',
            'project_name': 'Исследование материалов',
            'risk_text': 'Нехватка бюджета на закупку дорогостоящих материалов для исследований',
            'risk_priority': 'высокий',
            'status': 'активный'
        },
        {
            'project_id': 'PROJ-005',
            'project_type': 'product_project',
            'project_name': 'Веб-платформа',
            'risk_text': 'Неопределенность в требованиях клиента может привести к переработкам и увеличению стоимости',
            'risk_priority': 'средний',
            'status': 'на рассмотрении'
        },
        {
            'project_id': 'PROJ-006',
            'project_type': 'manufacturing',
            'project_name': 'Автоматизация склада',
            'risk_text': 'Сложность интеграции с существующими системами управления складом',
            'risk_priority': 'средний',
            'status': 'активный'
        }
    ]
    
    return pd.DataFrame(test_data)


def test_tool_filtering_interactive():
    """
    Интерактивный тест системы фильтрации через OpenAI function calling.
    """
    print("🧪 Тест системы фильтрации рисков через OpenAI function calling")
    print("=" * 60)
    
    # Создаем тестовые данные
    print("📊 Создание тестового DataFrame...")
    df = create_test_dataframe()
    print(f"Создано {len(df)} тестовых записей рисков")
    print()
    
    # Показываем все риски
    print("📋 Все доступные риски:")
    for idx, row in df.iterrows():
        print(f"{idx+1}. [{row['project_name']}] {row['risk_text'][:80]}...")
    print()
    
    # Инициализируем компоненты
    print("🔧 Инициализация LLM клиента и селектора...")
    try:
        llm_client = LLMClient()
        tool_selector = SimpleToolSelector(llm_client)
        print("✅ Компоненты инициализированы успешно")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return
    
    print()
    
    # Интерактивный цикл
    while True:
        print("💬 Введите ваш запрос (или 'exit' для выхода):")
        user_input = input("> ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'выход']:
            print("👋 До свидания!")
            break
            
        if not user_input:
            print("⚠️ Пустой запрос, попробуйте еще раз")
            continue
        
        print()
        print(f"🔍 Обработка запроса: '{user_input}'")
        print("-" * 40)
        
        try:
            # ШАГ 1: Извлечение ключевых слов через LLM + function calling
            print("1️⃣ Извлечение ключевых слов через LLM...")
            keywords = tool_selector.extract_keywords(user_input)
            print(f"   Извлечены ключевые слова: {keywords}")
            
            if not keywords:
                print("⚠️ Не удалось извлечь ключевые слова")
                continue
            
            # ШАГ 2: Фильтрация DataFrame
            print("2️⃣ Фильтрация рисков по ключевым словам...")
            filtered_df = filter_risks_by_keywords(df, keywords, top_n=3)
            
            # ШАГ 3: Вывод результатов
            print("3️⃣ Результаты фильтрации:")
            
            if filtered_df.empty:
                print("   🚫 Не найдено подходящих рисков")
            else:
                print(f"   🎯 Найдено {len(filtered_df)} подходящих рисков:")
                print()
                
                for idx, (_, row) in enumerate(filtered_df.iterrows(), 1):
                    relevance = row.get('keyword_relevance_score', 0.0)
                    print(f"   {idx}. [{row['project_name']}] (релевантность: {relevance:.2f})")
                    print(f"      💡 {row['risk_text']}")
                    print(f"      🔖 Приоритет: {row['risk_priority']} | Статус: {row['status']}")
                    print()
            
        except Exception as e:
            print(f"❌ Ошибка при обработке: {e}")
        
        print("=" * 60)
        print()


if __name__ == "__main__":
    test_tool_filtering_interactive()