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
COPY ./create_admin.py /code/create_admin.py
COPY ./create_technician.py /code/create_technician.py
COPY ./activate_user_admin.py /code/activate_user_admin.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
