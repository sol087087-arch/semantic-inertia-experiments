## Coherence Evaluation Protocol

### 1. Task Definition

Given a sequence of texts ( T = {t_1, t_2, ..., t_n} ), each text ( t_i ) is evaluated independently with respect to its internal coherence and, when applicable, its progression relative to ( t_{i-1} ).

---

### 2. Construct Definition

We define **coherence** as the joint presence of:

* **Semantic interpretability**: The existence of recoverable meaning that can be paraphrased.
* **Structural connectivity**: The presence of logical, causal, or associative relations between textual units.
* **Referential persistence**: Stability of entities, concepts, or abstractions across the text.
* **Progression**: Non-trivial transformation or extension relative to preceding content.

A failure in any single dimension does not imply incoherence; classification is based on aggregate degradation.

---

### 3. Label Space

Each text is assigned one of four mutually exclusive labels:

#### 3.1 Coherent

The text satisfies most coherence dimensions:

* Maintains a consistent semantic frame
* Preserves referential or conceptual continuity
* Exhibits interpretable relational structure
* Extends or transforms prior content (if sequential)
* Contains no significant linguistic corruption

#### 3.2 Borderline

The text exhibits partial degradation:

* Semantic content is present but weak or diffuse
* Interpretability is incomplete or unstable
* Conceptual drift without clear linkage
* Limited or superficial progression
* Minor linguistic anomalies that do not prevent reading

#### 3.3 Degenerate

The text exhibits substantial coherence failure:

* No stable or paraphrasable meaning
* Absence of referential or relational structure
* Fragmented or unconnected sentence sequence
* Repetition, looping, or absence of progression
* Surface fluency without semantic grounding

#### 3.4 Hard Degenerate

The text exhibits failure at the linguistic level:

* Token-level corruption (non-words, mixed scripts, code artifacts)
* Syntactic breakdown preventing interpretation

---

### 4. Annotation Procedure

Annotators perform evaluation using the following ordered protocol:

1. **Form Check**
   If token-level corruption or syntactic failure prevents interpretation → *Hard Degenerate*

2. **Paraphrasability Test**
   Attempt to restate the text:

   * Successful - proceed
   * Partial - candidate for *Borderline*
   * Impossible - *Degenerate*

3. **Structural Assessment**
   Evaluate presence of:

   * semantic continuity
   * referential stability
   * relational structure

4. **Progression Assessment** (for sequential data)
   Compare with ( t_{i-1} ):

   * Non-trivial extension - positive signal
   * Repetition or stalling - negative signal

5. **Final Assignment**
   Label is determined by aggregate signal across dimensions, not a single criterion.

---

### 5. Scoring Guideline (Optional)

For increased consistency, annotators may assign binary indicators:

* Interpretability (0/1)
* Continuity (0/1)
* Referential stability (0/1)
* Relational structure (0/1)
* Progression (0/1)

A simple mapping:

* 4–5 - Coherent
* 2–3 - Borderline
* 0–1 - Degenerate

Hard Degenerate overrides scoring.

---

### 6. Reliability Considerations

* The protocol prioritizes **interpretability over stylistic fluency**
* Ambiguous poetic or abstract texts should not be penalized if paraphrasable structure is present
* Repetition without transformation is treated as coherence degradation
* Annotators should avoid inferring meaning not supported by the text

Inter-annotator agreement should be measured (e.g., Cohen’s κ or Krippendorff’s α) on a validation subset.

---

### 7. Core Principle

Surface-level fluency is not sufficient for coherence.
Coherence requires interpretable semantic structure and measurable progression across adjacent units.

---

### 8. Borderline Resolution Heuristic


In ambiguous cases, annotators apply an additional interpretability criterion:
A text is classified as *coherent* if its semantic structure can be reasonably reconstructed by an uninformed reader without requiring external context or interpretive effort beyond standard language comprehension.
Texts that rely solely on stylistic cues (e.g., abstraction, elevated register) without supporting interpretable structure are classified as *degenerate*. 
