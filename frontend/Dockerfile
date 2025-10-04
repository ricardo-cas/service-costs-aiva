# Estágio 1: Usar uma imagem base leve do Nginx
FROM nginx:1.21.6-alpine

# Remover a configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar o arquivo HTML da aplicação para o diretório raiz do Nginx
COPY index.html /usr/share/nginx/html

# Expor a porta 80, que é a porta padrão do Nginx
EXPOSE 80

# O comando padrão do Nginx para iniciar o servidor em primeiro plano
CMD ["nginx", "-g", "daemon off;"]

