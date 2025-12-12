FROM python:3.12

WORKDIR /app

RUN pip install --upgrade pip

COPY src/requirements ./requirements

RUN pip install -r requirements/requirements.txt --no-cache-dir

COPY src/. .
# ENV PYTHONPATH="/app/src"

# CMD [ "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
