from fastapi import APIRouter, Depends, Query
from app.api.v1.schemas import AskRequest, AskResponse
from app.domain.enums import ButtonType
from app.pipelines import get_pipeline, init_container
from app.config import contractor_settings
from app.utils.logging import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Инициализация контейнера с зависимостями
init_container()

# Создание роутера
router = APIRouter(
    prefix="/v1",
    tags=["Contractor Analysis API v1"]
)

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
    limit: int = Query(contractor_settings.max_results, description="Максимальное количество результатов")
):
    """
    Обработка запроса от пользователя.
    
    :param request: Модель запроса с вопросом и типом кнопки
    :param limit: Максимальное количество возвращаемых результатов
    :return: Модель ответа с результатами
    """
    logger.info(f"Обработка запроса: '{request.question}' для кнопки {request.button}")
    
    # Получаем соответствующий пайплайн
    pipeline = get_pipeline(request.button, request.risk_category)
    
    # Обрабатываем запрос в зависимости от типа кнопки
    if request.button == ButtonType.CONTRACTORS:
        answer = pipeline.process(request.question)
    elif request.button == ButtonType.RISKS:
        answer = pipeline.process(request.question, request.risk_category)
    elif request.button == ButtonType.ERRORS:
        answer = pipeline.process(request.question)
    else:
        logger.error(f"Неизвестный тип кнопки: {request.button}")
        return AskResponse(
            text=f"Неизвестный тип кнопки: {request.button}",
            query=request.question,
            total_found=0,
            items=[]
        )
    
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