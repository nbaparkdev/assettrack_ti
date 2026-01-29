
FROM python:3.11-slim

WORKDIR /code

# Instalar dependências de sistema para zbar (QR Code) e postgres driver
RUN apt-get update && apt-get install -y \
    libzbar0 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./alembic /code/alembic
# COPY ./alembic.ini /code/alembic.ini 
# (Se tivesse alembic.ini, mas não criamos o arquivo de conf do alembic explícito, pode ser gerado depois com `alembic init`)

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
