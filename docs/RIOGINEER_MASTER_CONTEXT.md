# RIOGINEER — MASTER TECHNICAL CONTEXT

**Document purpose:** Persistent technical context for developers, AI coding agents and future RIOGINEER development sessions.

**Status:** Living technical document  
**Project:** RIOGINEER  
**Company:** RIOGINEER LTDA  
**Last major context update:** September 2026

---

# 1. PRODUCT VISION

RIOGINEER is an AI-powered Digital Engineering platform.

Its purpose is to create Digital Engineers capable of combining:

- engineering knowledge;
- technical specifications and engineering requirements;
- artificial intelligence;
- physical and mathematical models;
- deterministic engineering calculations;
- process simulation;
- optimization;
- engineering software;
- engineering knowledge bases;
- human engineering review.

RIOGINEER is not intended to be a general-purpose chatbot.

The fundamental concept is:

> Engineering Intelligence. Built on Physics. Powered by AI.

Artificial intelligence is primarily responsible for interpretation,
reasoning, orchestration and interaction.

Engineering calculations should, whenever possible, be performed by
explicit physical, mathematical or deterministic computational models.

The LLM must not replace validated engineering calculations.

---

# 2. FUNDAMENTAL ARCHITECTURAL PRINCIPLE

The core architecture separates AI interpretation from engineering
calculation.

Conceptually:

Engineering Specification
        ↓
LLM Interpretation
        ↓
Structured Engineering Requirements
        ↓
Human Review / Approval
        ↓
Structured Flowsheet
        ↓
Engineering Models
        ↓
Deterministic Calculation / Simulation
        ↓
Validation
        ↓
Engineering Results

The LLM may interpret engineering information.

The LLM must not silently invent missing engineering data.

Missing information must remain explicitly missing unless:

1. the source provides the information;
2. the user provides the information;
3. an engineering assumption is explicitly proposed and approved;
4. a deterministic conversion or normalization is permitted by the
   application.

---

# 3. HUMAN-IN-THE-LOOP PRINCIPLE

Engineering decisions remain under human supervision.

The Digital Engineer should:

- interpret;
- organize;
- propose;
- calculate through engineering models;
- identify missing information;
- identify conflicts;
- identify ambiguities;
- identify unsupported capabilities;
- provide traceability;
- assist engineering decisions.

It should not conceal assumptions or uncertainty.

Important engineering assumptions require explicit review or approval.

---

# 4. PROVENANCE AND TRACEABILITY

RIOGINEER must preserve the relationship between:

SOURCE INFORMATION
        ↓
INTERPRETED FACT
        ↓
NORMALIZED ENGINEERING VALUE
        ↓
CALCULATION INPUT
        ↓
ENGINEERING RESULT

Source evidence and normalized engineering values are different objects.

Example:

Source:

    n-Hexane

Source evidence must preserve:

    n-Hexane

The application may deterministically normalize the identifier to:

    n_hexane

The normalized identifier must not replace the original source evidence.

---

# 5. EVIDENCE POLICY

The original engineering source must be preserved exactly.

Provider-returned evidence should be treated as an evidence candidate or
locator.

The authoritative evidence should ultimately be anchored to the original
source text.

Permitted deterministic evidence-location normalization may account for
non-semantic presentation differences such as:

- whitespace;
- line breaks;
- bullet formatting;
- Unicode dash variants;
- harmless punctuation differences.

Evidence anchoring must NOT permit changes to engineering meaning.

The following must remain strictly consistent:

- numerical values;
- signs;
- decimal values;
- engineering units;
- component identities;
- equipment identities;
- outlet identities.

If a unique deterministic source anchor cannot be established, the fact
must not automatically be accepted.

Ambiguous evidence must require rejection or human review.

---

# 6. CURRENT SYSTEM ARCHITECTURE

Current prototype architecture:

Browser
   ↓
Next.js RIOGINEER Website
   ↓
Technical Specification Interface
   ↓
LLM Interpretation Layer
   ↓
Structured Requirements
   ↓
Review / Approval
   ↓
Python Engineering Engine
   ↓
Structured Flowsheet
   ↓
PFD
   ↓
Engineering Calculation
   ↓
Results / Checks / Warnings

Current local development endpoints:

Website:

    http://127.0.0.1:3000

Python Engineering Engine:

    http://127.0.0.1:8001

Digital Engineer workspace:

    http://127.0.0.1:3000/digital-engineer

---

# 7. WEBSITE TECHNOLOGY

Current website stack:

- Next.js App Router;
- TypeScript;
- React;
- MDX;
- CSS Modules;
- automated tests;
- server-side API routes.

Main public pages include:

- Home
- Technology
- Applications
- Field Design
- Demonstrations
- About
- Contact
- Digital Engineer workspace

The website is intended to become the environment where users interact
with Digital Engineers and execute engineering workflows.

---

# 8. WEBSITE BUSINESS ROLE

The public web platform is intended to provide accessible engineering
functionality and demonstrations.

The current business concept is:

PUBLIC / FREE LAYER

Users may access selected Digital Engineers and engineering models without
charge.

CORPORATE / PAID LAYER

Revenue may come from:

- customization for corporate engineering procedures;
- integration with corporate documents;
- private engineering knowledge bases;
- specialized equipment libraries;
- integration with proprietary simulators;
- private deployment;
- technical support;
- training;
- engineering studies;
- specialized Digital Engineers;
- corporate implementation services.

The public platform therefore also functions as:

- product demonstration;
- technology validation;
- user acquisition;
- lead generation;
- engineering community interface.

---

# 9. FIELD DESIGN

Field Design is an existing engineering platform for conceptual design and
evaluation of offshore petroleum production systems.

It includes engineering routines involving areas such as:

- reservoir representations;
- wells;
- subsea systems;
- multiphase production;
- processing facilities;
- production capacities;
- economic evaluation;
- optimization.

Field Design has already been contracted by Petrobras.

RIOGINEER is intended to integrate with Field Design.

The conceptual relationship is:

RIOGINEER
    ↓
Digital Engineer / Engineering Intelligence
    ↓
Field Design
    ↓
Integrated Production-System Models
    ↓
Simulation / Optimization / Economic Evaluation

Field Design must remain a distinct engineering capability rather than
being duplicated unnecessarily inside the LLM layer.

---

# 10. DIGITAL ENGINEER WORKFLOW

The conceptual seven-step sequence used in the website is:

1. Engineering specification
2. Digital Engineer interpretation
3. Engineering model
4. PFD / engineering configuration
5. Simulation
6. Optimization
7. Engineering decision

This sequence should remain conceptually consistent across website
diagrams and product documentation.

---

# 11. MILESTONE 1 — DETERMINISTIC ENGINEERING FOUNDATION

Milestone 1 established the first deterministic engineering workflow.

Scope:

Three-phase separator.

It includes:

- versioned requirements contracts;
- flowsheet contracts;
- results contracts;
- strict validation;
- Python engineering engine;
- local HTTP API;
- PFD generation from structured connections;
- stream calculations;
- mass-balance checks;
- energy accounting;
- warnings;
- explicit unavailable calculations;
- stale-result handling.

The original reference folders and engineering equations were preserved.

Milestone 1 must not be silently changed by later AI-layer development.

---

# 12. TREINAMENTO BIA REFERENCE CASE

The principal current regression/reference case is the three-phase
separator known as:

    Treinamento Bia

Current reference feed:

    110,000 kg/h

Components:

    methane:   22,000 kg/h
    n-hexane:  77,000 kg/h
    water:     11,000 kg/h

Reference feed conditions:

    Temperature = 313.15 K
    Pressure    = 2,000,000 Pa absolute

Separator conditions:

    Temperature = 313.15 K
    Pressure    = 2,000,000 Pa absolute

Reference temperature:

    273.15 K

Constant heat capacities:

    methane   = 2200 J/(kg K)
    n-hexane  = 2200 J/(kg K)
    water     = 4180 J/(kg K)

Prescribed recoveries:

Methane:

    gas   = 1.00
    oil   = 0.00
    water = 0.00

n-Hexane:

    gas   = 0.00
    oil   = 1.00
    water = 0.00

Water:

    gas   = 0.00
    oil   = 0.05
    water = 0.95

Expected outlet flows:

    Gas   = 22,000 kg/h
    Oil   = 77,550 kg/h
    Water = 10,450 kg/h

Expected separator duty for the current reference case:

    0 W

These values constitute a validated regression basis and must not be
changed casually.

---

# 13. CURRENT SEPARATION MODEL

The current website-integrated separator calculation uses:

    Prescribed Component Recoveries — Development Model

This is intentionally a development model.

It does NOT currently predict rigorous:

- vapor-liquid equilibrium;
- vapor-oil-water equilibrium;
- separator sizing;
- geometry-based separation efficiency.

Prescribed recoveries determine component distribution between outlets.

This model exists primarily to validate the complete Digital Engineer
workflow.

It should eventually be complemented or replaced in appropriate workflows
by rigorous thermodynamic calculations.

---

# 14. EXISTING THERMODYNAMIC DEVELOPMENT

Separate RIOGINEER / process-simulation development has already explored
thermodynamic calculations including:

- PT flash;
- PH flash;
- PS flash;
- CoolProp benchmarking;
- process-network calculations;
- recycle convergence.

These capabilities should be evaluated for later integration into the web
Digital Engineer workflow.

Do not assume that all experimental thermodynamic code is already
production-integrated.

Integration must preserve:

- validation;
- explicit model assumptions;
- unit consistency;
- regression tests;
- engineering traceability.

---

# 15. RECYCLE AND PROCESS NETWORK DEVELOPMENT

Process-network and recycle calculations have been developed separately.

Recycle convergence has been demonstrated in development cases.

Future plant-level simulation should support:

- multiple equipment items;
- connected streams;
- recycle streams;
- convergence algorithms;
- mass balances;
- energy balances;
- equipment models.

The current website milestone does not yet expose this complete capability.

---

# 16. EQUIPMENT LIBRARY

Engineering equipment representations have been developed for RIOGINEER
and/or Draw.io integration.

Existing work includes representations or models for:

- source / feed;
- three-phase separator;
- two-phase separator;
- mixer;
- heat exchanger;
- valve;
- pump;
- compressor;
- electrostatic treater;
- hydrocyclone;
- flotation unit;
- TEG absorber / dehydration tower;
- TEG regeneration tower.

Additional equipment exists in earlier development work.

Important:

The existence of an equipment XML/drawing/model does NOT automatically mean
that the equipment is already integrated into the current website
calculation engine.

Distinguish:

1. graphical representation;
2. structured equipment object;
3. engineering calculation model;
4. validated equipment model;
5. web-integrated equipment capability.

---

# 17. PFD STRATEGY

RIOGINEER should generate Process Flow Diagrams from structured engineering
models.

The PFD must not be the primary source of engineering truth.

The structured flowsheet should define:

- equipment;
- streams;
- ports;
- connections;
- engineering identifiers;
- model inputs.

The diagram is a visual representation of that structured flowsheet.

Current initial drawing environment:

    Draw.io / diagrams.net

Draw.io is acceptable for initial development.

Future alternatives may be evaluated, including more professional
engineering drawing environments and standards-based representations.

---

# 18. FUTURE GRAPHICAL EDITING

The desired future workflow is:

Technical Specification
        ↓
RIOGINEER Interpretation
        ↓
Generated Structured Flowsheet
        ↓
Generated PFD
        ↓
User Graphical Editing
        ↓
Updated Structured Flowsheet
        ↓
Engineering Recalculation

Graphical editing must not create inconsistencies between the drawing and
the engineering model.

Display-only layout changes should not invalidate engineering results.

Engineering-topology or engineering-input changes must invalidate affected
results and require recalculation.

Graphical editing is NOT yet part of the current validated milestone.

---

# 19. MILESTONE 2 — TECHNICAL SPECIFICATION INTERPRETATION

Milestone 2 added AI-assisted interpretation before deterministic
engineering calculations.

Input modes include:

- typed engineering specification;
- pasted engineering specification;
- text-based PDF;
- additional instructions.

The system preserves these as separate evidence sources.

PDF handling currently extracts text locally before sending relevant text
to the configured LLM provider.

No OCR is currently part of the validated workflow.

---

# 20. LIVE LLM INTEGRATION

A real external LLM provider has been configured and tested.

The current development environment uses server-side configuration through
environment variables.

Secrets must never be:

- committed to Git;
- exposed through NEXT_PUBLIC variables;
- rendered in the browser;
- included in logs;
- copied into documentation.

The local `.env.local` file contains sensitive configuration and must remain
outside version control.

---

# 21. INTERPRETATION PRINCIPLES

The LLM interpretation layer should extract engineering facts such as:

- equipment;
- topology;
- components;
- flow rates;
- temperatures;
- pressures;
- units;
- model parameters;
- requested outputs;
- assumptions;
- limitations;
- conflicts;
- ambiguities.

The LLM output is NOT automatically an approved engineering model.

The sequence is:

Provider interpretation
        ↓
Local validation
        ↓
Local normalization
        ↓
Human review
        ↓
Approval
        ↓
Deterministic engineering workflow

---

# 22. LOCAL NORMALIZATION

Supported engineering normalization should occur locally and
deterministically whenever practical.

Example:

Source:

    Methane
    n-Hexane
    Water

Canonical identifiers:

    methane
    n_hexane
    water

Original names and excerpts remain preserved for provenance.

Normalization must not fabricate engineering information.

Unknown identities, collisions and unresolved mappings must remain blocked
or require review.

---

# 23. OUTPUT NORMALIZATION

Supported output names such as:

    gas
    oil
    water

must be normalized individually.

A provider response such as:

    "gas, oil and water"

must not be incorrectly treated as one unsupported output if the three
individual outputs are supported.

Actual unsupported requests must continue to be detected and blocked.

---

# 24. MISSING INFORMATION

Missing required engineering data must remain missing.

The interface should:

- highlight missing required fields;
- summarize missing information;
- prevent approval when mandatory data are absent.

The interface should NOT create redundant explanation boxes for every
ordinary missing numerical input.

Resolution notes are appropriate for:

- conflicts;
- ambiguities;
- contradictory evidence;
- explicit interpretation issues.

---

# 25. SCOPE EXCLUSIONS VS UNSUPPORTED REQUESTS

The system must distinguish:

REQUEST:

    "Calculate rigorous vapor-liquid equilibrium."

from EXCLUSION:

    "Rigorous vapor-liquid equilibrium is outside the requested scope."

The first may be an unsupported request.

The second is a scope statement and must not be classified as a request for
unsupported capability.

This distinction has been implemented and regression-tested.

---

# 26. LIVE PROVIDER LESSONS

Real LLM testing revealed issues that synthetic provider tests did not
detect.

Important discovered classes include:

1. provider output normalization;
2. component identity mapping;
3. scope-exclusion classification;
4. evidence excerpt formatting;
5. provenance anchoring.

Therefore:

Passing mocked LLM tests is not sufficient.

Major interpretation changes should also be validated periodically against
a configured live provider using non-confidential reference cases.

---

# 27. RESOLVED EVIDENCE-ANCHORING ISSUE

Former live-provider failure, now resolved through deterministic anchoring:

    excerpt_not_exact

A live-provider interpretation returned a valid engineering fact, but the
provider-generated evidence excerpt was not an exact character-for-character
substring of the original source.

Observed diagnostic example:

    stage: evidence
    field: components
    reason: excerpt_not_exact

The implemented architectural correction is:

- preserve original source exactly;
- treat provider evidence as a locator/candidate;
- deterministically anchor it to original source;
- store the exact original substring as authoritative evidence;
- tolerate only non-semantic formatting differences during location;
- reject ambiguous or engineering-inconsistent matches.

This correction has been regression-tested and the complete live end-to-end
reference demonstration has now been manually completed (see MILESTONE_3.md).

---

# 28. VALIDATION PHILOSOPHY

RIOGINEER must favor correctness, traceability and explicit limitations
over superficially successful demonstrations.

Do NOT weaken:

- provenance;
- engineering validation;
- unit checks;
- identity checks;
- missing-data checks;
- deterministic calculations

merely to make a demonstration pass.

When a live test fails, diagnose the failure.

Do not hide it with defaults or special-case reference values.

---

# 29. TESTING

The project uses multiple testing layers.

These include:

- TypeScript unit tests;
- integration tests;
- browser tests;
- Python tests;
- contract checks;
- lint;
- TypeScript checks;
- formatting;
- production builds;
- HTTP / smoke checks.

Test counts evolve continuously and should not be treated as permanent
architectural facts.

Regression tests should be added whenever a real failure reveals a new
failure class.

---

# 30. REFERENCE CASE POLICY

Reference cases should be:

- reproducible;
- versioned;
- documented;
- deterministic where appropriate;
- associated with expected results.

Reference cases must distinguish:

- synthetic development assumptions;
- educational examples;
- validated engineering benchmarks;
- real client data.

Synthetic data must not be represented as client or field data.

---

# 31. CONFIDENTIALITY

Corporate engineering specifications may contain confidential information.

Future architecture should support:

- private deployment;
- local models;
- controlled knowledge bases;
- restricted document access;
- auditability;
- separation between customer environments.

Do not send confidential client information to external providers unless
explicitly authorized and technically appropriate.

The current Treinamento Bia case is synthetic and suitable for development
testing.

---

# 32. KNOWLEDGE BASE STRATEGY

Future corporate implementations may use local or private knowledge bases
containing:

- engineering procedures;
- specifications;
- design practices;
- equipment standards;
- corporate lessons learned;
- engineering templates;
- validated historical cases.

RAG or equivalent retrieval architectures may be used.

Knowledge retrieval must remain distinguishable from deterministic
engineering calculation.

---

# 33. ENGINEERING KNOWLEDGE VS CALCULATION

RIOGINEER should distinguish at least four layers:

1. SOURCE KNOWLEDGE
   Documents, specifications, procedures, standards and user instructions.

2. INTERPRETATION
   AI-assisted extraction, organization, reasoning and identification of
   engineering requirements.

3. ENGINEERING MODEL
   Structured representation of equipment, streams, properties, operating
   conditions, topology, assumptions and calculation requirements.

4. ENGINEERING CALCULATION
   Deterministic physical and mathematical models, thermodynamics,
   equipment calculations, process simulation and optimization.

Information may flow between these layers, but their responsibilities must
remain distinguishable and traceable.

An LLM interpretation must never be represented as if it were the result
of a deterministic engineering calculation.


# 34. REQUIREMENTS / FLOWSHEET / RESULTS CONTRACTS

The current architecture uses three principal structured representations:

requirements.json
        ↓
flowsheet.json
        ↓
results.json

Conceptually:

requirements.json
    represents what RIOGINEER understood and what the engineer approved.

flowsheet.json
    represents the engineering system to be calculated.

results.json
    represents the deterministic engineering calculation results.

These contracts should remain versioned.

Future extensions should preserve backward compatibility where practical
and explicitly migrate incompatible versions.


# 35. REQUIREMENTS CONTRACT

The requirements representation should support:

- source identity;
- case identity;
- revision;
- equipment requirements;
- feed conditions;
- component information;
- operating conditions;
- required outputs;
- proposed connections;
- model selection;
- assumptions;
- missing information;
- ambiguities;
- conflicts;
- unsupported requests;
- provenance;
- review status;
- approval status.

Missing values must remain distinguishable from zero.

Specified, assumed and derived information must remain distinguishable.


# 36. FLOWSHEET CONTRACT

The flowsheet should be the engineering source of truth for process
topology.

It should support:

- equipment IDs;
- equipment types;
- calculation-model references;
- explicit ports;
- material streams;
- energy streams or boundaries;
- connections;
- operating conditions;
- engineering parameters;
- units;
- solver configuration;
- calculation status;
- validation messages;
- optional graphical presentation metadata.

Graphical coordinates and routing must remain separable from engineering
identity.

Moving an equipment symbol without changing the engineering topology must
not invalidate calculation results.

Milestone 3.1 adds engine-assigned engineering stream numbers alongside stable
stream IDs. Source/destination owner and port identities remain in connections
keyed by stream ID. The PFD and Engineering Stream Table view the same streams;
results join by stable stream ID, never by labels, array order or geometry.
Numbering is deterministic and independent of graphical layout. See
MILESTONE_3_1.md for the traversal rule and flowsheet/results 1.1 compatibility.


Milestone 4 preserves this identity architecture for a deterministic acyclic
separator/splitter/mixer network. Requirements 1.1 and flowsheet/results 1.2
explicitly represent the graph; previous single-separator versions remain
supported. Service names may repeat; stable IDs and stored engineering numbers
remain distinct. See MILESTONE_4.md.


# 37. RESULTS CONTRACT

Engineering results should preserve:

- run identity;
- flowsheet revision;
- engine version;
- equipment-model versions;
- property-model versions;
- stream results;
- equipment results;
- mass balances;
- energy balances;
- solver status;
- convergence information;
- engineering checks;
- warnings;
- limitations;
- provenance;
- reproducibility metadata.

Unavailable calculations must be reported explicitly as unavailable or
not calculated.

Do not substitute zero for an unavailable engineering calculation.


# 38. EQUIPMENT TYPE VS CALCULATION MODEL

Equipment identity and calculation model are separate concepts.

Example:

Equipment type:

    three_phase_separator

Current calculation model:

    prescribed_component_recoveries

Future calculation models may include:

    equilibrium_flash
    rigorous_separator_model
    vendor_performance_model

The equipment object should therefore reference a calculation model rather
than embedding one permanent mathematical interpretation of the equipment.


# 39. MODEL CAPABILITY

Each engineering model should expose its capability explicitly.

Examples:

- required inputs;
- supported components;
- supported phases;
- supported operating modes;
- calculated outputs;
- assumptions;
- limitations;
- model version;
- property-package requirements.

RIOGINEER must not silently use a model outside its declared capability.


# 40. UNITS

Engineering units must be explicit.

The system should distinguish between:

    bar absolute
    bar gauge

and must not silently infer the pressure reference.

Supported deterministic unit conversions may be performed locally.

Unit conversion should preserve:

- original value;
- original unit;
- normalized value;
- normalized unit;
- provenance.

Unsupported or ambiguous units require user review.


# 41. RESULTS FRESHNESS

Calculation results belong to a specific engineering-model revision.

Changes to any of the following should normally invalidate affected
results:

- numerical engineering inputs;
- process topology;
- selected equipment model;
- property model;
- solver settings;
- accepted engineering assumptions.

Pure graphical layout changes should not invalidate engineering results.

Stale results may remain visible for comparison but must be clearly marked
as stale and must never be presented as current results.


# 42. FUTURE THERMODYNAMIC DIRECTION

The current prescribed-recovery separator is a workflow-development model.

The current architectural sequence is topology and stream identity first,
rigorous thermodynamics later. Milestone 3.1 establishes numbered streams and
an Engineering Stream Table without adding property estimates. Unsupported
properties use null / not_calculated and display as “—”. Current composition
is mass-based; future thermodynamic providers should enrich the same stable
streams rather than redefine their identity or topology.

A major future objective is to integrate appropriate thermodynamic models
so that users can specify engineering information such as:

- feed composition;
- flow;
- temperature;
- pressure;
- separator operating conditions;

and allow the engineering engine to predict phase distribution when a
validated thermodynamic model supports the requested system.

The LLM must not calculate phase equilibrium itself.

Thermodynamic calculations belong to the engineering engine.


# 43. PROCESS SIMULATION ROADMAP

The intended progression is approximately:

PHASE 1
Single three-phase separator using prescribed recoveries.

PHASE 2
Single separator with qualified thermodynamic calculations.

PHASE 3
Multiple connected equipment items.

PHASE 4
Process networks with recycle streams.

PHASE 5
Broader offshore production-process flowsheets.

PHASE 6
Integration with Field Design and system-level optimization.

The exact sequence may evolve according to validation results and business
priorities.


# 44. INITIAL APPLICATION DOMAIN

The initial engineering domain is offshore oil and gas production.

This limitation is deliberate.

The current equipment knowledge and engineering development are primarily
associated with offshore production facilities.

The public interface should not imply universal chemical-process
capability until the relevant equipment and models have been implemented
and validated.


# 45. UNSUPPORTED EQUIPMENT

When a specification requests equipment not available in the current
registered library, RIOGINEER should report:

    Unsupported equipment

or an equivalent explicit capability message.

It must not silently replace unknown equipment with a superficially similar
model.

Future equipment should be introduced through the equipment registry,
model implementation and validation process.


# 46. USER EXPERIENCE PRINCIPLE

The normal engineering user should not need to edit JSON.

The preferred interaction is:

Upload / Write Specification
        ↓
Interpret
        ↓
What RIOGINEER Understood
        ↓
Review / Correct
        ↓
Approve
        ↓
Generate PFD
        ↓
Calculate
        ↓
Review Engineering Results

Structured JSON should remain available in an Advanced / Engineering Data
area for:

- audit;
- debugging;
- interoperability;
- download;
- advanced users.


# 47. INPUT MODES

The intended Digital Engineer should eventually accept:

- typed process descriptions;
- pasted engineering specifications;
- PDF specifications;
- structured engineering data;
- future supported document formats.

All input modes should converge toward the same structured engineering
requirements model.

The downstream engineering engine should not depend on whether a fact came
from PDF, typed text or another supported source.


# 48. PDF LIMITATIONS

Current PDF interpretation is text-based.

Important limitations include:

- no OCR;
- no guaranteed extraction of diagrams;
- no guaranteed reconstruction of complex tables;
- possible extraction-order issues;
- formatting differences between rendered PDF and extracted text.

Therefore, extracted PDF evidence requires traceability and human review.

Future document-understanding capabilities may add controlled handling of
tables and diagrams.


# 49. CORPORATE DEPLOYMENT DIRECTION

Corporate customers may require:

- local execution;
- private cloud;
- on-premises deployment;
- private LLMs;
- restricted document access;
- corporate authentication;
- audit logs;
- customer-specific knowledge bases;
- integration with internal software.

The current architecture should avoid unnecessary coupling to one external
LLM provider so these deployment models remain possible.


# 50. PUBLIC PLATFORM DIRECTION

The public RIOGINEER website is intended to evolve into an engineering
platform rather than remain only a corporate website.

The long-term user experience may include:

- selecting Digital Engineers;
- submitting specifications;
- generating process configurations;
- executing simulations;
- reviewing results;
- modifying process configurations;
- rerunning calculations;
- downloading engineering information.

Public capabilities may remain free.

Corporate customization and engineering support may constitute the main
commercial revenue source.


# 51. CURRENT BUSINESS MODEL

Current intended business model:

B2B engineering technology and services.

Public platform:

    free access to selected Digital Engineers and engineering models.

Paid corporate services may include:

- customization;
- integration;
- private deployment;
- corporate knowledge integration;
- new engineering modules;
- technical support;
- training;
- engineering studies;
- implementation projects.

This model may evolve based on customer validation.


# 52. CUSTOMER VALIDATION

Potential-customer validation is an important development activity.

Demonstrations should collect evidence regarding:

- usefulness;
- workflow compatibility;
- required features;
- trust;
- traceability;
- engineering-model requirements;
- deployment constraints;
- confidentiality;
- willingness to adopt;
- willingness to contract specialized support.

Customer interest must not be represented as a contract unless a contract
actually exists.

Pilot interest must not be represented as technical validation until the
relevant validation has occurred.


# 53. CENTELHA DEVELOPMENT CONTEXT

RIOGINEER is being proposed to Programa Centelha RJ as a new technology
company.

The development objective is to evolve the tested prototype toward a
higher-fidelity MVP validated with potential customers.

The technical development described in this document provides evidence of
prototype maturity.

Grant documentation must distinguish:

- current capability;
- planned capability;
- demonstrated capability;
- customer interest;
- future development.

Do not describe planned functionality as already operational.


# 54. CURRENT DEVELOPMENT PRIORITY

The immediate priority is NOT broader equipment support.

The first live end-to-end reference workflow has been manually demonstrated.
The immediate priority is to preserve its reliability and clear approval
feedback:

Natural-language specification
        ↓
LLM interpretation
        ↓
Evidence anchoring
        ↓
Structured requirements
        ↓
Human approval
        ↓
PFD
        ↓
Deterministic engineering calculation
        ↓
Verified results

using the Treinamento Bia three-phase separator reference case.


# 55. RESOLVED INTERPRETATION ISSUES

Source-evidence anchoring and supported-topology normalization are resolved
issues, retained here as engineering and architecture lessons.

A real provider may return an evidence excerpt that is semantically correct
but differs from the original source in:

- whitespace;
- line breaks;
- bullets;
- dash characters;
- punctuation.

The application uses provider evidence as a locator and anchors it
deterministically to the original source.

The authoritative stored evidence must be the original source substring.

Engineering values, units and identities must remain strictly protected.

Ambiguous evidence must not be silently accepted.


# 56. COMPLETED LIVE END-TO-END VALIDATION

The user manually completed the full Treinamento Bia specification through
the live LLM provider and web interface, including human review, explicit
approval of development-model assumptions, mandatory deterministic requirements
validation, structured flowsheet generation, read-only PFD and Python calculation.

Interpretation completed without missing information, ambiguities, conflicts
or false unsupported-capability warnings. Supported natural-language topology
is normalized locally to one feed, one three-phase separator and gas/oil/water
outlets; extra feeds, equipment, recycles and unsupported outlets remain blocked.

Manually observed results:

    FEED  = 110,000 kg/h
    GAS   = 22,000 kg/h
    OIL   = 77,550 kg/h
    WATER = 10,450 kg/h

Separator duty was 0 W. Component mass-balance checks passed; total
mass-balance residual was 0. The energy-balance check passed with residual 0 W.

This is the first complete live end-to-end Digital Engineer reference
demonstration, using Prescribed Component Recoveries — Development Model
and synthetic development assumptions, not I-ET or client data.

See MILESTONE_3.md for the manual observations, separate automated coverage,
reproducibility information and limitations.


# 57. AFTER END-TO-END VALIDATION

The first complete reference workflow has been demonstrated. Preserve its
regression basis and review model qualification before major new capabilities.

Recommended next areas include:

1. improved thermodynamic separator model;
2. additional equipment integration;
3. multi-equipment flowsheets;
4. recycle handling;
5. graphical PFD editing;
6. broader offshore process specifications;
7. Field Design integration.

The ordering should be reviewed after customer feedback.


# 58. DEVELOPMENT RULES FOR AI CODING AGENTS

Before major architectural changes:

1. Read this document.
2. Read the latest milestone reports.
3. Inspect existing code and tests.
4. Preserve validated engineering calculations unless explicitly authorized.
5. Do not duplicate engineering equations in the web frontend.
6. Do not silently introduce new physical assumptions.
7. Do not weaken provenance to make tests pass.
8. Do not invent unsupported equipment behavior.
9. Preserve regression fixtures.
10. Add regression tests for discovered failure classes.
11. Distinguish experimental code from validated capability.
12. Report limitations explicitly.


# 59. REFERENCE FOLDERS

Important existing development references include:

Treinamento Bia:

/Users/giovaninunes/Folders/FieldDesignCode/Simulation Repository/RioGineer/Treinamento Bia

Flowsheet 03:

/Users/giovaninunes/Folders/FieldDesignCode/Simulation Repository/Learning Flash/Flowsheet 03

Website repository:

/Users/giovaninunes/Folders/RioGineer/riogineer-website

Original reference folders should not be modified merely to support web
integration.

Use adapters and new architecture where appropriate.


# 60. DOCUMENT MAINTENANCE

This document is a persistent technical context, not a chronological chat
transcript.

Update it when:

- an architectural decision changes;
- a milestone is validated;
- a major engineering model is integrated;
- a limitation is removed or added;
- a major business/product direction changes.

Do not update it for every minor bug fix.

Detailed implementation history belongs in:

- Git history;
- milestone reports;
- diagnostic reports;
- tests;
- issue tracking.


# 61. CURRENT STATE SUMMARY

Milestone 7 adds the offline `riogineer_components@1.0` dataset and `molecular_composition@1.0` provider. Molecular flow, mixture molecular mass and molar fractions derive from existing component mass flows; all Milestone 3–6 process calculations and numbering remain unchanged. Results 1.5 add molecular provenance and component molar flows; requirements/flowsheet versions are unchanged and old result readers remain supported. Density and phase volumetric flows remain unavailable. No EOS or equilibrium is implemented. See `MILESTONE_7.md` for constants, provenance, benchmarks, validation and future provider boundaries. Human-operated Milestone 7 validation is pending.

Milestone 6 adds `compressor` / `ideal_gas_isentropic_efficiency@1.0` on the SEP_1 gas branch, with independent case `MILESTONE_6_GAS_COMPRESSION` and requirements 1.3 / flowsheet-results 1.4. Existing references and interpretation scope remain unchanged. The constant-Cp/k ideal-gas adapter distinguishes gas/process work from shaft power; mechanical losses are outside the material-stream energy boundary. The reference gas reaches 6000000 Pa absolute and 433.63373984623405 K; gas/shaft powers are 1619836.9468215914 / 1652894.8436955013 W. The Milestone 5 oil train is unchanged. No EOS, driver sizing or recycle capability was introduced. See `MILESTONE_6.md` for scope, independent benchmarks and automated validation; human-operated manual validation of Milestone 6 was completed on 2026-09-28 (see its manual record).

Milestone 5 adds the qualified deterministic `heater` adapter (`specified_outlet_temperature_constant_cp@1.0`) and independent `MILESTONE_5_SEQUENTIAL_PROCESS` reference: SEP_1 → HEATER_1 → SEP_2. Requirements 1.2 and flowsheet/results 1.3 extend existing readers without relabelling earlier cases. The heater preserves material/pressure and changes specified temperature; SEP_2 consumes its calculated output through the unchanged dependency scheduler. Recoveries remain independently prescribed, not predicted by heating. With the unchanged declared inputs, heater duty is 953883.333333… W; the requested informal benchmark was arithmetically inconsistent. See `MILESTONE_5.md` for equations, scope and validation. Natural-language interpretation remains unchanged; manual browser validation of Milestone 5 was completed on 2026-09-28 (see its separate manual record).


Current state:

- corporate website operational locally;
- Digital Engineer workspace implemented;
- Python engineering engine separated from website;
- three-phase separator deterministic reference working;
- requirements / flowsheet / results contracts implemented;
- typed specification interpretation implemented;
- PDF text interpretation implemented;
- live LLM provider configured;
- human review and approval implemented;
- provenance controls implemented;
- local normalization implemented;
- missing/conflict/ambiguity handling implemented;
- read-only PFD implemented;
- deterministic calculation implemented;
- automated regression testing extensive;
- graphical PFD editing not yet implemented;
- broader facility equipment support remains outside the web workflow;
- rigorous three-phase thermodynamics not yet integrated into this workflow;
- deterministic evidence anchoring and supported-topology normalization resolved;
- first live end-to-end reference workflow manually demonstrated (Milestone 3);
- explicit approval confirmation and validated PFD guidance implemented;
- numbered material streams and Engineering Stream Table implemented (Milestone 3.1);
- unavailable stream properties explicitly represented; no new thermodynamics;
- Milestone 4 deterministic acyclic graph execution implemented for registered
  three-phase separators, proportional splitters and equal-condition mixers;
- seven-stream 60/40 branch/rejoin reference available in Engineering data / Advanced;
- per-equipment and external material checks and scoped constant-Cp accounting;
- natural-language interpretation still limited to the single-separator profile;
- cycles, general thermal mixing and additional equipment remain unsupported.


# 62. IMMEDIATE NEXT STEP

Prepare separate user manual validation of Milestone 7 using the existing Milestone 6 reference (see MILESTONE_7.md). A separately approved next milestone may qualify Peng–Robinson + two-phase PT flash for methane/n_hexane; water-containing VLLE requires separate qualification.
Preserve all four independent deterministic references: the Milestone 3/3.1 Bia
single separator, the Milestone 4 acyclic separator → 60/40 splitter →
equal-condition mixer network, the Milestone 5 separator → heater → separator, and Milestone 6 with its parallel gas compressor. Review numbered internal streams, balances and
PFD/Stream Table consistency with engineering users. See MILESTONE_4.md for
contracts, exact results, model tolerances and validation.

The live specification → review/approval workflow remains scoped to a single
separator. Milestone 4 is an explicit deterministic Advanced reference and does
not broaden LLM interpretation, evidence anchoring or topology normalization.

Do not proceed automatically to recycle convergence, additional equipment or
full Flowsheet 03 migration. A future dedicated milestone may qualify one
analytically testable recycle. Topology and stable stream identity come first;
rigorous EOS-based thermodynamics requires separate qualification and scope.


# 63. END OF MASTER CONTEXT

This document should be treated as the primary persistent technical context
for future RIOGINEER development sessions.

When conflicts exist between this document and executable validated tests,
investigate the discrepancy rather than silently assuming either is correct.

Engineering truth must ultimately be established through explicit models,
validated data, reproducible calculations and documented engineering review.
