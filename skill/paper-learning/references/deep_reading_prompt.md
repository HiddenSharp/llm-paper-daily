# Default Deep-Reading Prompt

Read the paper with the user's focus in mind.

Return a structured note with these sections:

1. Problem Setting
2. Core Contribution
3. Method Structure
4. Evidence and Experiments
5. Relationship to Prior Work
6. Reusable Ideas
7. Limitations
8. Archive Recommendation

Use the user's `Human Instruction` as a priority lens. If the instruction asks for benchmark design, RL formulation, agent workflow, data generation, or evaluation detail, emphasize that part of the note.

Do not claim full-paper evidence when only abstract-level material is available. Mark such sections as abstract-based.
