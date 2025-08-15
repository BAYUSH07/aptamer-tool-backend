FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential autoconf automake libtool pkg-config wget gzip tar \
    && rm -rf /var/lib/apt/lists/*

# Download, compile, and install ViennaRNA
RUN wget https://www.tbi.univie.ac.at/RNA/download/sourcecode/ViennaRNA-2.7.0.tar.gz && \
    tar -xf ViennaRNA-2.7.0.tar.gz && \
    cd ViennaRNA-2.7.0 && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && rm -rf ViennaRNA-2.7.0 ViennaRNA-2.7.0.tar.gz



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
