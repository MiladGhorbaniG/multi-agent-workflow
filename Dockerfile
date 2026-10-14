FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY sample_data ./sample_data
RUN pip install --no-cache-dir .

ENV DATA_DIR=/app/sample_data
ENV LLM_PROVIDER=mock

EXPOSE 8000

CMD ["uvicorn", "booknook_flow.api:app", "--host", "0.0.0.0", "--port", "8000"]
