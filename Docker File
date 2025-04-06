# Start with Python image
FROM python:3.11-slim

# Install system packages (including zbar for pyzbar)
RUN apt-get update && apt-get install -y \
    libzbar0 \
    curl \
    unzip \
    wget \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libx11-xcb1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all other files
COPY . .

# Run your app with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
