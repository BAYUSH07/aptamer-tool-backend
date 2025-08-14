import random
import RNA
import math
from Bio.SeqUtils import MeltingTemp as mt

def parse_fasta(fasta_text):
    lines = fasta_text.strip().split('\n')
    if lines[0].startswith('>'):
        return ''.join(lines[1:])
    return ''.join(lines)

def gc_content(sequence):
    gc_count = sequence.count('G') + sequence.count('C')
    return round((gc_count / len(sequence)) * 100, 2) if sequence else 0

def get_structure_and_mfe(seq):
    if not seq or any(nt not in "AUGC" for nt in seq.upper()):
        return ("", 0)
    structure, mfe = RNA.fold(seq)
    return (structure, round(mfe, 2))

def get_tm(seq):
    try:
        return round(mt.Tm_NN(seq, nn_table=mt.RNA_NN1), 2)
    except Exception:
        return None

def calculate_kd_from_dG(mfe):
    R = 1.987e-3  # kcal/(mol·K)
    T = 298
    if mfe is None or mfe == 0:
        return "N/A"
    try:
        K = math.exp(-mfe / (R * T))
        kd_molar = 1 / K
        kd_nM = kd_molar * 1e9
        if kd_nM < 0.01:
            return "<0.01"
        elif kd_nM > 1e8:
            return ">1E8"
        else:
            return "{:.2f}".format(kd_nM)
    except Exception:
        return "N/A"

def generate_aptamers_for_protein(
    sequence,
    num_aptamers=30,
    min_gc=None,
    max_gc=None,
    min_length=None,
    max_length=None,
    min_tm=None,
    max_tm=None,
):
    # Defaults if None supplied
    min_gc = 45 if min_gc is None else float(min_gc)
    max_gc = 65 if max_gc is None else float(max_gc)
    min_length = 20 if min_length is None else int(min_length)
    max_length = 80 if max_length is None else int(max_length)
    min_tm = float('-inf') if min_tm is None else float(min_tm)
    max_tm = float('inf') if max_tm is None else float(max_tm)

    aptamers = []
    attempts = 0
    max_attempts = num_aptamers * 40

    while len(aptamers) < num_aptamers and attempts < max_attempts:
        length = random.randint(min_length, max_length)
        aptamer = ''.join(random.choices("AUGC", k=length))
        gc = gc_content(aptamer)
        if min_gc <= gc <= max_gc:
            structure, mfe = get_structure_and_mfe(aptamer)
            mfe_display = "N/A" if mfe == 0 else "{:.2f}".format(mfe)
            tm = get_tm(aptamer)
            # Tm filter: only accept if within range; ignore if None
            if tm is not None and not (min_tm <= tm <= max_tm):
                attempts += 1
                continue
            kd = calculate_kd_from_dG(mfe)
            aptamers.append({
                "sequence": aptamer,
                "length": len(aptamer),
                "gc_content": gc,
                "structure": structure,
                "mfe": mfe_display,
                "tm": tm,
                "kd": kd
            })
        attempts += 1

    return aptamers

def mutate_aptamer(aptamer, num_mutations=30):
    complements = {'A': 'U', 'U': 'A', 'G': 'C', 'C': 'G'}
    first_five = ''.join(complements.get(nt, 'N') for nt in aptamer[:5])
    last_five = ''.join(complements.get(nt, 'N') for nt in aptamer[-5:])
    mutations = []
    while len(mutations) < num_mutations:
        middle = ''.join(random.choices("AUGC", k=len(aptamer)-10))
        mutated_aptamer = first_five + middle + last_five
        gc = gc_content(mutated_aptamer)
        if 45 <= gc <= 65:
            structure, mfe = get_structure_and_mfe(mutated_aptamer)
            mfe_display = "N/A" if mfe == 0 else "{:.2f}".format(mfe)
            tm = get_tm(mutated_aptamer)
            kd = calculate_kd_from_dG(mfe)
            mutations.append({
                "sequence": mutated_aptamer,
                "length": len(mutated_aptamer),
                "gc_content": gc,
                "structure": structure,
                "mfe": mfe_display,
                "tm": tm,
                "kd": kd
            })
    return mutations

