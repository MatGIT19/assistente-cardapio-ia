FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
# A chave entra em tempo de execução: docker run -e GEMINI_API_KEY=... -p 8000:8000 assistente-cardapio
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
