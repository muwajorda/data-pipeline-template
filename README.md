# Data Pipeline Template

## Overview
A minimal, production-aware data pipeline template designed for take-home assignments and small ETL workflows.

This template emphasizes:
- Config-driven execution
- Explicit schema validation
- Separation of concerns
- Cloud-aware I/O abstraction
- Containerization
- Basic test coverage

## Architecture
- `pipeline.py` - orchestration
- `validate.py` - schema enforcement
- `transform.py` - business logic
- `io.py` - storage abstraction
- Dockerized for reproducibility

## Run Locally
```bash
pip install -r requirements.txt
python -m pipeline_template.pipeline
```

## Run Tests
```bash
pytest
```

## Docker
```bash
docker build -t pipeline-template .
docker run pipeline-template
```

## Design Principles
- Fail loudly
- Avoid silent schema drift
- Separate transformation from orchestration
- Keep storage abstracted
- Make deployment trivial
