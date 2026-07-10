# 10-Paper Evidence-Gated KG Experiment

This experiment scales the minimal evidence-gated dashboard concept from one paper to 10 section-level source papers.

## Counts

- Papers: 10
- Entities: 188
- Relationships: 240
- Concept nodes: 18
- Evidence nodes: 80
- Observation nodes: 80
- Evidence-supported observations: 80/80

## Selected Papers

- Neurotoxicity Following Exposure to Micro and Nanoplastics
- Neurotoxicity of nanoplastics: A review
- Micro- and Nanoplastics Breach the Blood–Brain Barrier (BBB): Biomolecular Corona’s Role Revealed
- Detection of Microplastics in Human Breast Milk and Its Association with Changes in Human Milk Bacterial Microbiota
- Microplastics exposure: implications for human fertility, pregnancy and child health
- An overview of research on the association between microplastics and central nervous system disorders
- Do Microplastics Have Neurological Implications in Relation to Schizophrenia Zebrafish Models? A Brain Immunohistochemistry, Neurotoxicity Assessment, and Oxidative Stress Analysis
- A Detailed Review Study on Potential Effects of Microplastics and Additives of Concern on Human Health
- Microplastics in the Human Body: Exposure, Detection, and Risk of Carcinogenesis: A State-of-the-Art Review
- Polystyrene microplastics exposition on human placental explants induces time-dependent cytotoxicity, oxidative stress and metabolic alterations

## Important Scope Note

By default, this prototype does not call an external LLM. It creates prompt artifacts for extraction, critique, and refinement, then builds a deterministic concept/evidence KG from available section text. The dashboard includes question answering, random-paper testing, and KG-vs-LLM answer comparison based only on stored graph evidence.

The comparison tab can optionally call a local LLM proxy if you start `local_llm_server.py` with a fresh OpenAI or Gemini API key. Never store API keys in HTML, JSON, prompts, or chat.

## Optional Local LLM Test Setup

Use a newly created API key and keep it local to your shell. OpenAI and Gemini are both supported.

```bash
export OPENAI_API_KEY="your_new_key_here"
python3 experiments/ten_paper_evidence_gated/local_llm_server.py
```

For Gemini, use either:

```bash
export GEMINI_API_KEY="your_new_key_here"
python3 experiments/ten_paper_evidence_gated/local_llm_server.py
```

or run the server with no key set and paste only the key when the hidden Python prompt appears.

Then open:

```text
http://127.0.0.1:8765/experiments/ten_paper_evidence_gated/ten_paper_dashboard.html
```

The dashboard button `Generate LLM Answer Locally` calls only `http://127.0.0.1:8765/api/llm`.

## Files

- `ten_paper_kg.json`: generated graph data
- `ten_paper_source_bundle.json`: selected 10-paper title/abstract/section source bundle
- `ten_paper_dashboard.html`: standalone dashboard
- `ten_paper_extraction_prompt.txt`: 10-paper extraction prompt scaffold
- `ten_paper_critique_prompt.txt`: 10-paper critique prompt scaffold
- `ten_paper_refinement_prompt.txt`: 10-paper refinement prompt scaffold
- `build_ten_paper_experiment.py`: reproducible generator
- `local_llm_server.py`: optional local API-key-safe LLM proxy for comparison testing
