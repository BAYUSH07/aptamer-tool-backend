# Use official Miniconda base image for Python and conda
FROM continuumio/miniconda3:latest

# Create a conda environment named 'paws' with Python and ViennaRNA
RUN conda create -y -n paws python=3.11 viennarna

# Make sure conda env is activated for RUN commands
SHELL ["conda", "run", "-n", "paws", "/bin/bash", "-c"]

WORKDIR /app

# Copy requirements and install Python dependencies into the 'paws' env
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of your project files
COPY . .

# Add conda env bin directory to PATH for all subsequent instructions and the launched process
ENV PATH /opt/conda/envs/paws/bin:$PATH

# Expose port for uvicorn/FastAPI
EXPOSE 10000

# Run FastAPI with uvicorn in the conda environment
CMD ["conda", "run", "-n", "paws", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
