# Документация по сервисам DUP AI

## Оглавление
- [AI DUP Main API](#сервис-ai-dup-main-api)
- [Gradio UI](#визуальный-сервис-gradio-ui)
- [Ollama GPU Check](#отладка-и-мониторинг-ollama-llm)
- [Типовые проблемы и решения](#типовые-проблемы-и-решения)

### Полезные команды
```bash
systemctl status ai-dup-main-api.service
systemctl status ai-dup-gradio-ui.service
systemctl status ollama-check-gpu.timer
sudo journalctl -u ai-dup-main-api.service -e
sudo journalctl -u ai-dup-gradio-ui.service -e
```

### Сервис: AI DUP Main API

- **systemd unit-файл:** `/etc/systemd/system/ai-dup-main-api.service`
- **Описание:** Главный API-сервис бизнес-логики для команды DUP (работа с LLM, генерация ответов по внутренним данным)
- **Рабочая директория:** `/home/nemov_ma/Documents/dup_ai_final_2`
- **Пользователь:** `nemov_ma`
- **Переменные окружения:**  
  Файл `.env` располагается в рабочей директории. Ключевые переменные:
  ```bash
  APP_NAME=Contractor Analysis API
  HOST=0.0.0.0
  PORT=8080
  LLM_OLLAMA_BASE_URL=http://localhost:11434/v1
  LLM_OLLAMA_MODEL=llama3.1:8b-instruct-fp16
  ```
- **Логи:**
  - Доступ: `/var/log/ai-dup/main-api-access.log`
  - Ошибки: `/var/log/ai-dup/main-api-error.log`

#### Проверка статуса сервиса
```bash
systemctl status ai-dup-main-api.service
```

#### Просмотр логов (актуально для диагностики)
```bash
tail -f /var/log/ai-dup/main-api-access.log
tail -f /var/log/ai-dup/main-api-error.log
```

#### Просмотр вывода в журнал терминала
```bash
sudo journalctl -u ai-dup-main-api.service -e
```

#### Открытие файла сервиса
```bash
sudo nano /etc/systemd/system/ai-dup-main-api.service
```

#### Запуск / остановка сервиса
```bash
sudo systemctl start ai-dup-main-api.service
sudo systemctl stop ai-dup-main-api.service
sudo systemctl restart ai-dup-main-api.service
```

#### Диагностика и устранение проблем
- Проверить статус сервиса через `systemctl status`
- В случае ошибки — открыть `error.log`
- При необходимости перезапустить сервис: `sudo systemctl restart ai-dup-main-api.service`
- Если порт 8080 занят, следуйте шагам из раздела «Проверка порта 8080»

#### Проверка окружения
- Приложение запускается в окружении:
  `/opt/miniconda3/envs/semantic-router`

#### Проверка порта 8080

1. Узнать, какой процесс слушает порт:
   ```bash
   sudo lsof -i :8080
   ```
В выводе ищите строку, где:
- В колонке COMMAND — python или uvicorn
- В колонке USER — nemov_ma
- В колонке PID — номер процесса (например, 12345)

2. Проверить команду процесса:
   ```bash
   sudo lsof -Pan -p <PID> -i
   ```
Это покажет информацию о порте, который использует процесс.

3. Проверить команду процесса:
   ```bash
   ps -p <PID> -o cmd
   ```
Должен быть путь:
```bash
/opt/miniconda3/envs/semantic-router/bin/python -m uvicorn app.main\:app --host 0.0.0.0 --port 8080
```

4. Если процесс не ваш — завершить его:
   ```bash
   sudo kill <PID>
   ```

5. Если не помогает:
   ```bash
   sudo kill -9 <PID>
   ```

6. Запустить свой процесс на освободившемся порту:
   ```bash
   /opt/miniconda3/envs/semantic-router/bin/python -m uvicorn app.main\:app --host 0.0.0.0 --port 8080
   ```

### Визуальный сервис (Gradio UI)

- **systemd unit-файл:** `/etc/systemd/system/ai-dup-gradio-ui.service`
- **Окружение:** `/opt/miniconda3/envs/basic-rag`
- **Рабочая директория:** `/home/nemov_ma/Documents/ai/`
- **Связан с:** `ai-dup-main-api.service` (основной backend), запускается после него
- **Логи:**
  - Доступ: `/var/log/ai-dup/gradio-ui-access.log`
  - Ошибки: `/var/log/ai-dup/gradio-ui-error.log`

#### Проверка статуса сервиса
```bash
systemctl status ai-dup-gradio-ui.service
```

#### Просмотр логов (актуально для диагностики)
```bash
tail -f /var/log/ai-dup/gradio-ui-access.log
tail -f /var/log/ai-dup/gradio-ui-error.log
```

#### Просмотр вывода в журнал терминала
```bash
sudo journalctl -u ai-dup-gradio-ui.service -e
```

#### Открытие файла сервиса
```bash
sudo nano /etc/systemd/system/ai-dup-gradio-ui.service
```

#### Запуск / остановка сервиса
```bash
sudo systemctl start ai-dup-gradio-ui.service
sudo systemctl stop ai-dup-gradio-ui.service
sudo systemctl restart ai-dup-gradio-ui.service
```

#### Диагностика и устранение проблем
- Проверить статус сервиса через `systemctl status ai-dup-gradio-ui.service`
- В поле вывода `Main PID` найти PID процесса.
- В случае ошибки — открыть `error.log`
- При необходимости перезапустить сервис: `sudo systemctl restart ai-dup-gradio-ui.service`

### Отладка и мониторинг Ollama (LLM)

#### 1. Bash-скрипт проверки GPU

- **Файл:** `/usr/local/bin/check_ollama_gpu.sh`
- **Описание:** Проверяет, использует ли контейнер `ollama-server` GPU; если нет – рестарт контейнера.
- **Запуск вручную:**
  ```bash
  /usr/local/bin/check_ollama_gpu.sh
  ```

#### 2. Systemd-юниты

- **ollama-check-gpu.service**
  - **Путь:** `/etc/systemd/system/ollama-check-gpu.service`
  - **Описание:** Одноразовый запуск скрипта `check_ollama_gpu.sh`

- **ollama-check-gpu.timer**
  - **Путь:** `/etc/systemd/system/ollama-check-gpu.timer`
  - **Описание:** Запускает `ollama-check-gpu.service` каждые 5 минут (`OnBootSec=1min`, `OnUnitActiveSec=5min`)

#### 3. Управление и проверка статуса

- Перезагрузить конфигурацию systemd:
  ```bash
  sudo systemctl daemon-reload
  ```

- Включить и запустить таймер:
  ```bash
  sudo systemctl enable ollama-check-gpu.timer
  sudo systemctl start ollama-check-gpu.timer
  ```

- Проверить статус таймера:
  ```bash
  systemctl status ollama-check-gpu.timer
  ```

- Просмотреть логи сервиса:
  ```bash
  sudo journalctl -u ollama-check-gpu.service -e
  ```

- Проверить последние записи в логе проверки:
  ```bash
  tail -n 20 /var/log/ai-dup/ollama-watch.log
  ```

#### 4. Ручные команды для Ollama

- Проверить, слушает ли Ollama GPU:
  ```bash
  nvidia-smi pmon -c 1 | grep ollama-server
  ```

- Рестарт контейнера вручную:
  ```bash
  docker restart ollama-server
  ```

### Типовая последовательность действий при сбое
1. Проверить статус нужного сервиса:
   ```bash
   systemctl status <service>
   ```
2. Просмотреть последние ошибки:
   ```bash
   tail -n 50 /var/log/ai-dup/<service>-error.log
   ```
3. Перезапустить сервис при необходимости:
   ```bash
   sudo systemctl restart <service>
   ```
4. Если проблема не решена, убедитесь в корректности `.env` и проверьте занятые порты.

### Типовые проблемы и решения
| Симптом | Возможная причина | Решение |
| --- | --- | --- |
| Сервис не запускается | `.env` отсутствует или содержит ошибки | Проверьте файл и перезапустите сервис |
| Порт 8080 занят | Другой процесс использует порт | Найдите процесс `sudo lsof -i :8080` и завершите его |
| Ollama не использует GPU | Контейнер запущен без доступа к GPU | Запустите `/usr/local/bin/check_ollama_gpu.sh` или `docker restart ollama-server` |
