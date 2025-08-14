import os
import tempfile
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class StructureInput(BaseModel):
    sequence: str
    structure: str

def plot_secondary_structure(sequence: str, structure: str) -> str:
    import uuid

    try:
        # Sanitize inputs
        sequence = sequence.strip().upper().replace("T", "U")
        structure = structure.strip()

        # Validate
        if len(sequence) != len(structure):
            raise ValueError(f"Length mismatch: sequence ({len(sequence)}), structure ({len(structure)})")

        with tempfile.TemporaryDirectory() as tmpdir:
            uid = uuid.uuid4().hex[:6]
            input_basename = f"structure_{uid}"
            input_path = os.path.join(tmpdir, f"{input_basename}.ss")
            # Write input file
            with open(input_path, "w") as f:
                f.write(f"{sequence}\n{structure}\n")
            print(f"[RNAplot DEBUG] Input written to: {input_path}")
            print(f"[RNAplot DEBUG] Contents:\n{sequence}\n{structure}")

            # Run RNAplot
            result = subprocess.run(
                ["RNAplot", "-o", "svg", input_path],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            print(f"[RNAplot STDOUT]:\n{result.stdout}")
            print(f"[RNAplot STDERR]:\n{result.stderr}")
            if result.returncode != 0:
                raise Exception(f"RNAplot failed with exit code {result.returncode}. stderr: {result.stderr}")

            # ViennaRNA names output as <basename>_ss.svg
            expected_svg = os.path.join(tmpdir, f"{input_basename}_ss.svg")

            # Fallback: If file not found, pick the first SVG file in tempdir
            if not os.path.exists(expected_svg):
                svg_candidates = [f for f in os.listdir(tmpdir) if f.endswith(".svg")]
                if svg_candidates:
                    expected_svg = os.path.join(tmpdir, svg_candidates[0])
                else:
                    raise FileNotFoundError(f"RNAplot did not produce any SVG in {tmpdir}")

            # Move to system temp with unique name for later FileResponse cleanup
            final_path = os.path.join(tempfile.gettempdir(), f"rna_structure_{uid}.svg")
            os.replace(expected_svg, final_path)
            return final_path

    except Exception as e:
        print(f"[STRUCTURE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plot-structure")
def plot_rna_structure(input: StructureInput):
    from fastapi.responses import FileResponse
    path = plot_secondary_structure(input.sequence, input.structure)
    return FileResponse(path, media_type="image/svg+xml", filename="structure.svg")

