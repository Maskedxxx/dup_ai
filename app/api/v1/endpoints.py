# app/api/v1/endpoints.py

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.api.v1.schemas import AskRequest, AskResponse
from app.domain.enums import ButtonType
from app.pipelines import get_pipeline, init_container
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Инициализация контейнера с зависимостями
init_container()

# Создание роутера
router = APIRouter(
    prefix="/v1",
    tags=["API v1"]
)

# Словарь обработчиков для разных типов кнопок
BUTTON_PROCESSORS = {
    ButtonType.CONTRACTORS: lambda pipeline, req: pipeline.process(req.question),
    ButtonType.RISKS: lambda pipeline, req: pipeline.process(req.question, req.risk_category),
    ButtonType.ERRORS: lambda pipeline, req: pipeline.process(req.question),
    ButtonType.PROCESSES: lambda pipeline, req: pipeline.process(req.question),
}

@router.get("/health")
async def health_check():
    """
    Проверка работоспособности API сервиса.
    """
    logger.info("Запрос к эндпоинту health_check")
    return {"status": "Сервис анализа запущен"}

@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    limit: Optional[int] = Query(None, description="Максимальное количество результатов")
):
    """
    Обработка запроса от пользователя.
    
    :param request: Модель запроса с вопросом и типом кнопки
    :param limit: Максимальное количество возвращаемых результатов
    :return: Модель ответа с результатами
    """
    logger.info(f"Обработка запроса: '{request.question}' для кнопки {request.button}")
    
    # Проверяем поддержку типа кнопки
    if request.button not in BUTTON_PROCESSORS:
        logger.error(f"Неподдерживаемый тип кнопки: {request.button}")
        return AskResponse(
            text=f"Неподдерживаемый тип кнопки: {request.button}",
            query=request.question,
            total_found=0,
            items=[]
        )
    
    try:
        # Получаем соответствующий пайплайн
        pipeline = get_pipeline(request.button, request.risk_category)
        logger.debug(f"Используется пайплайн: {pipeline.__class__.__name__}")
        
        # Используем словарь обработчиков для вызова правильного метода
        processor = BUTTON_PROCESSORS[request.button]
        answer = processor(pipeline, request)
        logger.debug("Пайплайн завершил обработку запроса")
        
        # Получаем лимит из конфигурации если не указан
        if limit is None:
            from app.config import contractor_settings, risk_settings, error_settings, process_settings
            
            limits = {
                ButtonType.CONTRACTORS: contractor_settings.max_results,
                ButtonType.RISKS: risk_settings.max_results,
                ButtonType.ERRORS: error_settings.max_results,
                ButtonType.PROCESSES: process_settings.max_results,
            }
            limit = limits.get(request.button, 20)
        
        # Ограничиваем количество элементов в ответе
        items = answer.items[:limit] if answer.items else []
        
        # Формируем ответ API
        response = AskResponse(
            text=answer.text,
            query=answer.query,
            total_found=answer.total_found,
            items=items,
            meta=answer.meta,
            category=answer.category
        )
        
        logger.info(f"Сформирован ответ с {len(items)} элементами")
        return response
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return AskResponse(
            text=f"Произошла ошибка при обработке запроса: {str(e)}",
            query=request.question,
            total_found=0,
            items=[]
        )