FROM python:3.12-slim

ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /code

# Instalar dependências de sistema para zbar (QR Code) e postgres driver
RUN apt-get clean && apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false --allow-releaseinfo-change && apt-get install -y \
    libzbar0 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./static /code/static
COPY ./create_admin.py /code/create_admin.py
COPY ./create_technician.py /code/create_technician.py
COPY ./activate_user_admin.py /code/activate_user_admin.py
COPY ./init_app.py /code/init_app.py

# Garantir existência da pasta de uploads (PDFs de contratos - módulo Compras)
RUN mkdir -p /code/static/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
