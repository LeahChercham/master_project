FROM python:3.12

WORKDIR /code

# Copy only requirements first so we dont need to re install them everytime we build
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code

EXPOSE 8000

CMD ["python", "./api/main.py"]
# CMD ["uvicorn", "api.main:app", "--port", "8001"]
