FROM python:3.10
WORKDIR /app
COPY . .
RUN mkdir /app/data
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "band_tracker"]