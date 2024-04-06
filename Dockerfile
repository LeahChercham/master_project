FROM python:3.12

WORKDIR /usr/src/app

# Copy only requirements first so we dont need to re install them everytime we build
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "./api/main.py"]
