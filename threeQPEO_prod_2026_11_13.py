#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 08:45:59 2026

@author: mauro
"""

import numpy as np
import math
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import QFTGate
from itertools import combinations
import matplotlib.pyplot as plt
from qiskit.circuit.library import XGate
import random

def print_state_vector(qc, text, only_all_non_zero_amplitudes=True):
    """Print the state vector produced by a quantum circuit.

    Args:
        qc: The circuit to simulate. It must be compatible with
            ``Statevector.from_instruction`` (for example, a unitary circuit
            without measurements).
        text: A heading printed before the state-vector entries.
        only_all_non_zero_amplitudes: If True, omit basis states whose
            amplitudes are numerically close to zero. If False, print every
            basis state.

    Each output entry includes the computational-basis state, its complex
    amplitude, amplitude magnitude, and phase in radians. The displayed
    bitstring follows the integer indexing used by Qiskit's state vector.
    """
    print(f"\n=== {text} ===")
    # Simulate the circuit and obtain its state-vector amplitudes.
    state = Statevector.from_instruction(qc)
    n_qubits = qc.num_qubits

    # Visit each computational-basis state in the vector.
    for idx, amp in enumerate(state.data):
        # Convert the vector index to a fixed-width binary basis label.
        bitstring = format(idx, f"0{n_qubits}b")
        magnitude = np.abs(amp)

        # Optionally hide amplitudes that are effectively zero (up to
        # floating-point precision).
        if not only_all_non_zero_amplitudes or not np.isclose(magnitude, 0):
            # np.angle returns the complex amplitude's phase in radians.
            phase_angle_rad = np.angle(amp)
            print(f"|{bitstring}> : Amplitude = {amp:+.4f} | Mag = {magnitude:.4f} | Phase = {phase_angle_rad:+.4f} rad")



class hypergraph:
    """Represent a 3-SAT instance as signed-literal hyperedges.

    Each clause is an iterable of signed integers: a positive literal ``i``
    represents variable ``i``, and a negative literal ``-i`` represents its
    negation. The class derives the number of variables and the register sizes
    used by the phase-estimation circuit.

    Attributes:
        N: Number of variables, equal to the largest absolute literal value.
        edges: The clauses supplied at initialization.
        M: Number of clauses.
        m: Number of qubits allocated to the phase-estimation register.
    """
    def __init__(self, clauses):
        """Initialize from a collection of clauses containing signed literals.

        Args:
            clauses: A non-empty collection of clauses. Each clause contains
                the signed integer literals of one 3-SAT constraint.
        """

        self.N = 0  #it will be the number of Boolean variables in the 3-SAT instance, which is the maximum absolute value of the literals in the clauses
        for e in clauses:
            self.N = max(self.N, max(abs(v) for v in e))
        #self.vertices = [i for i in range(2*self.N)]
        self.edges = clauses
        
        self.M = len(self.edges)

        # Allocate enough counting qubits to represent the edge count,
        # retaining one extra qubit as in this project's QPE convention.
        self.m = 2 + int(np.ceil(np.log2(len(clauses))))  # Number of counting qubits

       

def three_sat_encoding_operator(H, theta, apply_global_phase=False):
    """Build the phase-encoding circuit for a 3-SAT instance.

    The target register contains two qubits per variable, representing its
    positive and negative literals. The circuit applies degree-dependent
    single-qubit phases, followed by controlled-phase operations for each
    three-literal clause.

    Args:
        H: 3-SAT instance with ``N`` variables and signed-literal clauses in
            ``edges``. It must also provide ``M``, the number of clauses.
        theta: Phase angle, in radians, used by the encoding gates.
        apply_global_phase: If True, add a global phase of ``-theta * H.M``.

    Returns:
        A ``QuantumCircuit`` acting on ``2 * H.N`` qubits.
    """
    # Allocate one target qubit for each variable polarity.
    qc = QuantumCircuit(2 * H.N, name="3QPEOCircuit")

    # Apply a phase to each literal qubit according to its clause degree.
    for v in range(1, H.N + 1):
        positive_degree = sum(1 for edge in H.edges if v in edge)
        qc.p(theta * positive_degree, v - 1)
        negative_degree = sum(1 for edge in H.edges if -v in edge)
        qc.p(theta * negative_degree, H.N + v - 1)

    # Add clause-specific controlled phases. Each edge must contain exactly
    # three literals, which are mapped to their polarity qubits.
    for e in H.edges:
        e1 = [H.N - v - 1 if v < 0 else v - 1 for v in e]
        v1, v2, v3 = e1

        # Apply pairwise phase contributions involving the first literal.
        qc.cp(-theta, v1, v2)
        qc.cp(-theta, v1, v3)

        # Apply the three-qubit phase contribution for the control pattern
        # specified by ctrl_state, with v3 as the target.
        qc.mcp(-theta, [v1, v2], v3, ctrl_state='10')

    if apply_global_phase:
        # Add the same phase offset once for every clause.
        qc.global_phase = -theta * H.M
    return qc

def register_conditional_bit_flip_(N):
    """Flip the vertex-selection qubits to match the oracle's expected layout.

    The oracle expects the vertex-selection register to be in a uniform
    superposition of all vertices, which is achieved by flipping the
    qubits corresponding to the second half of the vertex register.

    Args:
        qc: Quantum circuit containing the vertex-selection register.
    """
    # Flip the second half of the vertex-selection qubits.
    # Flip the second half of the vertex-selection qubits.
    qc = QuantumCircuit(2*N)
    # Flip qubit G.N + j when phase-register qubit j is |0>.
    zero_controlled_x = XGate().control(1, ctrl_state="0")
    for j in range(N):
        qc.append(zero_controlled_x, [j, N + j])
    return qc


def phase_estimation_circuit(G, is_superposition=True):
    """Construct a quantum phase-estimation circuit for the 3-SAT encoding.

    The circuit has an ``m``-qubit phase register followed by a ``2 * G.N``
    qubit target register. It prepares the registers according to
    ``is_superposition``, applies the conditional bit-flip preparation, then
    applies controlled powers of the 3-SAT encoding operator and an inverse
    QFT to the phase register.

    Args:
       G: 3-SAT instance providing the variable count ``N``, clause data,
           and phase-register size ``m``.
       is_superposition: If True, apply Hadamard gates to the phase register
           and the first ``G.N`` target qubits. If False, apply Hadamards
           only to the phase register.

    Returns:
       A ``QuantumCircuit`` with ``G.m + 2 * G.N`` qubits implementing the
       phase-estimation circuit.
    """
    # The target register uses two qubits per variable, one for each literal
    # polarity; the phase register stores the estimated phase.
    N = G.N * 2
    m = G.m
    theta = 2 * np.pi / (2**m)

    # Lay out the phase register first and the encoding target register after it.
    qpe_qc = QuantumCircuit(m + N)

    # Put the phase register into superposition. Optionally also prepare the
    # first half of the target register in superposition.
    if is_superposition:
       qpe_qc.h(range(m + G.N))
    else:
       qpe_qc.h(range(m))

    # Apply the conditional bit-flip preparation to the target register.
    zqc = register_conditional_bit_flip_(int(N/2))
    qpe_qc.compose(
       zqc,
       qubits=range(m, m + zqc.num_qubits),
       inplace=True,
    )

    # Apply B^(2^j) controlled by phase-register qubit j.
    for j in range(m):
       power = 2**j
       B = three_sat_encoding_operator(G, power * theta)

       # Convert the encoding circuit into a gate, then add its phase-qubit
       # control and apply it across the full target register.
       B_gate = B.to_gate(label=f"B^{power}")
       controlled_B = B_gate.control(1)
       target_qubits = list(range(m, m + N))
       qpe_qc.append(controlled_B, [j] + target_qubits)

    # The inverse QFT converts the accumulated phase information into phase-
    # register computational-basis amplitudes.
    iqft = QFTGate(m).inverse()
    iqft.label = "QFT†"
    qpe_qc.append(iqft, range(m))

    return qpe_qc
 
def measure_phase_amplitude(qpe_qc, m, N, shots=1024):
    """Sample a QPE circuit and print counts for its phase register.

    The circuit is simulated as a state vector, then sampled the requested
    number of times. Since Qiskit displays bitstrings from the highest-index
    qubit to the lowest, the rightmost ``m`` bits correspond to qubits
    ``0`` through ``m - 1``.

    Args:
        qpe_qc: Quantum phase-estimation circuit to simulate.
        m: Number of qubits in the phase register.
        N: Number of target-register qubits (retained for the function's
            interface; the phase register is selected using ``m``).
        shots: Number of samples to draw from the circuit's output state.
    """
    # Remove any terminal measurements so Statevector can simulate the
    # circuit, then sample its final state.
    qpe_without_measurements = qpe_qc.remove_final_measurements(inplace=False)
    counts = Statevector.from_instruction(
        qpe_without_measurements
    ).sample_counts(shots=shots)

    print(f"\n--- Measurement Results ({shots} shots) ---")
    first_m_counts = {}
    for bitstring, count in counts.items():
        # Extract the phase-register bits (qubits 0 through m - 1) from
        # Qiskit's right-to-left bitstring representation.
        first_m = bitstring[-m:]
        # Combine counts that share the same phase-register measurement,
        # regardless of the target-register state.
        first_m_counts[first_m] = (
            first_m_counts.get(first_m, 0) + count
        )

    # Display phase-register outcomes from most to least frequently sampled.
    print("Measurements of the phase register (displayed as q(m-1),..., q1, q0):")
    for bitstring, count in sorted(
        first_m_counts.items(), key=lambda item: item[1], reverse=True
    ):
        print(f"{bitstring}: {count} counts ({(count/shots)*100:.2f}%) ")


   

if __name__ == "__main__":

    # Demonstrate phase estimation and the hitting-set on the 3-SAT instance of the paper
    # reported in the paper.
    clauses=[[1,2,3], [-1,2,4], [2,-3,-4], [-2,3,4], [1,-2, -4]]
    G = hypergraph(clauses)
    
    qc = QuantumCircuit(2*G.N, name="3QPEOCircuit")
    qc.h(range(G.N))
    zqc = register_conditional_bit_flip_(G.N)
    zqc_gate = zqc.to_gate(label="bit flip")
    qc.append(zqc_gate, range(zqc.num_qubits))
    qp = three_sat_encoding_operator(G, theta=2*np.pi/(2**G.m), apply_global_phase=False)
    qc.compose(qp, inplace=True)
    print("--- 3-SAT Quanbtum Encoding Operator Circuit ---")
    print(qc.draw(output='text'))
    print_state_vector(qc, "Phase State Vector")


    qpe_qc = phase_estimation_circuit(G, is_superposition=True)
    print(qpe_qc.draw(output='text'))
    measure_phase_amplitude(qpe_qc, G.m, G.N, shots=1024)
    
  
