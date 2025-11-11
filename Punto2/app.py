from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import boto3
import pandas as pd
import io
import os

app = FastAPI(title="FastAPI con S3", description="Actividad Final SO - Universidad EIA", version="1.0")

# --- Configuración AWS ---
S3_BUCKET = os.getenv("S3_BUCKET", "mamboprimero")  # cambia por el nombre real
S3_KEY = "datos.csv"
s3 = boto3.client("s3")

# --- Modelo de validación ---
class Persona(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    edad: int = Field(..., gt=0, lt=120)
    altura: float = Field(..., gt=0.5, lt=3.0)

# --- Endpoint POST ---
@app.post("/guardar")
def guardar_persona(persona: Persona):
    try:
        # Descargar CSV actual o crear uno nuevo
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
            df = pd.read_csv(io.BytesIO(obj['Body'].read()))
        except s3.exceptions.NoSuchKey:
            df = pd.DataFrame(columns=["nombre", "edad", "altura"])

        # Agregar nueva fila
        nueva_fila = {"nombre": persona.nombre, "edad": persona.edad, "altura": persona.altura}
        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

        # Guardar nuevamente en S3 (sobrescribiendo el archivo)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=csv_buffer.getvalue())

        return {"mensaje": "Datos guardados correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint GET ---
@app.get("/filas")
def contar_filas():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()))
        return {"numero_filas": len(df)}
    except s3.exceptions.NoSuchKey:
        return {"numero_filas": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
