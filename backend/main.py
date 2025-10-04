import os
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, condecimal
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from prometheus_fastapi_instrumentator import Instrumentator

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Carregamento de Configurações do Ambiente ---
HOURLY_RATE = float(os.getenv("HOURLY_RATE", 50.0))
FRONTEND_URL = os.getenv("FRONTEND_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logging.error("Variável de ambiente DATABASE_URL não definida.")
    raise ValueError("DATABASE_URL é necessária para a conexão com o banco de dados.")

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="API de Cálculo de Valor por Tarefa",
    description="Calcula o valor de tarefas com base no tempo e persiste os dados.",
    version="1.0.0"
)

# --- Habilitar CORS (com segurança para produção) ---
origins = []
if FRONTEND_URL:
    origins.append(FRONTEND_URL)
    logging.info(f"CORS habilitado para a origem: {FRONTEND_URL}")
else:
    logging.warning("FRONTEND_URL não definida, CORS não permitirá nenhuma origem.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuração do Banco de Dados ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "calculated_tasks"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_hours = Column(Float)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Modelos de Dados Pydantic ---
class TaskInput(BaseModel):
    description: str = Field(..., example="Desenvolvimento do endpoint de autenticação")
    start_time: datetime = Field(..., example="2024-01-10T09:00:00")
    end_time: datetime = Field(..., example="2024-01-10T11:30:00")

class CalculationRequest(BaseModel):
    tasks: List[TaskInput]

class TaskOutput(TaskInput):
    duration_hours: float
    cost: float

class CalculationResponse(BaseModel):
    calculated_tasks: List[TaskOutput]
    grand_total: float

# --- Endpoints da API ---
@app.get("/", summary="Endpoint de Health Check")
def read_root():
    return {"status": "ok"}

@app.post("/api/calculate/", response_model=CalculationResponse, summary="Calcula e salva tarefas")
def calculate_and_save_tasks(request: CalculationRequest):
    if not request.tasks:
        raise HTTPException(status_code=400, detail="A lista de tarefas não pode estar vazia.")
    calculated_tasks_output = []
    grand_total = 0.0
    db = SessionLocal()
    try:
        for task in request.tasks:
            if task.end_time <= task.start_time:
                raise HTTPException(
                    status_code=400, 
                    detail=f"A data de fim da tarefa '{task.description}' deve ser posterior à data de início."
                )
            duration = task.end_time - task.start_time
            duration_hours = duration.total_seconds() / 3600
            cost = duration_hours * HOURLY_RATE
            calculated_tasks_output.append(
                TaskOutput(
                    description=task.description,
                    start_time=task.start_time,
                    end_time=task.end_time,
                    duration_hours=duration_hours,
                    cost=cost,
                )
            )
            grand_total += cost
            db_task = TaskDB(
                description=task.description,
                start_time=task.start_time,
                end_time=task.end_time,
                duration_hours=duration_hours,
                cost=cost,
            )
            db.add(db_task)
        db.commit()
        logging.info(f"{len(request.tasks)} tarefas calculadas e salvas. Valor total: {grand_total:.2f}")
    except Exception as e:
        db.rollback()
        logging.error(f"Erro durante o cálculo e salvamento: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao processar as tarefas.")
    finally:
        db.close()
    return CalculationResponse(
        calculated_tasks=calculated_tasks_output,
        grand_total=grand_total,
    )

# --- Configuração de Métricas para Prometheus ---
Instrumentator().instrument(app).expose(app, endpoint="/metrics")