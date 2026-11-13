# 3QPEO: Quantum Phase Estimation for 3-SAT

This repository contains a Python prototype for encoding a 3-SAT instance as
a quantum circuit and applying quantum phase estimation (QPE) to the encoding.
The implementation is in
[`threeQPEO_prod_2026_11_13.py`](./threeQPEO_prod_2026_11_13.py).


## What the script does

The script:

1. Represents each clause as three signed integer literals.
2. Builds a phase-encoding circuit with two qubits per variable, for its
   positive and negative literals.
3. Constructs a QPE circuit using controlled powers of the encoding operator
   and an inverse quantum Fourier transform.
4. Simulates the circuits with Qiskit's state-vector simulator, prints
   non-zero state-vector amplitudes, and samples the phase-register outcomes.

The example at the bottom of the script runs the circuit on a small,
hard-coded 3-SAT instance. Edit `clauses` there to try another instance.

## Requirements

- Python 3
- NumPy
- Qiskit
- Matplotlib

Install the dependencies with:

```bash
python -m pip install numpy qiskit matplotlib
```

## Run

From the repository directory:

```bash
python threeQPEO_prod_2026_11_13.py
```

The script prints circuit diagrams as text, state-vector information, and
sampled counts for the phase register. State-vector simulation requires memory
that grows exponentially with the number of qubits, so use small instances.

## Input format

Provide a non-empty list of clauses, each containing exactly three signed
integers:

```python
clauses = [
    [1, 2, 3],
    [-1, 2, 4],
    [2, -3, -4],
]
G = hypergraph(clauses)
```

A positive literal `i` denotes variable `i`; a negative literal `-i` denotes
its negation. Variable identifiers are expected to be positive integers
starting at `1`. The number of variables is inferred as the largest absolute
literal value.

## Main functions

- `hypergraph(clauses)` stores the clauses and derives the variable count and
  phase-register size.
- `three_sat_encoding_operator(H, theta, apply_global_phase=False)` builds the
  clause phase-encoding circuit.
- `phase_estimation_circuit(G, is_superposition=True)` builds the QPE circuit.
- `measure_phase_amplitude(qpe_qc, m, N, shots=1024)` samples and prints the
  phase-register outcomes.

## Use as a Python library
You can import its functions from another script. Keep the module in the same directory as your
script, or install/place it somewhere on Python's import path:

```python
import math

from threeQPEO_prod_2026_11_13 import (
    hypergraph,
    three_sat_encoding_operator,
)

clauses = [
    [1, 2, 3],
    [-1, 2, 4],
    [2, -3, -4],
]
instance = hypergraph(clauses)

theta = 2 * math.pi / (2**instance.m)
encoding_circuit = three_sat_encoding_operator(instance, theta)
print(encoding_circuit.draw(output="text"))
```

`three_sat_encoding_operator` returns a Qiskit `QuantumCircuit`, which you can
compose into a larger circuit or simulate with Qiskit.

## Notes

- The QPE circuit uses `G.m + 2 * G.N` qubits.
- `is_superposition=True` prepares the phase register and the first half of
  the target register in superposition.

