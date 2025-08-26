# app/adapters/excel_loader.py

import pandas as pd
import os
from pathlib import Path
from app.adapters.exceptions import DataLoadError
from app.config import contractor_settings, risk_settings, error_settings, process_settings
from app.utils.logging import setup_logger, get_pipeline_logger
from app.domain.enums import ButtonType

# Настройка логгера
logger = setup_logger(__name__)

class ExcelLoader:
    """
    Адаптер для загрузки и очистки данных из Excel файла.
    """
    
    def __init__(self):
        """Инициализация загрузчика Excel."""
        self.pipeline_logger = get_pipeline_logger(f"{self.__class__.__name__}")
    
    def load(self, button_type: ButtonType = None) -> pd.DataFrame:
        """
        Загружает и очищает данные из Excel-файла в зависимости от типа кнопки.
        
        :param button_type: Тип кнопки (contractors или risks)
        :return: DataFrame с данными из файла
        :raises HTTPException 500: если не удалось загрузить файл
        """
        file_path, file_description = self._get_file_path_and_description(button_type)
        
        self.pipeline_logger.log_detail(f"Загрузка данных для типа: {button_type.value if button_type else 'default'}")
        self.pipeline_logger.log_detail(f"Путь к файлу: {file_path}")
        
        if not self._check_file_exists(file_path):
            error_msg = f"Файл данных не найден: {file_path}"
            self.pipeline_logger.log_detail(error_msg, "ERROR")
            raise DataLoadError(error_msg)
        
        file_info = self._get_file_info(file_path)
        self.pipeline_logger.log_detail(f"Информация о файле: {file_info}")
        
        try:
            self.pipeline_logger.log_detail("Начинаем чтение Excel файла")
            df = pd.read_excel(file_path)

            # Очистка всего DataFrame сразу после загрузки
            self.pipeline_logger.log_detail("Начинаем очистку загруженных данных...")
            df = self._clean_dataframe(df)
            self.pipeline_logger.log_detail("Очистка данных завершена.")
            
            self._log_dataframe_details(df, file_description)
            
            self.pipeline_logger.log_detail("Данные успешно загружены и очищены из Excel файла")
            return df
            
        except Exception as e:
            error_msg = f"Ошибка чтения или обработки файла данных: {e}"
            self.pipeline_logger.log_detail(error_msg, "ERROR")
            self.pipeline_logger.log_detail(f"Тип ошибки: {type(e).__name__}")
            raise DataLoadError(error_msg)
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает строковые данные во всем DataFrame.
        Применяется только к колонкам с типом 'object' (обычно строки).
        
        :param df: Исходный DataFrame
        :return: Очищенный DataFrame
        """
        # Проходимся по каждой колонке в DataFrame
        for col in df.columns:
            # Проверяем, что тип колонки - 'object', чтобы применять строковые методы
            if df[col].dtype == 'object':
                self.pipeline_logger.log_detail(f"Очистка колонки '{col}'...")
                
                # 1. Удаляем артефакт _x000D_
                df[col] = df[col].str.replace('_x000D_', '', regex=False)
                
                # ================================================================
                # НОВОЕ ИЗМЕНЕНИЕ: Полностью удаляем все двойные кавычки
                # Это необходимо, так как генератор грамматики не может их обработать.
                # ================================================================
                df[col] = df[col].str.replace('"', '', regex=False)
                
                # 3. Удаляем лишние пробелы в начале и в конце
                df[col] = df[col].str.strip()
        return df
    
    def _get_file_path_and_description(self, button_type: ButtonType) -> tuple[str, str]:
        """
        Получает путь к файлу и его описание в зависимости от типа кнопки.
        
        :param button_type: Тип кнопки
        :return: Кортеж (путь_к_файлу, описание_файла)
        """
        file_configs = {
            ButtonType.RISKS: (risk_settings.data_file_path, "файл рисков"),
            ButtonType.ERRORS: (error_settings.data_file_path, "файл ошибок"),
            ButtonType.PROCESSES: (process_settings.data_file_path, "файл процессов"),
        }
        
        # По умолчанию загружаем файл подрядчиков
        file_path, description = file_configs.get(
            button_type, 
            (contractor_settings.data_file_path, "файл подрядчиков")
        )
        
        return file_path, description
    
    def _check_file_exists(self, file_path: str) -> bool:
        """
        Проверяет существование файла.
        
        :param file_path: Путь к файлу
        :return: True если файл существует, False иначе
        """
        exists = os.path.exists(file_path)
        self.pipeline_logger.log_detail(f"Проверка существования файла '{file_path}': {exists}")
        return exists
    
    def _get_file_info(self, file_path: str) -> dict:
        """
        Получает информацию о файле.
        
        :param file_path: Путь к файлу
        :return: Словарь с информацией о файле
        """
        try:
            file_path_obj = Path(file_path)
            stat = file_path_obj.stat()
            
            info = {
                "размер": f"{stat.st_size} байт",
                "изменен": stat.st_mtime,
                "полный_путь": file_path_obj.absolute(),
                "расширение": file_path_obj.suffix
            }
            
            return info
        except Exception as e:
            self.pipeline_logger.log_detail(f"Ошибка получения информации о файле: {e}", "WARNING")
            return {"ошибка": str(e)}
    
    def _log_dataframe_details(self, df: pd.DataFrame, file_description: str):
        """
        Логирует детальную информацию о загруженном DataFrame.
        
        :param df: Загруженный DataFrame
        :param file_description: Описание файла
        """
        self.pipeline_logger.log_detail(f"Успешно загружен {file_description}")
        self.pipeline_logger.log_detail(f"Количество строк: {len(df)}")
        self.pipeline_logger.log_detail(f"Количество колонок: {len(df.columns)}")
        self.pipeline_logger.log_detail(f"Колонки: {list(df.columns)}")
        
        # Информация о типах данных
        dtype_info = {}
        for col, dtype in df.dtypes.items():
            dtype_info[col] = str(dtype)
        self.pipeline_logger.log_detail(f"Типы данных: {dtype_info}")
        
        # Информация о пустых значениях
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            null_info = {col: count for col, count in null_counts.items() if count > 0}
            self.pipeline_logger.log_detail(f"Пустые значения по колонкам: {null_info}")
        else:
            self.pipeline_logger.log_detail("Пустых значений не обнаружено")
        
        # Показываем первые несколько строк в DEBUG режиме
        if len(df) > 0:
            sample_size = min(3, len(df))
            self.pipeline_logger.log_detail(f"Первые {sample_size} строки данных:")
            for i in range(sample_size):
                row_data = df.iloc[i].to_dict()
                # Ограничиваем длину значений для логирования
                limited_row = {k: (str(v)[:100] + "..." if len(str(v)) > 100 else str(v)) 
                              for k, v in row_data.items()}
                self.pipeline_logger.log_detail(f"Строка {i+1}: {limited_row}")
        
        # Память, занимаемая DataFrame
        memory_usage = df.memory_usage(deep=True).sum()
        self.pipeline_logger.log_detail(f"Память, занимаемая данными: {memory_usage} байт")
