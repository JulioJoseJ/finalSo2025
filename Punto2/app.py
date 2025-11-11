from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
import boto3
from botocore.exceptions import ClientError
import csv
import io
from typing import Optional

app = FastAPI(
    title="API de Personas",
    description="API para gestionar datos de personas en S3",
    version="1.0.0"
)

# Configuración de S3
S3_BUCKET = "mamboprimero"  # Cambiar por tu bucket
S3_FILE_KEY = "personas.csv"

# Cliente S3
s3_client = boto3.client('s3')

# Modelo Pydantic para validación
class Persona(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre de la persona")
    edad: int = Field(..., ge=0, le=150, description="Edad de la persona (0-150)")
    altura: float = Field(..., gt=0, le=3.0, description="Altura en metros (0-3.0)")
    
    @validator('nombre')
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    @validator('altura')
    def altura_valida(cls, v):
        if v <= 0:
            raise ValueError('La altura debe ser mayor a 0')
        return round(v, 2)

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "edad": 25,
                "altura": 1.75
            }
        }


@app.get("/", tags=["General"])
def read_root():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "Bienvenido a la API de Personas",
        "endpoints": {
            "POST /persona": "Agregar una persona al CSV en S3",
            "GET /personas/count": "Obtener el número de personas almacenadas"
        }
    }


@app.post("/persona", status_code=201, tags=["Personas"])
def agregar_persona(persona: Persona):
    """
    Agrega una nueva persona al archivo CSV en S3.
    El archivo se sobrescribe completamente con los nuevos datos.
    """
    try:
        # Intentar leer el archivo existente
        personas_existentes = []
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_FILE_KEY)
            contenido = response['Body'].read().decode('utf-8')
            
            # Leer CSV existente
            csv_reader = csv.DictReader(io.StringIO(contenido))
            personas_existentes = list(csv_reader)
        except ClientError as e:
            # Si el archivo no existe, comenzamos con lista vacía
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
        
        # Agregar nueva persona
        personas_existentes.append({
            'nombre': persona.nombre,
            'edad': str(persona.edad),
            'altura': str(persona.altura)
        })
        
        # Crear nuevo CSV en memoria
        output = io.StringIO()
        fieldnames = ['nombre', 'edad', 'altura']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(personas_existentes)
        
        # Subir a S3 (sobrescribir)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_FILE_KEY,
            Body=output.getvalue().encode('utf-8'),
            ContentType='text/csv'
        )
        
        return {
            "mensaje": "Persona agregada exitosamente",
            "persona": persona.dict(),
            "total_personas": len(personas_existentes)
        }
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al acceder a S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@app.get("/personas/count", tags=["Personas"])
def obtener_cantidad_personas():
    """
    Retorna el número de filas (personas) almacenadas en el CSV de S3.
    No cuenta la fila de encabezados.
    """
    try:
        # Obtener archivo de S3
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_FILE_KEY)
        contenido = response['Body'].read().decode('utf-8')
        
        # Contar filas (sin contar el header)
        csv_reader = csv.DictReader(io.StringIO(contenido))
        num_filas = sum(1 for _ in csv_reader)
        
        return {
            "numero_de_personas": num_filas,
            "archivo": S3_FILE_KEY,
            "bucket": S3_BUCKET
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {
                "numero_de_personas": 0,
                "mensaje": "No hay datos almacenados aún",
                "archivo": S3_FILE_KEY,
                "bucket": S3_BUCKET
            }
        raise HTTPException(
            status_code=500,
            detail=f"Error al acceder a S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@app.get("/health", tags=["General"])
def health_check():
    """Verificar el estado de la aplicación"""
    return {"status": "healthy", "service": "fastapi-s3-app"}