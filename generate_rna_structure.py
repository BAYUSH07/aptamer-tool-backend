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
        sequence = sequence.strip().upper().replace("T", "U")
        structure = structure.strip()
        if len(sequence) != len(structure):
            raise ValueError(f"Length mismatch: sequence ({len(sequence)}), structure ({len(structure)})")
        with tempfile.TemporaryDirectory() as tmpdir:
            uid = uuid.uuid4().hex[:6]
            input_basename = f"structure_{uid}"
            input_path = os.path.join(tmpdir, f"{input_basename}.ss")
            with open(input_path, "w") as f:
                f.write(f"{sequence}\n{structure}\n")
            # Run RNAplot
            result = subprocess.run(
                ["RNAplot", input_path],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            # List all files produced
            output_files = os.listdir(tmpdir)
            print(f"[RNAplot] Output files in {tmpdir}: {output_files}")
            print(f"[RNAplot STDOUT]:\n{result.stdout}")
            print(f"[RNAplot STDERR]:\n{result.stderr}")
            expected_svg = os.path.join(tmpdir, f"{input_basename}_ss.svg")
            # Fallback: pick first SVG file if available
            if not os.path.exists(expected_svg):
                svg_candidates = [f for f in output_files if f.endswith(".svg")]
                if svg_candidates:
                    expected_svg = os.path.join(tmpdir, svg_candidates[0])
                else:
                    # Return all context to the API client for debugging!
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "RNAplot did not produce any SVG file.",
                            "output_files": output_files,
                            "stdout": result.stdout,
                            "stderr": result.stderr
                        }
                    )
            final_path = os.path.join(tempfile.gettempdir(), f"rna_structure_{uid}.svg")
            os.replace(expected_svg, final_path)
            return final_path
    except Exception as e:
        print(f"[STRUCTURE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plot-structure")
def plot_rna_structure(input: StructureInput):
    from fastapi.responses import FileResponse, JSONResponse
    try:
        path = plot_secondary_structure(input.sequence, input.structure)
        return FileResponse(path, media_type="image/svg+xml", filename="structure.svg")
    except HTTPException as exc:
        # If detail is a dict, return as JSON (for frontend to parse/debug)
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=500, content=exc.detail)
        raise
