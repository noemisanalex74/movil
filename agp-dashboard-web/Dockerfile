# 1. Usar una imagen base de Python
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo
WORKDIR /app

# 3. Instalar Poetry
RUN pip install poetry

# 4. Copiar los archivos de dependencias
COPY poetry.lock pyproject.toml ./

# 5. Instalar dependencias del proyecto sin crear un venv, y sin dev-dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# 6. Copiar el resto del código de la aplicación
COPY . .

# 7. Exponer el puerto que usará la aplicación
EXPOSE 5000

# 8. Comando para ejecutar la aplicación con un servidor de producción como gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]