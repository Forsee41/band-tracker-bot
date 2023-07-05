FROM python:3.11
WORKDIR /app
RUN mkdir /app/data
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "band_tracker"]