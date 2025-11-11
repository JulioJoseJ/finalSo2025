FROM public.ecr.aws/lambda/python:3.11

# Copiar requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Instalar dependencias
RUN pip install -r requirements.txt

# Copiar código de la aplicación
COPY . ${LAMBDA_TASK_ROOT}

# Instalar Mangum para el handler de Lambda
RUN pip install mangum

# Comando para ejecutar la función Lambda
CMD ["main.handler"]