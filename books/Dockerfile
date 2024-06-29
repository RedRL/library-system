FROM python:3.9

WORKDIR /app

COPY . /app

# Install Python dependencies
RUN apt-get update && \
    apt-get install -y python3-dev && \
    pip install flask requests pymongo

EXPOSE 5001

CMD ["python", "app.py"]
