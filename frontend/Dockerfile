# Utiliza una imagen base de Nginx
FROM nginx:latest

# Copia los archivos HTML y recursos estáticos al directorio raíz de Nginx
COPY . /usr/share/nginx/html

# Expone el puerto 80 para que Nginx pueda recibir solicitudes HTTP
EXPOSE 80

# Comando para iniciar Nginx cuando se ejecute el contenedor
CMD ["nginx", "-g", "daemon off;"]