FROM python:3.11-slim

# Install ViennaRNA (which includes RNAplot)
RUN apt-get update && apt-get install -y --no-install-recommends vienna-rna \
    && rm -rf /var/lib/apt/lists/*


# Set working directory inside container
WORKDIR /app

# Copy Python dependencies file inside the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Expose port 10000 (you can change if needed)
EXPOSE 10000

# Start the FastAPI server with uvicorn inside container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
