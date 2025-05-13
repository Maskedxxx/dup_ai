# API Examples

## Подрядчики

### Поиск подрядчиков по типу работ
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Найди подрядчиков для дорожного строительства",
       "button": "contractors"
     }'
```

### Поиск подрядчиков с ограничением результатов
```bash
curl -X POST "http://localhost:8080/v1/ask?limit=5" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Покажи всех подрядчиков по мостовым работам",
       "button": "contractors"
     }'
```

## Риски проектов

### Риски НИОКР проектов
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Какие риски есть в проекте по разработке нового ПО?",
       "button": "risks",
       "risk_category": "niokr"
     }'
```

### Риски производственных проектов
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Основные риски при запуске нового производства",
       "button": "risks", 
       "risk_category": "manufacturing"
     }'
```

## Ошибки проектов

### Поиск ошибок по проекту
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Какие ошибки были в проекте строительства моста?",
       "button": "errors"
     }'
```

### Анализ типовых ошибок
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Покажи самые частые ошибки в строительных проектах",
       "button": "errors"
     }'
```

## Бизнес-процессы

### Поиск процессов по названию
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Найди процесс закупки материалов",
       "button": "processes"
     }'
```

### Поиск процессов по описанию
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Какие процессы связаны с контролем качества?",
       "button": "processes"
     }'
```

## Python примеры

### Простой клиент
```python
import requests
import json

class ContractorAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        
    def ask(self, question, button, risk_category=None, limit=None):
        """Отправляет запрос к API."""
        url = f"{self.base_url}/v1/ask"
        
        # Добавляем параметр limit если указан
        if limit:
            url += f"?limit={limit}"
            
        payload = {
            "question": question,
            "button": button
        }
        
        # Добавляем категорию риска если указана
        if risk_category:
            payload["risk_category"] = risk_category
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def find_contractors(self, question, limit=None):
        """Ищет подрядчиков."""
        return self.ask(question, "contractors", limit=limit)
    
    def analyze_risks(self, question, category):
        """Анализирует риски проектов."""
        return self.ask(question, "risks", risk_category=category)
    
    def find_errors(self, question):
        """Ищет ошибки в проектах."""
        return self.ask(question, "errors")
    
    def find_processes(self, question):
        """Ищет бизнес-процессы."""
        return self.ask(question, "processes")

# Использование
client = ContractorAPIClient()

# Поиск подрядчиков
result = client.find_contractors("Найди подрядчиков для дорожных работ", limit=5)
print(f"Найдено: {result['total_found']} подрядчиков")
for item in result['items']:
    print(f"- {item['name']}: {item['work_types']}")

# Анализ рисков
risks = client.analyze_risks("Риски разработки ПО", "niokr")
print(risks['text'])

# Поиск ошибок
errors = client.find_errors("Ошибки в проекте Альфа")
for error in errors['items']:
    print(f"- {error['description']} ({error['project']})")
```

### Асинхронный клиент
```python
import aiohttp
import asyncio

class AsyncContractorAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    async def ask(self, question, button, **kwargs):
        """Асинхронный запрос к API."""
        url = f"{self.base_url}/v1/ask"
        params = {}
        
        if 'limit' in kwargs:
            params['limit'] = kwargs.pop('limit')
            
        payload = {
            "question": question,
            "button": button,
            **kwargs
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, params=params) as resp:
                return await resp.json()
    
    async def batch_requests(self, requests):
        """Выполняет несколько запросов параллельно."""
        tasks = []
        for req in requests:
            task = self.ask(**req)
            tasks.append(task)
            
        return await asyncio.gather(*tasks)

# Использование
async def main():
    client = AsyncContractorAPIClient()
    
    # Параллельные запросы
    requests = [
        {"question": "Подрядчики для дорог", "button": "contractors"},
        {"question": "Риски НИОКР", "button": "risks", "risk_category": "niokr"},
        {"question": "Ошибки проекта Альфа", "button": "errors"}
    ]
    
    results = await client.batch_requests(requests)
    
    for i, result in enumerate(results):
        print(f"Запрос {i+1}: найдено {result['total_found']} элементов")

# Запуск
asyncio.run(main())
```

## Полезные команды

### Проверка доступности API
```bash
curl http://localhost:8080/v1/health
```

### Красивый вывод JSON
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "test", "button": "contractors"}' \
     | python -m json.tool
```

### Сохранение результата в файл
```bash
curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "Все подрядчики", "button": "contractors"}' \
     -o contractors.json
```

### Измерение времени ответа
```bash
time curl -X POST "http://localhost:8080/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "test", "button": "contractors"}'
```