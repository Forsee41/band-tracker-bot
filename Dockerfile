FROM python:3.11
WORKDIR /app
RUN mkdir /app/data
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["python", "-m", "band_tracker"]
