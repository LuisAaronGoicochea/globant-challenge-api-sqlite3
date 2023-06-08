# Utiliza una imagen base de Python 3.9
FROM python:3.9

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos y el código de la API a /app
COPY requirements.txt app.py /app/

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 5000 para que la API Flask pueda recibir solicitudes HTTP
EXPOSE 5000

# Comando para ejecutar la aplicación Flask cuando se ejecute el contenedor
CMD ["python", "app.py"]