FROM python:3.9-slim
ENV DB_HOST=host.docker.internal
ENV DB_NAME=microservices
ENV DB_USER=postgres
ENV DB_PASSWORD=bikeshop
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
ENV NAME World
CMD ["python", "app.py"]