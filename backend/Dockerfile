# Estágio 1: Usar uma imagem base oficial do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de dependências para o diretório de trabalho
COPY requirements.txt .

# Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação para o diretório de trabalho
COPY . .

# Expor a porta 8000, onde a aplicação FastAPI/Uvicorn irá rodar
EXPOSE 8000

# Comando para iniciar a aplicação usando Uvicorn
# --host 0.0.0.0: permite que a aplicação seja acessível de fora do contêiner
# --port 8000: a porta que o Uvicorn vai usar
# main:app: "main" é o nome do arquivo python, "app" é o objeto FastAPI dentro do arquivo
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Nota: Certifique-se de que o arquivo requirements.txt e o código da aplicação estejam no mesmo diretório que este Dockerfile.