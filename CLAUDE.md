# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload

# Alternative start command
python app/main.py
```

### Testing
```bash
# Test specific pipeline interactively
python test_universal_pipeline.py

# Test contractors pipeline
python test_universal_pipeline.py contractors "Найти подрядчика для строительства"

# Test risks with category
python test_universal_pipeline.py risks "Основные риски производства" manufacturing

# Test errors pipeline
python test_universal_pipeline.py errors "Ошибки в проекте разработки ПО"

# Test processes pipeline
python test_universal_pipeline.py processes "Процесс управления проектами"

```

### Health Check
```bash
curl http://localhost:8080/v1/health
```

## Architecture Overview

This is a FastAPI-based LLM-powered analysis system built with Clean Architecture principles. The system analyzes contractors, risks, errors, and business processes using intelligent tool selection and classification.

### Core Architecture Layers

1. **API Layer** (`app/api/`) - FastAPI endpoints and request/response schemas
2. **Pipeline Layer** (`app/pipelines/`) - Orchestrates the 8-step processing workflow
3. **Service Layer** (`app/services/`) - Business logic (normalization, classification, answer generation)
4. **Tools Layer** (`app/tools/`) - Intelligent tool selection using KeyBERT instead of LLM-based tool selection
5. **Domain Layer** (`app/domain/`) - Core models and business rules
6. **Adapter Layer** (`app/adapters/`) - External services (Excel loading, LLM client)

### Key Components

**Pipelines** (`app/pipelines/`):
- `base.py` - Base pipeline with block logging and 8-step processing
- Individual pipelines for contractors, risks, errors, and processes
- Each pipeline follows the same 8-step workflow

**Tools System** (`app/tools/`):
- `ToolRegistry` - Auto-discovers and registers available tools
- `ToolExecutor` - Executes selected tools based on KeyBERT analysis
- `KeywordSearchTool` - Intelligent keyword search with lemmatization
- **Important**: Uses KeyBERT for tool selection instead of LLM-based selection

**Configuration** (`app/config.py`):
- `ClassificationConfig` - Controls which columns are used for data classification
- Unified configuration for all entity types (contractors, risks, errors, processes)
- Environment-based settings with pydantic-settings

## Data Processing Workflow

Each request follows this 8-step pipeline:
1. **Data Loading** - Load Excel files from `/data` directory
2. **Normalization** - Clean and standardize data
3. **Preprocessing** - Filter by categories if applicable
4. **Item Loading** - Load unique classification items (e.g., project names)
5. **Classification** - LLM selects most relevant item
6. **Tool-based Filtering** - KeyBERT-powered tool selection and execution
7. **Model Transformation** - Convert to domain models
8. **Answer Generation** - LLM generates final response

## Configuration Management

### Classification Configuration
The system uses `ClassificationConfig` in `app/config.py` to control data classification:

```python
# Contractors classified by work types
CONTRACTOR = {
    "column_name": "work_types",
    "item_type": "вид работ",
    "description": "Классификация по видам работ подрядчиков"
}

# Risks classified by project names
RISK = {
    "column_name": "project_name", 
    "item_type": "проект",
    "description": "Классификация рисков по названиям проектов"
}
```

To modify classification logic, update the relevant configuration section and restart the application.

### Environment Variables
Required `.env` file variables:
- `DEBUG=true` - Enable detailed logging
- `LLM_OLLAMA_BASE_URL=http://localhost:11434/v1`
- `LLM_OLLAMA_MODEL=llama3.1:8b-instruct-fp16`
- Data file paths for each entity type

## Logging System

**Block-based logging** with unique Pipeline IDs:
- All logs go to `LOGS/dup_ai.log`
- Each request gets a unique 8-character Pipeline ID
- DEBUG mode shows full details of all 8 steps
- PROD mode shows only step completion status

**Log monitoring commands**:
```bash
# Real-time monitoring
tail -f LOGS/dup_ai.log

# Search by Pipeline ID
grep "a1b2c3d4" LOGS/dup_ai.log

# View only pipeline steps
grep "\[ШАГ" LOGS/dup_ai.log
```

## Data Requirements

Place Excel files in the `data/` directory:
- `contractors.xlsx` - Contractor data
- `riski.xlsx` - Risk data  
- `errors.xlsx` - Error data
- `bpmn_processes.xlsx` - Business process data

## Important Notes

- **Tool Selection**: The system recently switched from LLM-based tool selection to KeyBERT-based selection for improved performance
- **No Build/Lint Commands**: This is a Python project without specific build or lint configurations
- **LLM Dependency**: Requires Ollama running locally at `http://localhost:11434`
- **Russian Language**: The system is designed for Russian-language data and prompts