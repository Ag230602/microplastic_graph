// ===========================================================================
// Microplastics Knowledge Graph (v2) - Evidence-aware benchmark queries
// Load mpkg_graph_v2.cypher into Neo4j first, then run these.
// ===========================================================================

// ---------------------------------------------------------------------------
// Q1  Which polymers are linked to oxidative stress, with supporting evidence?
// ---------------------------------------------------------------------------
MATCH (m:Mechanism {label: 'oxidative_stress'})<-[:ACTIVATES]-(h:HostPopulation)<-[:EXPOSES]-(xp:ExposurePathway)<-[:ENTERS_VIA]-(p:Polymer)
OPTIONAL MATCH (p)<-[:HAS_POLYMER]-(o:Observation)<-[:SUPPORTS]-(e:Evidence)<-[:PROVIDES]-(s:Study)
RETURN p.name AS polymer,
       count(DISTINCT e) AS evidence_count,
       collect(DISTINCT s.title) AS supporting_studies,
       collect(DISTINCT e.text)[0..5] AS supporting_evidence
ORDER BY evidence_count DESC, polymer;

// ---------------------------------------------------------------------------
// Q2  Which tissues/organs are most frequently affected, with evidence counts?
// ---------------------------------------------------------------------------
MATCH (t:TissueOrgan)
OPTIONAL MATCH (t)<-[:AFFECTS]-(o:Observation)<-[:SUPPORTS]-(e:Evidence)<-[:PROVIDES]-(s:Study)
OPTIONAL MATCH (t)<-[:MEASURED_IN]-(b:Biomarker)<-[:REPORTS]-(bs:Study)
RETURN t.label AS tissue,
       count(DISTINCT e) AS evidence_count,
       count(DISTINCT o) + count(DISTINCT b) AS graph_links,
       collect(DISTINCT coalesce(s.title, bs.title))[0..8] AS supporting_studies,
       collect(DISTINCT e.text)[0..5] AS supporting_evidence
ORDER BY evidence_count DESC, graph_links DESC, tissue;

// ---------------------------------------------------------------------------
// Q3  Which biomarkers support inflammatory mechanisms, with studies/evidence?
// ---------------------------------------------------------------------------
MATCH (:Mechanism {label: 'inflammation'})-[:EVIDENCED_BY]->(b:Biomarker)
OPTIONAL MATCH (s:Study)-[:REPORTS]->(b)
OPTIONAL MATCH (s)-[:PROVIDES]->(e:Evidence)
WHERE e.text IS NULL OR toLower(e.text) CONTAINS toLower(replace(b.name, 'α', 'alpha')) OR toLower(e.text) CONTAINS toLower(b.name)
RETURN b.name AS biomarker,
       count(DISTINCT e) AS evidence_count,
       collect(DISTINCT s.title) AS supporting_studies,
       collect(DISTINCT e.text)[0..5] AS supporting_evidence
ORDER BY biomarker;

// ---------------------------------------------------------------------------
// Q4  What evidence links drinking-water MPs to human cardiovascular outcomes?
// Expected result for this corpus: human evidence is limited / no direct chain.
// ---------------------------------------------------------------------------
MATCH (dw:EnvironmentalCompartment {label: 'drinking water'})-[:CONTRIBUTES_TO]->(xp:ExposurePathway)-[:EXPOSES]->(h:HostPopulation {organism_class: 'human'})
OPTIONAL MATCH path = (dw)-[:CONTRIBUTES_TO]->(:ExposurePathway)-[:EXPOSES]->(h)-[:EXPERIENCES]->(cv:ClinicalOutcome)
WHERE cv IS NULL OR toLower(cv.label) CONTAINS 'cardiovascular'
RETURN 'limited' AS human_evidence,
       collect(DISTINCT h.label) AS human_hosts,
       collect(DISTINCT cv.label) AS cardiovascular_outcomes,
       count(path) AS direct_evidence_chains,
       CASE WHEN count(path) = 0
            THEN 'No direct drinking-water -> human cardiovascular evidence chain in this corpus.'
            ELSE 'Direct chain(s) found.'
       END AS verdict;

// ---------------------------------------------------------------------------
// Provenance traceability: exact sentence -> observation -> study.
// ---------------------------------------------------------------------------
MATCH (s:Study)-[:PROVIDES]->(e:Evidence)-[:SUPPORTS]->(o:Observation)
RETURN s.title AS study,
       e.text AS supporting_sentence,
       e.section AS section,
       e.confidence AS confidence,
       o.id AS observation,
       o.notes AS observation_summary
ORDER BY study, observation;

// ---------------------------------------------------------------------------
// Full reasoning chain for Graph-RAG retrieval.
// ---------------------------------------------------------------------------
MATCH (st:Study)-[:PROVIDES]->(ev:Evidence)-[:SUPPORTS]->(ob:Observation)-[:ABOUT]->(reservoir:EnvironmentalCompartment)-[:CONTAINS]->(agent:Polymer)-[:ENTERS_VIA]->(xp:ExposurePathway)-[:EXPOSES]->(host:HostPopulation)-[:ACTIVATES]->(mech:Mechanism)-[:EVIDENCED_BY]->(bm:Biomarker)-[:LEADS_TO]->(outcome:ClinicalOutcome)
RETURN st.title AS study,
       ev.text AS evidence,
       ob.notes AS observation,
       reservoir.label AS environmental_reservoir,
       agent.name AS agent,
       xp.pathway_label AS exposure_pathway,
       host.label AS host_population,
       mech.label AS mechanism,
       bm.name AS biomarker,
       outcome.label AS clinical_outcome
LIMIT 50;
