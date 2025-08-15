FROM continuumio/miniconda3:latest

# Add conda-forge and bioconda channels BEFORE environment creation
RUN conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda

# Create the conda env 'paws' with Python 3.11 and ViennaRNA from bioconda
RUN conda create -y -n paws python=3.11 viennarna

SHELL ["conda", "run", "-n", "paws", "/bin/bash", "-c"]

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH /opt/conda/envs/paws/bin:$PATH

EXPOSE 10000

CMD ["conda", "run", "-n", "paws", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
