# 3-SAT Quantum Phase Estimation Operator (3QPEO)

A Qiskit-based quantum computing implementation for encoding and solving 3-SAT (3-Satisfiability) instances using **Quantum Phase Estimation (QPE)**.

This repository represents 3-SAT formulas as signed-literal hypergraphs and constructs a dedicated unitary phase-encoding operator (`3QPEOCircuit`). By integrating this operator into a Quantum Phase Estimation pipeline, the circuit encodes clause satisfaction into eigenphases, enabling state-vector inspection and phase-register sampling.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Prerequisites & Installation](#prerequisites--installation)
- [Usage](#usage)
- [Code Structure](#code-structure)
- [Example Output](#example-output)
- [Notes & Caveats](#notes--caveats)

---

## Overview

In a 3-SAT problem with $N$ Boolean variables and $M$ clauses, each clause is a disjunction of three literals (variables or their negations). This project maps a 3-SAT instance onto a quantum register containing **$2N$ target qubits**—two qubits per variable representing its positive ($x_i$) and negative ($\neg x_i$) literal polarities—alongside an **$m$-qubit counting/phase register**.

Key capabilities include:
- **Hypergraph Representation:** Automatically infers variable counts ($N$), clause counts ($M$), and required phase-register precision ($m = 2 + \lceil \log_2(M) \rceil$) from signed-literal clause lists.
- **Unitary Phase Encoding:** Applies single-qubit degree phases, two-qubit controlled-phase gates (`cp`), and multi-controlled phase gates (`mcp`) to encode clause evaluations into quantum phases.
- **Quantum Phase Estimation (QPE):** Prepares valid dual-rail variable superpositions, applies controlled powers of the encoding operator $B^{2^j}$, and performs an inverse Quantum Fourier Transform ($\text{QFT}^\dagger$).
- **Exact State-Vector & Sampling Analysis:** Inspects non-zero computational basis amplitudes/phases and samples phase-register measurement distributions.

---

## How It Works

1. **Hypergraph Initialization (`hypergraph`)**
   - Clauses are supplied as lists of signed integers (e.g., `[1, -2, 3]` represents $x_1 \lor \neg x_2 \lor x_3$).
   - Positive literal $i$ maps to target qubit $i - 1$; negative literal $-i$ maps to target qubit $N + i - 1$.

2. **Valid Assignment State Preparation (`register_conditional_bit_flip_`)**
   - The first $N$ target qubits are placed in uniform superposition via Hadamard ($H$) gates.
   - Zero-controlled $X$ gates flip qubit $N + j$ whenever qubit $j$ is $|0\rangle$, ensuring each variable is in a valid complementary literal state ($|01\rangle$ or $|10\rangle$).

3. **3-SAT Phase Encoding Operator (`three_sat_encoding_operator`)**
   - Applies single-qubit phase gates $P(\theta \cdot d)$ proportional to each literal's clause degree $d$.
   - Iterates over every 3-literal clause $(v_1, v_2, v_3)$ and applies controlled-phase interactions (`cp(-theta)` and `mcp(-theta, ctrl_state='10')`) so that the accumulated phase reflects satisfied clauses.

4. **Quantum Phase Estimation (`phase_estimation_circuit`)**
   - Uses an $m$-qubit phase register with base angle $\theta = \frac{2\pi}{2^m}$.
   - Applies controlled-$B^{2^j}$ operations across the $2N$ target qubits followed by an inverse QFT (`QFTGate(m).inverse()`).

---

## Prerequisites & Installation

### Requirements
- Python 3.9+
- [Qiskit](https://www.ibm.com/quantum/qiskit) (v1.0+ recommended, utilizing `QFTGate` and `Statevector`)
- NumPy
- Matplotlib

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/3qpeo.git
   cd 3qpeo
   ```

2. Install the required dependencies:
   ```bash
   pip install qiskit numpy matplotlib
   ```

---

## Usage

Run the main script directly to execute the built-in 4-variable, 5-clause 3-SAT benchmark instance:

```bash
python threeQPEO_prod_2026_11_13.py
```

### Customizing the 3-SAT Instance

Modify the `clauses` list inside the `__main__` block of `threeQPEO_prod_2026_11_13.py` to test your own 3-SAT formulas:

```python
# Define clauses using signed integers (1-indexed variables)
# Example: (x1 OR x2 OR x3) AND (NOT x1 OR x2 OR x4) ...
clauses = [
    [1, 2, 3],
    [-1, 2, 4],
    [2, -3, -4],
    [-2, 3, 4],
    [1, -2, -4]
]

G = hypergraph(clauses)
qpe_qc = phase_estimation_circuit(G, is_superposition=True)
measure_phase_amplitude(qpe_qc, G.m, G.N, shots=1024)
```

---

## Code Structure

| Component | Description |
| :--- | :--- |
| `hypergraph` | Parses 3-SAT clauses into signed-literal hyperedges and computes $N$, $M$, and phase-register qubit count $m$. |
| `three_sat_encoding_operator` | Constructs the $2N$-qubit unitary circuit `3QPEOCircuit` encoding literal degrees and 3-literal clause phases. |
| `register_conditional_bit_flip_` | Prepares dual-rail polarity consistency across the $2N$ target qubits using zero-controlled `XGate` operations. |
| `phase_estimation_circuit` | Builds the full $(m + 2N)$-qubit QPE circuit with controlled-$B^{2^j}$ gates and inverse QFT. |
| `print_state_vector` | Simulates a unitary circuit with `Statevector` and prints non-zero basis states with magnitudes and phases (in radians). |
| `measure_phase_amplitude` | Samples the QPE output state vector and aggregates marginal measurement counts for the $m$-qubit phase register. |

---

## Example Output

Running the script prints:
1. An ASCII circuit diagram of the standalone **3-SAT Quantum Encoding Operator**.
2. The **Phase State Vector** listing computational basis states, complex amplitudes, magnitudes, and phase angles in radians.
3. An ASCII diagram of the complete **QPE Circuit**.
4. **Measurement Results** displaying sampled bitstrings (ordered $q_{m-1} \dots q_1 q_0$) and their occurrence percentages across 1,024 shots:

```text
--- Measurement Results (1024 shots) ---
Measurements of the phase register (displayed as q(m-1),..., q1, q0):
00000: 524 counts (51.17%)
11111: 438 counts (42.77%)
...
```

---

## Notes & Caveats

- **3-Literal Constraint:** `three_sat_encoding_operator` unpacks each clause as three literals (`v1, v2, v3 = e1`), so every input clause must contain exactly 3 literals.
- **Variable Indexing:** Variables must be 1-indexed positive/negative integers (`1` through `N` and `-1` through `-N`). Variable `0` is not supported.
- **Scope Note:** In `register_conditional_bit_flip_(N)`, ensure the loop bound references the passed parameter `N` if importing the function into external modules where global `G` is not defined.
- **Simulation Scaling:** Exact state-vector simulation scales exponentially as $O(2^{m + 2N})$. Practical local simulation is best suited for small instances ($N \le 6$).
