from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from algorithm import (
    parse_fasta,
    generate_aptamers_for_protein,
    mutate_aptamer,
    gc_content,
    get_structure_and_mfe,
    get_tm,
    calculate_kd_from_dG,
)
from generate_rna_structure import plot_secondary_structure
from fastapi.responses import FileResponse
import random

app = FastAPI()

# CORS middleware to allow requests from your frontend on Netlify and backend itself
origins = [
    "http://localhost:3000",
    "https://paws-aptamers.netlify.app",  # Your Netlify site
    "https://paws.software",
    # You can add your custom domain here if you use it
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use ["*"] for debugging all origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class AptamerRequest(BaseModel):
    fasta_sequence: str
    num_aptamers: int = 30
    min_gc: Optional[float] = None
    max_gc: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_tm: Optional[float] = None
    max_tm: Optional[float] = None

class MutationRequest(BaseModel):
    aptamer: str
    num_mutations: int = 30

class PointMutationRequest(BaseModel):
    aptamer: str
    num_point_mutations: int = 10

class StructurePlotRequest(BaseModel):
    sequence: str
    structure: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "RNA Aptamer Generator is running!"}

@app.post("/generate-aptamers")
def generate(request: AptamerRequest):
    try:
        sequence = parse_fasta(request.fasta_sequence)
        aptamers = generate_aptamers_for_protein(
            sequence=sequence,
            num_aptamers=request.num_aptamers,
            min_gc=request.min_gc,
            max_gc=request.max_gc,
            min_length=request.min_length,
            max_length=request.max_length,
            min_tm=request.min_tm,
            max_tm=request.max_tm,
        )
        if not aptamers:
            raise HTTPException(
                status_code=400,
                detail="No aptamers could be generated with the given constraints. Try relaxing Tm, GC%, or length filters."
            )
        return {
            "input_length": len(sequence),
            "num_aptamers": len(aptamers),
            "aptamers": aptamers
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mutate-aptamer")
def mutate(request: MutationRequest):
    try:
        aptamer = request.aptamer.strip().upper()
        if not (20 <= len(aptamer) <= 80):
            raise ValueError("Aptamer must be between 20 and 80 nucleotides long.")
        mutations = mutate_aptamer(aptamer, request.num_mutations)
        return {
            "original_aptamer": aptamer,
            "mutations": mutations
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def point_mutate_aptamer(aptamer, num_mutations=10):
    bases = ['A', 'U', 'G', 'C']
    aptamer = aptamer.upper()
    if not (20 <= len(aptamer) <= 80):
        raise ValueError("Aptamer length must be between 20 and 80 nucleotides.")
    mutations = set()
    mutation_results = []
    attempts = 0
    max_attempts = num_mutations * 20
    while len(mutation_results) < num_mutations and attempts < max_attempts:
        mutated = list(aptamer)
        pos = random.randint(0, len(mutated) - 1)
        current_nt = mutated[pos]
        choices = [b for b in bases if b != current_nt]
        mutated[pos] = random.choice(choices)
        mutated_seq = ''.join(mutated)
        if mutated_seq == aptamer or mutated_seq in mutations:
            attempts += 1
            continue
        if any(nt not in "AUGC" for nt in mutated_seq):
            attempts += 1
            continue
        gc = gc_content(mutated_seq)
        if not (45 <= gc <= 65):
            attempts += 1
            continue
        structure, mfe = get_structure_and_mfe(mutated_seq)
        mfe_display = "N/A" if mfe == 0 else "{:.2f}".format(mfe)
        tm = get_tm(mutated_seq)
        kd = calculate_kd_from_dG(mfe)
        mutation_results.append({
            "sequence": mutated_seq,
            "length": len(mutated_seq),
            "gc_content": gc,
            "structure": structure,
            "mfe": mfe_display,
            "tm": tm,
            "kd": kd
        })
        mutations.add(mutated_seq)
        attempts += 1
    if not mutation_results:
        raise ValueError("No valid point mutations generated with the given parameters.")
    return mutation_results

@app.post("/point-mutate-aptamer")
def point_mutate(request: PointMutationRequest):
    try:
        mutated_aptamers = point_mutate_aptamer(request.aptamer, request.num_point_mutations)
        return {
            "original_aptamer": request.aptamer,
            "mutations": mutated_aptamers
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/plot-structure")
def plot_structure_endpoint(request: StructurePlotRequest):
    try:
        path = plot_secondary_structure(request.sequence, request.structure)
        return FileResponse(path, media_type="image/svg+xml", filename="structure.svg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


