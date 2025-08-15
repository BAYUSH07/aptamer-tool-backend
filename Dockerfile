FROM continuumio/miniconda3:latest

# Install system tools for EPS to SVG conversion (ghostscript and pstoedit)
RUN apt-get update && apt-get install -y --no-install-recommends ghostscript pstoedit && rm -rf /var/lib/apt/lists/*

# Add conda-forge and bioconda channels BEFORE environment creation
RUN conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda

# Create the conda env 'paws' with Python 3.11 and ViennaRNA from bioconda
RUN conda create -y -n paws python=3.11 viennarna

# Ensure all subsequent RUN/CMD/ENTRYPOINT use the conda env
SHELL ["conda", "run", "-n", "paws", "/bin/bash", "-c"]

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make conda env available for subprocesses
ENV PATH /opt/conda/envs/paws/bin:$PATH

EXPOSE 10000

# Start FastAPI backend
CMD ["conda", "run", "-n", "paws", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
