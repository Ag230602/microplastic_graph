// ===========================================================================
// Microplastics Knowledge Graph (v2) - Benchmark scientific queries (Cypher)
// Load mpkg_graph_v2.cypher into Neo4j first, then run these.
// These satisfy Requirement 4 (benchmark queries) and Phase 3 (ranking/RAG).
// ===========================================================================

// ---------------------------------------------------------------------------
// Q1  Which polymers are linked to a mechanism (e.g. oxidative stress)?
// Path used by this review KG: Polymer <-(has_polymer)- Observation
//                              <-(reports)- Study -(evaluates)-> Mechanism
// ---------------------------------------------------------------------------
MATCH (p:Polymer)<-[:HAS_POLYMER]-(o:Observation)<-[:REPORTS]-(s:Study)
      -[:EVALUATES]->(m:Mechanism {label: 'oxidative_stress'})
RETURN DISTINCT p.name AS polymer
ORDER BY polymer;

// ---------------------------------------------------------------------------
// Q2  Which tissues/organs are most frequently affected?
// ---------------------------------------------------------------------------
MATCH (t:TissueOrgan)<-[r:AFFECTS|MEASURED_IN|RELEVANT_TO]-()
RETURN t.label AS tissue, count(r) AS links
ORDER BY links DESC, tissue;

// ---------------------------------------------------------------------------
// Q3  Which biomarkers support inflammation?
// ---------------------------------------------------------------------------
MATCH (m:Mechanism {label: 'inflammation'})-[:EVIDENCED_BY]->(b:Biomarker)
RETURN b.name AS biomarker
ORDER BY biomarker;

// ---------------------------------------------------------------------------
// Q4  Drinking-water microplastics -> human cardiovascular outcomes?
// Translational gap query: expected to return NOTHING for this corpus,
// which is itself a scientifically valuable result.
// ---------------------------------------------------------------------------
MATCH path = (h:HostPopulation {organism_class: 'human'})
             -[:EXPERIENCES]->(o:ClinicalOutcome)
WHERE toLower(o.label) CONTAINS 'cardiovascular'
RETURN path;
// (No rows => insufficient direct human cardiovascular evidence in the graph.)

// ---------------------------------------------------------------------------
// Provenance / evidence traceability:
//   Which exact sentence supports an observation, and from which study?
// ---------------------------------------------------------------------------
MATCH (s:Study)-[:PROVIDES]->(e:Evidence)-[:SUPPORTS]->(o:Observation)
RETURN s.title AS study, e.text AS supporting_sentence,
       e.section AS section, e.confidence AS confidence, o.id AS observation
ORDER BY study;

// ---------------------------------------------------------------------------
// Human vs animal evidence ranking (by translational relevance)
// ---------------------------------------------------------------------------
MATCH (h:HostPopulation)
OPTIONAL MATCH (h)-[:EXHIBITS]->(b:Biomarker)
OPTIONAL MATCH (h)-[:EXPERIENCES]->(o:ClinicalOutcome)
RETURN
  CASE WHEN h.organism_class = 'human' THEN 'human' ELSE 'animal' END AS bucket,
  count(DISTINCT h)  AS hosts,
  count(DISTINCT b)  AS biomarkers,
  count(DISTINCT o)  AS outcomes
ORDER BY bucket;

// ---------------------------------------------------------------------------
// Which studies reported oxidative stress?  (systematic-review style)
// ---------------------------------------------------------------------------
MATCH (s:Study)-[:EVALUATES]->(m:Mechanism {label: 'oxidative_stress'})
RETURN s.id AS study, s.design AS design, s.species AS species
ORDER BY study;

// ---------------------------------------------------------------------------
// Full reasoning chain (Graph-RAG retrieval):
//   Study -> Evidence -> Observation -> Polymer, plus Host -> Biomarker
// ---------------------------------------------------------------------------
MATCH (st:Study)-[:PROVIDES]->(ev:Evidence)-[:SUPPORTS]->(ob:Observation)
OPTIONAL MATCH (ob)-[:HAS_POLYMER]->(pol:Polymer)
OPTIONAL MATCH (st)-[:INVESTIGATES]->(host:HostPopulation)-[:EXHIBITS]->(bm:Biomarker)
RETURN st.title AS study, ev.text AS evidence, ob.id AS observation,
       collect(DISTINCT pol.name) AS polymers,
       host.label AS host, collect(DISTINCT bm.name) AS biomarkers;
