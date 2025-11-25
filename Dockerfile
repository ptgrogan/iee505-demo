from python:3.10

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./src /app/src
COPY ./pyproject.toml /app/pyproject.toml
RUN pip install .

EXPOSE 8000
CMD ["fastapi", "run", "src/iee505/main.py", "--port", "8000"]

