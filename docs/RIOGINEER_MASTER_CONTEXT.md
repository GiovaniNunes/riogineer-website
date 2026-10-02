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

M18 guarded configurable liquid pump implementation and automated qualification:
COMPLETE — 2026-10-01 within the two Pre-M18 studies' bounded scope. See
`MILESTONE_18.md` and `benchmarks/pump_energy/m18/`. Production model
`rigorous_isentropic_pump_pr@1.0` adds requirements 1.10 / flowsheet 1.11 /
results-process 1.12, engine 1.11.0, one source -> pump -> sink. Fixed equimolar
methane/n-hexane, explicit zero kij; Tin 300–350 K, Pin 20–25 MPa absolute,
Pout=Pin exactly or Pin+10,000 Pa through 30 MPa, eta 0.6–1, flow 5–200 mol/s.
Existing unchanged high_accuracy PT/calorics, full-domain PS and PH calculate
fluid power and actual outlet state. Three actual states require 300–370 K /
20–30 MPa, stable liquid and fresh same-T/z liquid witnesses at 16 MPa. Work
screening remains an engineering numerical allowance, not certified uncertainty.
Identity validates inlet/witness only, imposes zero work/duty and publishes null
isentropic reference/efficiency with not-applicable inverses. M7 molecular table
properties are populated for both streams; PFD, results and downloads agree.
Actual callable plus adapter passed 59 cases (43 accepted, 16 controlled rejects),
10,477 comparisons and 155 integrity/work-policy checks. Final regression evidence
covers 637 Python tests (full run plus documented affected-scope recovery), 268
TypeScript tests and 38 browser tests; schema, type, lint, format, build and smoke
passed. The hash-sensitive compressor class was rerun after source stabilization;
see the report for exact commands and other development/environment retries.
Both prerequisite studies, their frozen evidence, thermodynamic foundation and
incoming next-env.d.ts bytes are preserved. Human acceptance: COMPLETE —
2026-10-01, America/Sao_Paulo, operator Giovani Nunes. This is user-reported
acceptance from a user-operated browser session whose screenshots and off-grid
results.json were reviewed in ChatGPT, not independently operated/observed by
the closeout agent. Engine 127.0.0.1:8118 and frontend
http://127.0.0.1:3118/digital-engineer were used. Canonical, equal-pressure identity,
invalidation before Validate, 1,000 Pa sub-floor rejection, half-flow scaling,
off-grid operation and download agreement were confirmed. Previous general
results/balance statuses remained visible as stale; PFD/pump panel were hidden
and download/generation/calculation disabled. No new accepted result appeared
on rejection. Exact 10,000 Pa floor remains automated-only evidence.
Off-grid export run e8084a35-c661-45ba-a827-247baa2032d6, input SHA-256
d77f0eb947d1f99a25a552fa537fce9add9d5a85fa8cb6bb6ebf5451adaacae3;
Tout=308.665248379672 K, fluid power=33292.48812016267 W, eta=0.7131999999999931,
energy residual=-4.3655745685100555e-11 W within 2.2379900405281102e-8 W.
Mass/energy passed; PS/PH succeeded; density/volumetric properties remained
unavailable. No claim is made that screenshots/export are stored in this repo.
See MILESTONE_18.md for all supplied observations and evidence attribution.
The user authorized normal commit/push of the verified 57-file scope (26 M18,
31 prerequisite paths); next-env.d.ts is excluded and untouched during closeout.
Prior cumulative testing and recovery history are retained. Acceptance does not
expand qualification. Deployment and M19 remain unauthorized.
No general fluid coverage, global convergence/phase proof, experimental pump
validation, sizing, head/curves, NPSH, cavitation or electrical model is claimed.
The Pre-M18 entries below describe their historical study-only completion.

Pre-M18 configurable-scope extension: COMPLETE — 2026-10-01. See
`PRE_MILESTONE_18_CONFIGURABLE_PUMP_SCOPE_QUALIFICATION.md` and
`benchmarks/pump_energy/configurable_scope/`. Numerical evidence supports fixed
equimolar methane/n-hexane, zero kij, inlet 300–350 K / 20–25 MPa, discharge up to
30 MPa, eta 0.6–1 and continuous flow 5–200 mol/s. Exact equal pressure is a
separate identity; positive rise requires at least 10,000 Pa plus runtime work
screening. All three states require 300–370 K / 20–30 MPa, stable liquid and
fresh same-temperature 16 MPa liquid PT witnesses. The fixed boundary ceiling
is a conservatively supported engineering policy, not a proven global envelope.
The extension records 46 candidate entries, eight off-grid holdouts, 149 boundary
temperatures, 5,522 passing checks and 13 focused tests; numerical artifacts
reproduce byte-for-byte. Four alternate saturation-inverse branch returns are
retained and investigated separately. Prior evidence and production solvers are
unchanged. A guarded configurable pump implementation can be separately scoped;
no pump, contract or interface is implemented, and M18 is not complete. The
first-study record below remains historical evidence, not the latest scope limit.

Pre-M18 liquid PS/PH pump-path prerequisite study: COMPLETE FOR A NARROWER
ENUMERATED SCOPE — 2026-10-01. See
`PRE_MILESTONE_18_LIQUID_PUMP_PATH_QUALIFICATION.md` and `benchmarks/pump_energy/`.
Twenty candidates yield 13 accepted production tuples, two controlled PS scan
failures, three unresolved-small-work cases and two non-liquid inlet rejections;
1,215 applicable comparison checks and 18 focused tests passed. Independent and
production artifacts reproduce byte-for-byte. The 8 MPa boundary paths remain
blocked by two PT holes in the full PS scan; separate PH diagnostics do not rescue
them. Stability/PIP alone cannot exclude saturation or supercritical service, so
the proposed admissibility policy is the exact accepted input set, not a continuous
operating envelope. Production solvers, contracts and UI are unchanged. No pump
is implemented or registered; M18 is not complete, and no experimental or cavitation
validation is claimed. Broader inputs or inclusion of the blocked paths need
separate prerequisite qualification before implementation.

Milestone 17 automated implementation and qualification: COMPLETE — 2026-10-01: `equilibrium_separator_energy_pr@1.0`
extends the existing M9 separator using M10 calorics and the shared M11/M16 PH
solver. Requirements 1.9 / flowsheet 1.10 / results 1.11 add explicit separator
pressure with specified-temperature PT (calculated duty) and adiabatic PH (zero
duty, calculated temperature). Actual PT-defined positive-flow inlet and separate
vapor/liquid material outlets are conserved; absent-phase intensive properties are
unavailable and enthalpy-flow contributions are zero. Independent Pre-M17 evidence
establishes 24 cases, L/V/VL inlet/outlet service within the frozen methane/n_hexane
zero-kij matrix, and 969 production comparisons. M9 material-only null-energy
semantics and development models remain intact. No water, three-phase model, pump,
separate KO solver, sizing, hydraulics, recycles or mixed rigorous network is added.
See `MILESTONE_17.md` and `PRE_MILESTONE_17_TWO_PHASE_SEPARATOR_ENERGY_QUALIFICATION.md`
for equations, provenance, tolerances, reproduction and completion checks.
Original implementation evidence (2026-10-01): all 620 Python, 265 TypeScript and 36 browser tests passed, along with six
independent tests, byte-identical reference/production-evidence verification,
schema parity, lint/types/format, final build and smoke.

User-operated M17 checks were reported on 2026-10-01, with screenshots reviewed in
the accompanying ChatGPT discussion (not agent-performed manual testing; no local
screenshot files claimed). PT: 300,000 Pa absolute, specified 350 K, feed
18,399.2688 kg/h, vapor approximately 15,585.658223 kg/h, liquid approximately
2,813.610577 kg/h, calculated Q approximately +1,832,535.619763 W, balances passed.
PH: 1,000,000 Pa absolute, calculated T approximately 291.74213866 K, vapor
approximately 3,001.467851 kg/h, liquid approximately 15,397.800949 kg/h, imposed
Q=0 W, balances passed and results current. Changing only separator pressure to
30,000,000 Pa and recalculating gave approximately 300 K, liquid 18,399.2688 kg/h,
vapor 0 kg/h, Q=0 W and passing balances; the dedicated panel retained zero absent
vapor material/molar/enthalpy flows and unavailable composition/specific enthalpy.
Editing pressure back to 1,000,000 Pa without recalculating removed result panels,
set results (not current)/flowsheet JSON to null, disabled PFD/calculation and
showed Requirements await validation. These reported manual checks are complete.

The new browser reproduction differs in one reported UI detail: a same-case edit
retains raw results labelled not current and a generic STALE section, with the
Previous results are stale warning; the dedicated panel disappears, flowsheet
clears and buttons disable. This is the unchanged workflow reducer behavior;
case-identity changes clear results. The manual observation remains recorded as
reported, with its JSON/status difference unresolved, not silently equated to the
new automated reproduction. No stale-result workflow change was made.

The same session exposed missing general-table molecular properties. M17's
serializer had filled all stream properties as unavailable while its dedicated
panel used separate thermodynamics fields. The correction populates existing
molar-flow, molecular-mass and molar-composition fields using unchanged M7 qualified
infrastructure: kmol/h = mol/s × 3.6, molecular mass in kg/kmol. Absent vapor retains
zero extensive flows and unavailable intensive properties; density/volumetric
quantities remain unavailable. The legend now explains both unavailable cases.
No solver, numerical tolerance, contract version or qualified scope changed.
Human review of this subsequent correction was not yet reported at the
implementation closeout; completed visual acceptance is recorded below.

New correction checks: 29 focused Python tests (12 M17, seven M9, ten M7), all 265
TypeScript tests, three focused M17 browser workflows, the final full 37-browser
suite and 24-case/969-comparison frozen production verification passed. Schema
parity, lint/types/format, diff checks, final production build and smoke passed.
Before/after PT, PH and equal-pressure engineering outputs matched exactly apart
from intended property enrichment and run/code fingerprints. Frozen artifact hashes
are unchanged (recorded in `MILESTONE_17.md`). The original 620-test full numerical
suite and six independent tests remain dated evidence, not newly rerun tests.
The updated complete inventory is 31 files (13 tracked modifications, 18 new);
follow-up files and final gates are detailed in `MILESTONE_17.md`. Commit and normal
push were explicitly authorized; actual identity/outcome belong to Git history
and the closeout report. No deployment or M18 work is included. Earlier entries
below are historical status records, not current capability exclusions.

Visual acceptance of the corrected molecular table: **COMPLETE — 2026-10-01,
America/Sao_Paulo**, for the three cases below. Giovani Nunes reported manually
executing the corrected interface. Screenshots were supplied to and reviewed in
the ChatGPT design conversation. This is user-operated evidence with screenshot
review in ChatGPT, not manual execution or direct screenshot inspection by this
Codex session. No screenshots are claimed to be stored in the repository.

All three cases displayed current results and passing mass/energy checks:

- **PT reference:** feed 360 kmol/h and molecular mass 51.10908 kg/kmol;
  liquid 32.85692419 kmol/h; vapor 327.14307581 kmol/h. Molecular masses and mole
  fractions populated consistently. Calculated duty: +1832535.619763 W.
- **Adiabatic PH at 1000000 Pa:** calculated temperature approximately
  291.74213866 K; liquid 187.40076793 kmol/h; vapor 172.59923207 kmol/h.
  Molecular masses and mole fractions populated consistently. Imposed duty: 0 W.
- **Equal-pressure adiabatic PH at 30000000 Pa** (separator pressure equals inlet
  pressure): calculated temperature approximately 300 K; liquid 18399.2688 kg/h
  and 360 kmol/h; liquid molecular mass 51.10908 kg/kmol; liquid mole fractions
  methane 0.5 and n-hexane 0.5. Absent vapor had zero mass, molar, component and
  enthalpy flows. Vapor molecular mass, mass/mole fractions and specific enthalpy
  displayed unavailable (—). Imposed duty: 0 W.

The subsequent molecular-table correction is now visually accepted for these
three cases; no discrepancies were reported in the supplied screenshots. This
acceptance does not broaden the documented qualification scope or supersede the
prior distinction between stale results retained as “not current” and cleared
results. Prior automated evidence remains unchanged. This documentation-only
registration did not rerun numerical or browser regression suites.

Milestone 16 automated acceptance: COMPLETE — 2026-09-30. Human-operated M16 validation: COMPLETE — 2026-09-30, separately reported by the reviewer after executing and inspecting canonical, pressure, flow, phase, negative and summary --verify. All reviewed modes passed, including PRESSURE_FLASH_ONSET, flow invariance, phase/service-scope behavior and all 38 negatives; the final summary confirmed 17 positives, 38 negatives, 572 numerical comparisons and eight byte-identical call-order checks. The five separate thermodynamic studies remain outside primary equipment-service qualification. The separately authorized `rigorous_isenthalpic_pr@1.0` valve uses requirements 1.8 / flowsheet 1.9 / results 1.10, actual inlet material flow/composition, high_accuracy PT/M10 → H target = H inlet → shared PH/M11 → fresh final acceptance, and one overall material outlet including qualified VL states. Against unchanged Pre-M16 evidence, 17 primary cases, 38 negatives, 572 primary comparisons, five separate studies (130 comparisons), eight byte-identical call-order checks and fresh production-artifact reproduction passed. The general PH correction partitions the unchanged 128-point 200–500 K scan at controlled PT failures, discovers candidates only inside valid intervals and rejects global ambiguity; it enables PRESSURE_FLASH_ONSET without hard-coded intervals or PT/EOS/tolerance changes. Only the separately authorized M11 early-abort implementation assertion changed; PH numerical evidence remains unchanged. All 609 Python, 260 TypeScript and 34 browser tests, schema parity, lint/types/format, build and smoke passed. Scope remains the frozen methane/n_hexane, explicit-zero-kij, tested pressure matrix with single-liquid/single-vapor inlet and qualified L/V/VL outlet; VL inlet, unsupported coexistence gaps and root-relevant property holes remain rejected. No sizing, Cv/Kv, flow prediction, shaft power, heat-duty/efficiency model, hydraulic/network pressure solution, non-equilibrium flashing or automatic separation is added. No M17 work has begun. See `MILESTONE_16.md` for the complete limitations, authorization history, protected-file inventory, numerical tables and tested review commands. Earlier milestone statements below describing M16 as unimplemented retain their historical meaning.

Independent Pre-M16 automated qualification: COMPLETE. Human-operated Pre-M16 validation: COMPLETE — 2026-09-30, separately reported by the reviewer after inspecting canonical, pressure, flow, phase, negative and summary; all reviewed modes passed. Production M16: NOT IMPLEMENTED. The independent `independent_throttling_valve@1.0` Peng–Robinson reference qualifies isenthalpic methane/n_hexane throttling with explicit zero kij within the frozen pressure/case matrix and 200–500 K domain: 17 primary cases, five separate studies, 38 negatives, 1,633 numerical checks and 12 byte-identical call-order checks. Automated evidence remains 54 independent tests, nine fresh-process verifications, 571 read-only production PT/PH comparisons and 532 unique historical production tests. Initial recommended service is single-liquid/single-vapor inlet with qualified liquid/vapor/VL outlet; VL inlets and boundary perturbations remain separate studies. `PRESSURE_FLASH_ONSET` is qualified only on the explicit 280–350 K interval; the independent property hole remains unavailable, without bridging or interpolation. Frozen SHA-256: `ef0141ec3b72740175553381f2e0431290a0fa8eb937bd03ad0259a9aa2dbead`. No water/general-mixture/nonzero-BIP, VLLE/three-phase, non-equilibrium flashing, kinetic/potential correction, heat transfer, shaft work, valve efficiency, sizing, cavitation/erosion/noise or automatic phase separation is qualified. Future production requires a separately authorized additive contract branch; no production valve, contract or topology change is implemented. See `PRE_MILESTONE_16_THROTTLING_VALVE_QUALIFICATION.md` for the separate automated/human records, investigation, full limitations and tested commands.

Independent Pre-M15 two-stream heat-exchanger automated qualification is COMPLETE against baseline `e17490f1b470645e9a042086d9330d52c90507de`: 19 primary cases, six separate phase studies, 79 negatives, 2,002 numerical comparisons, 116 independent tests and 12 byte-identical call-order checks passed; fresh frozen reproduction and unchanged historical protection, including all 414 Python tests, passed. The independent methane/n-hexane, constant-zero-kij, bounded 200–500 K evidence qualifies signed side-specific enthalpy balances with separate material streams and reciprocal hot- or cold-outlet-temperature specifications. Recommended initial M15 scope is single-phase inlet/outlet states only, rejecting terminal crossing under `Thi > Tco`, `Tho > Tci`, `Tho >= Tco`; phase changes remain separate thermodynamic studies, with no design-feasibility or minimum-approach claim. Pre-M15 required a separate additive four-port contract/topology authorization before production implementation; M15 records that completed gate below. No production code, contracts or historical evidence changed. Frozen SHA-256: `533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1`. Human-operated Pre-M15 validation: COMPLETE — 2026-09-30, separately reported by the reviewer after inspecting canonical, reciprocal, flow, phase, zero_duty, temperature_scope, negative and summary modes. All reviewed modes passed within frozen allowances; phase changes remain separate studies rejected from primary scope, and all 79 negatives published no accepted complete exchanger result. Production M15 automated status is recorded below. See `PRE_MILESTONE_15_TWO_STREAM_HEAT_EXCHANGER_QUALIFICATION.md` for independent methodology, allowances, limitations and tested review commands.

Milestone 15 automated acceptance: COMPLETE — 2026-09-30. `rigorous_two_stream_pr@1.0` adds an authorized requirements 1.7 / flowsheet 1.8 / results 1.9 branch with `hot_in`, `hot_out`, `cold_in`, `cold_out`, independent material paths and atomic outputs. Mode A specifies hot outlet temperature; Mode B specifies cold outlet temperature. Existing high_accuracy PT/M10 and PH/M11 supply fresh terminal states and signed energy balances. Qualification against unchanged `independent_two_stream_heat_exchanger@1.0` passed 19 primary cases (including LIQUID_BOTH), 79 negatives, six phase-study service rejections, 1,165 numerical comparisons and 12 byte-identical call-order checks; 113 focused and 532 complete Python tests, 231 TypeScript tests, 33 browser tests, historical comparators, build and smoke passed. Scope remains the frozen methane/n_hexane, constant-zero-kij, bounded 200–500 K monophase endpoint matrix, rejecting pressure gain, reversed heat direction and terminal crossing. No phase-change service, UA/LMTD/NTU, minimum-approach design rule, sizing, hydraulic correlation, recycle algorithm or broader thermodynamic scope is added. Frozen Pre-M15 SHA-256 remains `533797cb1b26a8f3e597907ab9cc1e480353bd189280cfde273157cd3fa0e4b1`. Human-operated M15 validation: COMPLETE — 2026-09-30. The human reviewer inspected canonical, reciprocal, phase, zero_duty, temperature_scope, negative and summary --verify; all passed, confirming the recorded 19 primary positives, 79 negatives, six excluded phase studies, 1,165 numerical comparisons and 12 byte-identical call-order checks within frozen allowances. This is a separate human-validation record; automated evidence and qualification limits remain unchanged. See `MILESTONE_15.md` for evidence, explicit historical fixture type authorizations, integrity inventory and tested review commands. No M16 implementation.

Milestone 14 adds the separately authorized production `rigorous_isentropic_pr@1.0` compressor while preserving `ideal_gas_isentropic_efficiency@1.0` and all historical numerical semantics. Automated M14 acceptance is COMPLETE — 2026-09-30: 19 vapor positive cases, 43 negative cases, one separate VL-study service rejection, 1,083 numerical comparisons, 18 byte-identical call-order checks and fresh production-artifact reproduction passed against unchanged Pre-M14 evidence. Requirements 1.6, flowsheet 1.7 and results 1.8 provide additive versioned support. Runtime composition is inlet high_accuracy PT/M10 -> H1,S1; PS/M13 -> H2s; isentropic efficiency -> H2 target; PH/M11 -> actual outlet; M7 molar flow -> fluid power. Positive fluid power enters the material stream; mechanical/driver losses are not calculated. Qualification remains one source -> compressor -> sink, single-vapor methane/n-hexane service with explicit constant zero kij within the frozen bounded 200–500 K matrix; liquid/VL service is rejected. No maps, polytropic model, multistage/intercooling, sizing or network pressure solution is implemented. The complete Python suite (414), TypeScript suite (219), browser suite (32), historical regressions, repository gates and production smoke passed. M14 human-operated validation: COMPLETE — 2026-09-30, separately reported by the human reviewer after inspection of canonical, efficiency, pressure, flow, ideal, service_scope, negative and summary modes. All reviewed modes passed, including the recorded numerical allowances, 43 failures without accepted outlets, vapor-only service boundary and 18 byte-identical call-order checks. Automated acceptance and human validation are both complete within the existing qualification limits. See `MILESTONE_14.md` for exact scope, contract fields, numerical evidence, integrity checks and tested review commands.

Pre-Milestone 14 independent PR compressor qualification is complete: automated qualification passed on 2026-09-30. Human-operated Pre-M14 validation: COMPLETE — 2026-09-30. The reviewer separately confirmed the canonical, efficiency, pressure, flow, ideal, pure, boundary, negative and summary modes, consistent with the frozen evidence: 19 vapor positive cases, 1 separate VL thermodynamic study, 43 negative cases, 918 independent numerical checks and 18 byte-identical call-order checks. The frozen reference SHA-256 is `31972f6057f1c4191e25dc8fec317a0e21b20816d0a7c6513649fb7b630ed8cc`. Qualification remains limited to the documented methane/n-hexane, constant-zero-kij, bounded 200–500 K, adiabatic isentropic-efficiency matrix. Initial compressor service remains vapor-only; liquid/VL inlets are rejected as equipment service, and the separate VL study does not authorize broader service. Existing limitations and the requirement for separate authorization of future protected contract changes remain intact. See `PRE_MILESTONE_14_COMPRESSOR_QUALIFICATION.md` for separate automated and human records.

Milestone 13 adds standalone production `flash_PS` to `peng_robinson@1.0`: `P + S_target + z -> T + equilibrium state + H_eq`. Automated acceptance passed on 2026-09-30 against the unchanged committed Pre-M13 methane/n_hexane, explicit-constant-zero-kij matrix: 15 positive cases, 17 negative cases and 270 field comparisons; 55 focused PS tests and 339 complete Python tests passed. The bounded 200–500 K inversion uses a complete 64-point scan, bisection with at most 100 iterations and 1e-10 K internal tolerance, existing high_accuracy PT and M10 entropy/enthalpy, and a fresh final entropy residual <=1e-8 J/(mol K). Bubble/dew-adjacent and qualified pure states pass; pure coexistence gaps, ambiguity and property holes fail without accepted state. Frozen evidence and historical numerical behavior remain unchanged; the obsolete M11 PS-absence capability assertion was minimally updated under explicit authorization. Qualification is limited to the frozen pressure/composition matrix, with no mathematical global uniqueness, water, arbitrary petroleum mixture/nonzero BIP, VLLE, three-phase, critical-region or pure coexistence interpolation claim. M13 does not implement compressor, turbine, valve, equipment energy integration or a process-contract PS specification. Human-operated M13 validation is separately COMPLETE — 2026-09-30, as reported by the human reviewer. See `MILESTONE_13.md` for automated gates, the human validation record, integrity evidence and reproduction commands. Earlier milestone statements about PS unavailability describe their historical scope; current standalone PS status is recorded here.

Milestone 12 adds `heater` / `equilibrium_energy_balance_pr@1.0` alongside the unchanged historical `specified_outlet_temperature_constant_cp@1.0` model. Automated acceptance passed on 2026-09-29 against the unchanged independent Pre-M12 evidence: 14 positive cases, 15 controlled negatives and 1,264 production comparisons. Specified T_out uses PT/M10 caloric properties to calculate Q; specified Q calls M11 PH to recover T_out and equilibrium state. M7 converts runtime mass flows to mol/s; component flows and overall composition are conserved. P_out is specified, not hydraulically calculated. Phase transitions belong to the property package. Requirements 1.5, flowsheet 1.6 and results 1.7 add explicitly discriminated contracts while preserving historical readers and M9 semantics. Integration is limited to one source → heater → sink; no network energy solver, sizing, hydraulic delta-P, utility-side modeling or broad Stream Table enrichment is implemented. Methane/n_hexane with explicit zero kij remains the qualified scope. Separately, human-operated M12 validation was successfully completed on 2026-09-29, as reported by the reviewer: Mode A, Mode B using M11 flash_PH/high_accuracy, zero duty, flow scaling, all four qualified phase-transition directions, all 15 controlled negatives without accepted outlets, and the beginning/end of the complete summary were inspected. The summary reported 14 positive cases, 15 negative cases and 1,264 passing comparisons, zero scaling error, and successful determinism/call-order checks; dew-adjacent Mode B remained within frozen allowances. M12 automated acceptance: COMPLETE. M12 human-operated validation: COMPLETE — 2026-09-29. See the separate manual record in `MILESTONE_12.md`; qualification boundaries and the distinct historical constant-Cp model remain unchanged.

Milestone 11 adds standalone production `flash_PH` to `peng_robinson@1.0`, reusing explicit high_accuracy PT and M10 caloric properties. Automated acceptance passed on 2026-09-29 against the unchanged frozen Pre-M11 methane/n_hexane, explicit-zero-kij matrix: all 29 positive cases, eight negative specifications and the pure n-hexane coexistence-gap rejection passed. A deterministic 128-point 200–500 K scan and bounded bisection require a fresh final enthalpy residual; finite sampling does not prove global uniqueness. M8.1/M8.2 restart behavior is inherited through PT, and the nine-grid 1,152-state PT scan remains successful. Separately, human-operated M11 validation was successfully completed on 2026-09-29, as reported by the reviewer: canonical A/B/C, bubble/dew-adjacent and near-zero-H results passed with explicit HIGH_ACCURACY PT; the complete summary confirmed all 29 positive cases, nine controlled negative/gap rejections without accepted payload and 401 positive field comparisons. The human review confirmed phase-state agreement, the unchanged dew-side liquid-enthalpy allowance and the expected bubble/dew phase-transition sequence. M11 automated acceptance: COMPLETE. M11 human-operated validation: COMPLETE — 2026-09-29. See the separate manual record in `MILESTONE_11.md`; the existing qualification scope is unchanged. Process equipment energy integration and PS remain unavailable; water PH and coexistence interpolation remain unqualified.

Milestone 8.2 extends the existing production PT restart to both independently qualified orientations: liquid-parent/vapor-trial uses K=S*w/z and vapor-parent/liquid-trial uses K=z/(S*w). Automated acceptance passed on 2026-09-29: all four former failures, both profiles across the 13-state neighborhood, historical regressions and the complete nine-grid high_accuracy PT scan (1,152/1,152 successes, zero unexplained holes). The explicitly reviewed historical no-recovery test now verifies qualified recovery while preserving controlled-failure coverage. EOS, RR, stability mathematics, caloric properties, frozen evidence and process contracts remain unchanged. See `MILESTONE_8_2.md`. Separately, human-operated M8.2 validation was successfully completed on 2026-09-29, as reported by the reviewer: representative and all four former failures passed both profiles and frozen field comparisons; both restart orientations coexist; normal-Wilson and stable-vapor controls retain zero restarts; near-boundary behavior, isolation, determinism and call order were confirmed. The complete high_accuracy scan reported 9 grids, 1,152/1,152 successes, zero unexpected failures and restart counts of four vapor-parent/liquid-trial and one liquid-parent/vapor-trial. The manual record and reported frozen-reference hash are in `MILESTONE_8_2.md`, separate from automated coverage and limited to the existing M8.2 scope. M8.2 automated acceptance: COMPLETE. M8.2 human-operated validation: COMPLETE — 2026-09-29. M8.2 itself adds no PH/PS capability or process energy integration; standalone M11 PH status is recorded above.

Milestone 8.1 adds a single stability-derived PT initialization restart when converged instability conflicts with an initial Wilson RR endpoint tendency. The qualified positive-binary liquid-parent/vapor-trial mapping uses runtime stationary TPD evidence and existing EOS phase identification. Immutable internal standard/high-accuracy controls retain 1e-11 as the default and explicitly offer 1e-12. RR semantics, EOS/caloric equations, historical accepted M8/M9/M10 results, process equipment, contracts and UI remain unchanged. Automated M8.1 acceptance passed on 2026-09-29. Separately, human-operated M8.1 validation was successfully completed on 2026-09-29, as reported by the user: bubble-center and dew-precision reviews each reported PASS for 325 comparisons, confirming the single stability-derived restart, explicit precision profiles, approximately 9.729× downstream margin and deterministic isolation/repeatability. The expected standard caloric diagnostic failure is not a high-accuracy acceptance gate. The manual record remains limited to the defined M8.1 scope. See `MILESTONE_8_1.md` and its production comparison against the unchanged committed Pre-M8.1 reference. M8.1 itself did not implement PH/PS; standalone M11 PH status is recorded above, and PS remains unavailable.

Milestone 10 adds opt-in `phase_caloric_TP` and `equilibrium_caloric_PT` capabilities to `peng_robinson@1.0`, using the separate offline `riogineer_caloric@1.0` Cp dataset and existing M8 EOS derivatives/root selection. Production methane/n_hexane phase and equilibrium H/S reproduce the independent pre-M10 caloric reference. Reference conventions and explicit failures remain traceable. This is property qualification only: no PH/PS solver, process equipment energy integration, UI/contract change or water/VLLE support. M9 process enthalpy/duty semantics remain unavailable. See `MILESTONE_10.md` for comparison evidence and scope. Human-operated M10 validation was successfully completed on 2026-09-29, as reported by the user, covering Cases A/B/C and pure methane/n_hexane; all five runs reported PASS for 1526 comparisons with no FAIL observed. The manual record is separate from automated coverage in `MILESTONE_10.md` and remains limited to the defined M10 scope. M10 itself did not implement PH/PS or process integration; standalone M11 PH status is recorded above.

Milestone 9 adds a separate `equilibrium_separator_2phase` / `pt_flash_separator@1.0` and controlled `MILESTONE_9_PT_FLASH_SEPARATOR` reference. Actual inlet mass flows pass through M7 Composition into the qualified M8 `peng_robinson@1.0` PT provider; phase results become mass-basis outlet streams and independently reconstructed molecular properties. Case B uses 300 K, 300000 Pa, 1000 kmol/h equimolar methane/n_hexane with explicit zero kij; Cases A/C qualify zero-flow absent-phase semantics. Requirements 1.4 / flowsheet 1.5 / results 1.6 preserve older readers. Energy/duty, density and phase volumetric flows are unavailable. Existing prescribed separators, heaters and compressors remain unchanged. See `MILESTONE_9.md` for scope, results, tolerances and automated evidence. Human-operated M9 browser validation was successfully completed on 2026-09-29, as reported by the user and recorded separately from automated coverage in `MILESTONE_9.md`; acceptance is limited to the defined M9 scope.

Milestone 8's standalone PR EOS and stability remain unchanged; its PT flash now has the separately scoped M8.1 initialization/precision controls above, preserving the qualified independent A/B/C results. Its human-operated comparison was completed on 2026-09-28 (see `MILESTONE_8.md`). Water/VLLE and PS remain unsupported; M10 adds property-layer caloric evaluation and M11 adds separately qualified standalone PH as recorded above.

Milestone 7 adds the offline `riogineer_components@1.0` dataset and `molecular_composition@1.0` provider. Molecular flow, mixture molecular mass and molar fractions derive from existing component mass flows; all Milestone 3–6 process calculations and numbering remain unchanged. Results 1.5 add molecular provenance and component molar flows; requirements/flowsheet versions are unchanged and old result readers remain supported. Density and phase volumetric flows remain unavailable in process results. No EOS or equilibrium was implemented in M7. See `MILESTONE_7.md` for constants, provenance, benchmarks, validation and future provider boundaries; its human-operated validation was completed on 2026-09-28.

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

Current handoff (2026-10-01): M19 is user-accepted by Giovani Nunes within the
documented guarded scope; see the dated M19 acceptance/closeout entry below.
The 37 verified M19 paths are authorized for normal commit/push. Preserve the
current next-env.d.ts and tsconfig.json bytes outside the commit and leave user
services untouched. Await a separately scoped next request; no M20 or deployment.

Historical M18 handoff: M18 numerical qualification and user-reported human acceptance
are complete within the documented guarded scope. Giovani Nunes authorized
repository closeout (normal commit/push of implementation and both prerequisites).
Preserve the unrelated next-env.d.ts bytes outside the commit and leave running
services untouched. Await a separately scoped next request; no M19 or deployment
is authorized. Earlier study handoffs below are historical and superseded by the
M18 implementation and acceptance records above.

Latest follow-up: the configurable Pre-M18 extension supports the guarded ranges
above. Await a separate production-pump implementation request. Earlier handoff
records below are retained; no implementation is authorized by study completion.

The separately authorized Pre-M18 benchmark-only study is now complete for the
restricted cases described above. Await a separate request for pump implementation
or broader liquid admissibility/PS qualification; no production M18 work has begun.

M17 user-operated engineering checks and completed visual acceptance of the
corrected general Stream Table are recorded in `MILESTONE_17.md` (2026-10-01,
America/Sao_Paulo), limited to the three reviewed cases.
Use that document for reproduction and closeout evidence. Await a separately scoped
next request; no M18 implementation is authorized by this closeout. Preserve
historical M1–M16 accepted workflows and independent references. Live specification interpretation remains on its existing
reviewed development-model scope; M17 adds deterministic Advanced demonstrations,
not broader natural-language topology interpretation.

Future knockout service can reuse the two-phase thermodynamic core with explicit
service qualification. Future three-phase work may treat oil/water as mutually
immiscible, without mutual solubility or a full VLLE requirement, but still needs
qualified water caloric/phase assumptions. Water is excluded from current PR.
Mixed rigorous networks, pump qualification and recycles require separate scope;
none is implied by M17 or by the legacy Flowsheet 03 experiments.


# 63. END OF MASTER CONTEXT

This document should be treated as the primary persistent technical context
for future RIOGINEER development sessions.

When conflicts exist between this document and executable validated tests,
investigate the discrepancy rather than silently assuming either is correct.

Engineering truth must ultimately be established through explicit models,
validated data, reproducible calculations and documented engineering review.

# M19 — variable-composition liquid pump (human-accepted 2026-10-01)

M19 extends the pump through `rigorous_isentropic_pump_pr@2.0` and a separate
`variable_pump_energy` profile. Requirements 1.11, flowsheet 1.12, results/process
1.13, branch engine 1.12.0. M18 model 1.0 retains fixed equimolar semantics and its
frozen files/evidence. New scope: methane mole fraction 0.01–0.55 with n-hexane
balance, explicit constant zero kij, mass-rate-derived composition. M18 inlet
300–350 K / 20–25 MPa, eta 0.6–1, F 5–200 mol/s, exact identity or ≥10000 Pa rise
through 30 MPa remain unchanged. Reached states 300–370 K and fresh 16 MPa witnesses
were independently requalified across composition; all runtime numerical and
liquid-service guards remain mandatory. Shared thermodynamic solvers are unchanged.

Independent evidence: 53 accepted / 11 rejected pump cases, 824 boundary checks,
13,607 actual callable/adapter comparisons passed; reference reproduced byte-for-byte.
Finite sampling and engineering witness reserve are not a global proof or
experimental validation. All 24 historical M17 separator cases fail direct-entry
requirements or have no liquid. One additional high-pressure full-liquid case is
compatible; representative low-pressure fractionated products still require new
pressure/state/saturation-margin qualification. Production mixed networks remain
out of scope. At implementation handoff, no commit/push/deployment had occurred
and human acceptance was pending; the dated acceptance entry below supersedes
that status.

See [MILESTONE_19.md](../MILESTONE_19.md) for verification, versions, startup/manual
acceptance and exact inventory; see
[qualification](../PRE_MILESTONE_19_VARIABLE_COMPOSITION_PUMP_QUALIFICATION.md)
for independent methodology, phase/work evidence and separator gaps.

## M19 human acceptance and closeout — 2026-10-01, America/Sao_Paulo

Giovani Nunes reports acceptance based on browser operation, screenshots and the
exported canonical JSON reviewed in the accompanying ChatGPT conversation. These
are user-reported observations, not new automated tests or checks personally
performed by the closeout agent. The screenshots/export are not included in this
commit. The precise record is in the dated acceptance section of MILESTONE_19.md.

Reported M19 canonical values: model 2.0, z=0.25/0.75, 300 K and 20 MPa inlet,
30 MPa discharge, eta 0.8, 360 kmol/h (100 mol/s), 24,711.1992 kg/h and
68.64222 kg/kmol. Outlet ≈304.097803733 K; fluid power ≈132,548.174119273 W;
heat duty 0 W. Mass/energy passed, results current, exported JSON agreed and
identified results 1.13 / engine 1.12.0. Density and phase volumetric flows were
unavailable. Feed edits left previous results visible with STALE/previous-calculation
warnings and disabled download; they did not clear all historical results.

Methane/hexane rates 3465.2448/12409.25184 kg/h (z methane 0.60) were rejected with
`composition_scope` and qualified interval 0.01–0.55; historical results remained
stale and download disabled. Restoring M19 and setting Pout=Pin=20 MPa yielded
300 K, zero work/duty, unchanged flow/composition/enthalpy flow, zero mass/energy
residuals and passed checks; results current/download enabled. Ideal reference
and reconstructed efficiency were unavailable for identity/zero work. Setting
Pout=20.001 MPa (1000 Pa rise) returned `positive_rise_below_floor`, disabled PFD,
calculation and download, and retained historical results marked STALE.

Historical M18 model 1.0 remained equimolar: outlet ≈305.581525034 K, fluid power
≈110,622.860113396 W, reconstructed eta 0.8, passed checks and current results.
With that M18 model retained, methane/hexane rates 1443.852/23267.3472 kg/h gave
`composition_scope; Fixed equimolar methane/n_hexane required`; PFD/calculation/
download were disabled and previous results stale. M18 semantics remain intact.
Unreported reproduction-checklist items are not marked manually observed.

All existing composition, zero-kij, temperature, pressure, efficiency, flow,
phase/witness, inverse, residual and work limits remain. Finite sampling does not
guarantee convergence at every intermediate input; numerical agreement is not
experimental validation. Low-pressure fractionated separator-product integration
remains unresolved. No mixed networks, sizing, NPSH, cavitation or electrical
power capability is added.

Closeout authorizes exactly 37 verified M19 paths for commit and normal push.
The additional local tsconfig.json generated type includes/formatting and the
pre-existing next-env.d.ts modification are both preserved outside the commit.
Lightweight inventory, integrity, schema-parity, formatting and whitespace checks
are distinct from the unchanged historical 658 cumulative Python / 271 TypeScript /
39 browser record, including its separately successful HTTP retry. No full suites
are rerun solely for closeout. User services remain running. Handoff: accepted M19
only; await a separate task, with no deployment, M20 or scope expansion.

## Pre-M20 low-pressure separator-liquid pump study — 2026-10-01

Study only; M20 is not implemented. The 24 actual historical M17 outputs contain
19 liquids (15 saturated, four compressed) and five absent liquid outlets.
Unchanged PT reproduces their phase calorics, including methane fractions below
0.01. The 41-entry study records 30 accepted numerical tuples, nine rejections
and two unresolved 8 MPa PS paths with retained high-temperature scan holes;
2,337 applicable independent comparisons pass. This supports specific tuples,
not a configurable production domain. Literal streams still fail M19's
independent-caloric-input contract and its scalar scope. Saturated phase/provenance
semantics, local admissibility, inverse limitations and mixed-network integration
remain future dependencies; no NPSH/cavitation or experimental validation is implied.
See `PRE_MILESTONE_20_LOW_PRESSURE_SEPARATOR_PUMP_QUALIFICATION.md` and
`benchmarks/low_pressure_separator_pump/` for inventory, fixed tolerances, complete
ledger, independent provenance and reproduction. Production/historical evidence
and both unrelated local files remain unchanged; no stage, commit, push or deploy.

## Pre-M20 separator-liquid contract/local guards — 2026-10-01

Study-only continuation reaches decision A for future implementation restricted
to the 30 explicitly qualified tuples; M20 is not implemented. A proposed additive
state context distinguishes upstream-derived Hdot from independent caloric inputs,
resolves actual source calculation/port identity and preserves source material/energy
values. Fresh production PT/common-tangent/fugacity evidence admits verified
saturated liquid; same-T/z lower-pressure liquid witnesses screen compressed states.
No reference-library runtime dependency or new shared boundary solver is required
for these exact cases. This is not a configurable domain or cavitation approval.
Twelve captured separator results, 72 new independent witnesses/probes, eight fresh
pump/identity paths and 2,543 comparisons support the study; 27 contract negatives
reject as expected. Both known 8 MPa PS failures remain unresolved and excluded.
See `PRE_MILESTONE_20_SEPARATOR_LIQUID_CONTRACT_QUALIFICATION.md` and
`benchmarks/low_pressure_separator_pump/phase_contract/`. Future implementation
still needs source-freshness resolution, additive schemas/adapters and mixed-network
integration under separate authorization. All first-study/historical evidence and
both unrelated modified files remain preserved; no stage, commit, push or deploy.

## M20 — qualified separator-to-pump integration (2026-10-01; human acceptance pending)

Production implementation adds `separator_pump_energy`: existing M17 rigorous separator
→ verified actual liquid → `separator_liquid_pump_pr@1.0` → liquid product, with a separate
vapor sink. Requirements/flowsheet/results versions are 1.12/1.13/1.14; branch engine 1.13.0.
The production input-only specification admits exactly the 30 accepted phase-contract
study tuples, including only the explicit 1,000 Pa exception. Known 8 MPa PS failures
remain excluded and unresolved. No arbitrary low-pressure envelope, interpolation,
new feed thermodynamic qualification, hydraulics, NPSH or cavitation prediction.

Runtime source resolution comes from the validated graph and private current execution,
not editable provenance assertions or historic UUIDs. Upstream Hdot is preserved and
verified. Versioned phase/source/basis contexts distinguish independent PT and derived
material; pump outlets identify the pump and retain separator lineage. Identity preserves
material fields exactly, returns zero work/null reconstructed efficiency, and skips PS/PH.
Shared thermodynamic solvers and M17–M19 model/contract behavior remain unchanged.

Fresh runtime evidence: `benchmarks/m20_separator_pump/implementation.json`; exact source
mapping and 1,680 comparisons across 30 tuples pass against frozen independent evidence.
The inverse association keeps exact received specifications and uses the qualified
composition tolerance for the unchanged PR evaluator's normalization roundoff. The
qualified local phase policy, full inverse scans, 500 K work-budget term and atomic
failure behavior remain mandatory; endpoint checks do not prove a continuous liquid path.

See `MILESTONE_20.md` for scope, verification, exact implementation/prerequisite inventories,
CLI/browser demonstrations and the pending human-acceptance checklist. The two prerequisite
studies and their frozen artifacts are preserved byte-for-byte, including their historical
qualification status. The original context prefix and unrelated `next-env.d.ts` and
`tsconfig.json` modifications are preserved. Everything remains unstaged; no commit, push
or deployment. Browser automation does not constitute human acceptance.

## M20 — user-reported browser checks and energy-label correction (2026-10-01)

Giovani Nunes reported the following browser checks on 2026-10-01,
America/Sao_Paulo. These are user observations, separate from automated evidence;
the assistant did not operate the user's browser or assert repository screenshots.

- Canonical: four-stream topology inspected; pump 1 → 2 MPa, outlet approximately
  292.169147283 K, fluid power approximately 8068.185157497 W; balances passed.
  Exported JSON was reviewed in the accompanying ChatGPT discussion and matched the
  display, preserving component flows, upstream enthalpy and consistent run/source lineage.
- Identity: inlet/outlet 1 MPa and approximately 291.742138657 K; zero fluid power;
  flow/composition/enthalpy preserved, reconstructed efficiency unavailable for equal-pressure
  identity, balances passed.
- Alternative PT: pump 0.3 → 1.3 MPa, liquid flow approximately 2813.610577 kg/h,
  temperature 350 → 350.57142487 K, fluid power approximately 1585.58354265 W,
  separator heat duty approximately 1832535.61976255 W; balances passed. The remaining
  defect was the general summary incorrectly attributing process heat to imposed pump duty.
- SCALED17.3: pump liquid flow 17.3 mol/s = 62.28 kmol/h (not total process-feed flow),
  fluid power approximately 2681.34745204 W; canonical-consistent pressure, temperature,
  composition, flow-scaled extensive quantities; balances passed and results current.
- Unsupported: explicit `unsupported_qualified_tuple` rejection identifying 30 qualified
  combinations and known 8 MPa exclusions; no PFD generated, calculation disabled.
- Stale: canonical feed-temperature edit displayed “Engineering results — STALE,” a warning
  that retained results belonged to a previous calculation, and disabled Download results.
  Historical values remained visible with the warning; they were not cleared.

The presentation-only correction separates M20 process-total heat duty from total power
transferred to the fluid, using the corresponding process result fields and explicit
positive-into-process signs. Separator specification labels use its mode: PT calculated,
adiabatic imposed zero. Zero/unavailable semantics and historical equipment workflows
remain intact. No numerical output, contract, solver, scope or frozen evidence changed.
Six focused frontend tests passed (including rendered general summaries for PT, PH and
identity); types, changed-file lint/formatting and diff checks passed. Previous full-suite
history and the historical M19 test exclusion are preserved, not rerun or reclassified.
Current unrelated Next/TS configuration bytes are preserved; no services were started or
stopped. See the new section in `MILESTONE_20.md` for exact observations, commands, files,
hashes and the short visual-review checklist. Everything remains unstaged; no commit,
push, deployment or M21. Final M20 closeout remains pending the user's visual review of
this correction; the corrected UI has not yet received human acceptance.

## M20 — final human acceptance and closeout (2026-10-01)

**Current status: M20 accepted and complete within its documented scope.**
Reviewer: **Giovani Nunes**; date: **2026-10-01**;
timezone: **America/Sao_Paulo**. Evidence: user-operated browser checks, screenshots
and an exported JSON reviewed in the accompanying ChatGPT discussion. The assistant
did not perform these manual checks and asserts no repository paths for uploads or
screenshots. Earlier pending statements above are preserved as historical context;
this entry supersedes their status.

All previously recorded canonical, identity, alternative PT, scaled-flow,
unsupported-combination, stale-warning/disabled-download and exported-JSON
agreement/provenance observations remain valid. The user has now also visually
confirmed the corrected general and detailed energy labels:

- Alternative PT (`PT_VL_HEATING_DP1000000.0`): total process heat duty
  **1832535.619763 W**, separately displayed power transferred to the fluid
  **1585.583543 W**; detailed label **“Separator heat duty — calculated”**;
  mass and energy checks remain passed.
- Canonical PH (`PH_FLASH_DP1000000.0`): total process heat duty **0 W**,
  separately displayed power transferred to the fluid **8068.185157 W**;
  detailed label **“Separator heat duty — imposed zero”**; mass and energy checks
  remain passed.

The heat-duty attribution defect is corrected and visually reviewed by the user.
Acceptance remains limited to exactly **30 qualified methane/n-hexane combinations
with explicit zero kij**, existing local phase checks and numerical guards. No
continuous envelope/interpolation, NPSH, cavitation safety, hydraulic sizing or
electrical-power qualification. Known 8 MPa PS failures remain unresolved and
excluded; broader separator-to-pump operation is outside this completed scope.

The final reviewed inventory is **63 unique paths**: 33 M20 implementation paths,
including the summary regression test and final acceptance documentation, plus 30
prerequisite-study paths. The shared master-context path is counted once. Current
`next-env.d.ts` and `tsconfig.json` bytes are preserved and excluded. Historical
verification, its explicit hash-assertion exclusion, and the subsequent six frontend
tests remain recorded without claiming new full-suite runs. Closeout uses read-only
evidence/source integrity, inventory, schema, changed-document formatting and
working-tree/staged-diff checks; no frozen evidence or solver changes.

The user authorized the M20/prerequisite commit and normal push to `origin/main`:
`Complete Milestone 20 separator-to-pump integration and record human acceptance`.
No deployment, M21 work, expanded qualification or service shutdown. See
`MILESTONE_20.md` for the exact inventory, final acceptance details and fresh-conversation
handoff. Broader operation and the known 8 MPa failures require separate future work.

## Pre-M21 — configurable separator-to-pump study (2026-10-01)

**Decision D for extension into the investigated 8 MPa region; M21 remains
unimplemented.** M20 still supports exactly its 30 accepted combinations. The
study evaluates 64 entries (62 distinct combinations): 55 numerical acceptances
including 30 anchors and two repeated controls, seven exclusions and two unresolved
production paths. Additional exact candidates do not establish a configurable
envelope. Independent source qualification remains separate from pump and
execution/provenance qualification; a nearby 355 K source produces no liquid.

Both 8 MPa PS failures reproduce at 461.9047619047619 and 466.6666666666667 K:
initial stability converges, but PT equilibrium exhausts 100 iterations above the
fixed fugacity tolerance. Independent liquid roots near 232 K and isolated local
prototypes agree; default production PS remains rejected. Existing PH connected
interval semantics explain successful PH diagnostics without repairing PS.
Isolated 200/400-iteration PT scans resolve the sampled holes (maximum 152),
without changing production or tolerances. Solver/control/guard qualification
and source-family boundary evidence remain prerequisites to broader operation.

See `PRE_MILESTONE_21_CONFIGURABLE_SEPARATOR_PUMP_QUALIFICATION.md` and
`benchmarks/configurable_separator_pump/` for independent references, ledger,
prototypes, reproduction, guards and limitations. Historical evidence, production,
HEAD/index and both unrelated configuration files are preserved; only this context
is appended. No commit, push, deployment or service change. Numerical phase/path
sampling does not establish global uniqueness, universal convergence, NPSH,
cavitation safety, hydraulic sizing or electrical power.

### PRE-M21 — PT iteration-budget qualification (2026-10-01)

Study-only extension: `PRE_MILESTONE_21_PT_ITERATION_BUDGET_QUALIFICATION.md` and
`benchmarks/pt_iteration_budget/`. Decision A: explicit opt-in
`pr_high_accuracy_pt200@1` qualified for the predeclared finite matrix, ready for
separately authorized implementation; legacy100 defaults remain unchanged, no
400 fallback and no configurable operating envelope. Caps 200/400 complete all
70 PT inputs, six inverse anchors and 12 prototype chains; legacy100 completes
41/70, 6/6 and 6/12. Both actual 8 MPa cold-source chains succeed in the prototype
and remain excluded by production M20; all original 30 combinations remain admitted.
Full-chain peak is 199 equilibrium iterations (PH sample 469.29133858267716 K),
leaving only one iteration of observed headroom at 200. Normal successful PT traces
remain exact; 400 adds no recovered cases. Final independent ledger: 7,895 checks,
5,857 scalar comparisons, zero unresolved failures. Preserve the 195 original named
reference failures: a separate independent PIP/volume/density audit identifies six
swapped reference phase names without changing phase properties or tolerances.
Final focused tests: 14 passed; existing solver regressions: 273/274 passed, sole
failure the pre-existing M20 historical next-env hash assertion. Current config bytes,
production and all prerequisite artifacts remain unchanged; master content before
this entry is preserved. Source/settings identity, full-chain guards, timing samples,
raw failures and read-only reproduction are frozen in the separate extension.
No staging, commit, push, deployment, service or production changes.

## M21 — explicit opt-in PT200 infrastructure (2026-10-01; review pending)

Production implementation adds immutable `pr_high_accuracy_pt200@1` selection via
provider PT/caloric/PS/PH APIs, standalone PS/PH and explicit expected-profile pump
inverse guards. Named settings carry exact provenance; unknown/conflicting selections
reject. Legacy omitted defaults and explicit-None behavior are preserved. No shared
PT/EOS/stability/RR/caloric algorithm, tolerance, inverse policy or equipment caller
selection changes. No named PT400, retries, fallback, pressure-triggered selection,
UI selector, new equipment model, public schema change or expanded admission.

Real production APIs reproduce the frozen 70 PT / six inverse / 12-chain finite
qualification. PT200 accepts all; legacy100 retains 41/70, 6/6 and 6/12. Both 8 MPa
chains succeed numerically and remain rejected by M20. All 30 admitted M20 workflows
pass 1,680 independent checks. M21 ledger: 4,941 checks, 3,679 scalar comparisons,
zero failures; separate 10,248 compatibility/propagation checks pass. All 140 PT
runs retain frozen numerical payloads/iteration traces after accounting only for
explicit named provenance. Peak remains 199 iterations, one iteration below the
cap; no continuous envelope or universal convergence claim.

Full Python run: 680 tests, eight assertion failures and one sandbox HTTP setup
error. The explicit-None compatibility defect was fixed; 74 affected tests pass,
and HTTP retry passes two tests. Seven historical source/result/config assertions
across three methods remain failing and unchanged, separately audited against a
new current-source manifest. Full frontend run was 276/277; the maintained freshness
test now distinguishes archived stale data from actual current calculations, with
six affected tests and two final-source tests passing. Contracts, lint, types and
isolated build pass; no browser/user acceptance claimed. Source fingerprints are
mapped honestly; frozen references and raw phase-audit failures are preserved.

See `MILESTONE_21.md` and `benchmarks/m21_pt200/` for APIs, exact commands, intermediate
failures, current-source adapters, inventory and review items. All prerequisite
bytes, existing master prefix, unrelated configurations, HEAD and index are preserved.
Implementation review/acceptance remains pending. No commit, push, deployment or
running-service change. Equipment integration or broader qualification requires
separate authorization.


## M21 — final implementation review (2026-10-02; acceptance pending)

Review found no further production correction. Maintained three historical-identity
methods, strengthened full source-replay provenance/envelope checks and M20 comparison
length checks, and added mutation tests. Complete ledger: 169 assertions, 41 obsolete
historical/current comparisons, including 34 masked by earlier failures. Historical
expectations and original failed logs are preserved. Current calculations now have
separate frozen-reference numerical, current freshness and review-start preservation
coverage. Recovered 103/104 historical pins (all production), verified a coherent
36-source M19 snapshot, and reproduced all 30 old M20 semantic identities. The old
next-env snapshot is unavailable; complete archival verification still explicitly
fails. No historical numerical solver rerun is claimed.

Focused Python run: 29 methods passed. One standard full Python discovery run after
stabilization: 684 methods passed in 841.731 seconds, zero failures/errors,
including temporary HTTP fixtures. Counts overlap and are not cumulative. Source
replay, contracts, lint, TypeScript and preservation pass. Repository format check
fails only on pre-existing tsconfig formatting; explicitly protected bytes are unchanged.
Frontend test is unchanged, so no repeat frontend suite/browser/build was required.
Original full failures and affected reruns remain separately recorded.

Unchanged production source identity supports reuse of 4,941 independent checks
(3,679 scalar), 10,248 compatibility/propagation checks, and the finite 70 PT / six
anchor / 12-chain scope. Fresh M20 runs pass 1,680 checks across 30 workflows. Peak
remains 199 iterations; legacy defaults and application exclusion of 8 MPa remain.
Both prerequisite studies, frozen evidence, original logs, configs, HEAD and index
are preserved. See MILESTONE_21.md and benchmarks/m21_pt200/review/ for the full
assertion ledger, reproduction procedures, verification and exact inventory.
Ready for user acceptance with disclosed limitations; user acceptance and authorized
closeout are not recorded. No commit, push, deployment, service or equipment change.

## M21 — user acceptance (2026-10-02; America/Sao_Paulo)

Giovani Nunes accepts the documented M21 implementation and completed review, based
on the presented evidence. This is user acceptance of internal numerical infrastructure,
not browser acceptance, independent code inspection by the user or user-executed
numerical verification. No browser acceptance is required or claimed.

Recorded evidence remains 684 passed methods in one full Python run and 29 passed
methods in a separate focused run; totals overlap and are not cumulative. Three
historical-identity methods were maintained. The ledger covers 169 assertions,
including 41 obsolete comparisons and 34 masked mismatches. Independent evidence
remains 4,941 checks (3,679 scalar), 10,248 compatibility/propagation checks and
1,680 checks across 30 M20 workflows. Original failures and corrections are preserved.
Historical byte/semantic reconstruction is separate from numerical reproduction;
the unavailable historical next-env snapshot and pre-existing tsconfig formatting
remain disclosed limitations. Both current configuration files are preserved and
excluded from the commit.

PT200 remains explicit opt-in `pr_high_accuracy_pt200@1` through production numerical
APIs. Historical defaults and M20 application admission are unchanged; there is no
automatic fallback/escalation or continuous operating-envelope claim. Finite scope
remains 70 PT inputs, six inverse anchors and 12 chains, with an observed peak of 199
iterations. The 8 MPa chains succeed numerically but remain excluded from application
workflows. Broader equipment integration requires a separately defined next milestone.

Documentation closeout, exact inventory staging, a new commit and normal push to
verified origin/main are authorized. See MILESTONE_21.md and
benchmarks/m21_pt200/closeout/inventory.json. Earlier pending-acceptance entries are
preserved as history. No deployment, M22 work or running-service changes are included.

## M22 — explicit PT200 separator-to-pump integration (2026-10-02; acceptance pending)

Adds only PT_BUBBLE_BELOW and PT_BUBBLE_ABOVE actual source recipes at 8 MPa
absolute pump discharge and efficiency 0.8, explicitly selecting
`pr_high_accuracy_pt200@1`. Exact input-only recipes are in
`engine/riogineer_engine/separator_pump_pt200_cases.json`; the unchanged historical
list still admits its original 30 combinations with historical defaults. There is
no interpolation, arbitrary flow/efficiency scaling or combination of sampled inputs.
The below source is compressed liquid; the above source supplies phase-specific
liquid from a verified two-phase separator, not an independent bulk liquid feed.

Additive requirements/flowsheet/results branches are 1.13/1.14/1.15, branch engine
1.14.0, pump `separator_liquid_pump_pr@2.0`. Existing 1.12/1.13/1.14 and pump@1.0
semantics remain unchanged. Pump parameters require the exact numerical_profile;
omitted, unknown, conflicting and historical-selection 8 MPa requests reject.
Selection persists in flowsheets/results and participates in calculation identity.
The separator remains `equilibrium_separator_energy_pr@1.0` with historical
high_accuracy100 settings. Pump PT200 settings and source/local historical settings
are recorded separately with compatibility checks; no whole-network switch occurs.

Actual source rates, phase composition and authoritative Hdot propagate through the
private execution registry. Existing source/local guards, M21 exact inverse-profile
guards, full PS/PH scans, fresh endpoints, work/entropy and equipment/process balances
remain active. Production calculates targets from actual streams; no independent
endpoint is injected. Solvers, equations, tolerances and property data are unchanged.
Controlled failures return errors without successful process outlets or automatic
fallback. No named PT400. The accepted M21 peak remains 199 iterations under the
200 cap; this finite integration does not establish universal convergence, a
continuous operating envelope, hydraulic sizing, NPSH or cavitation qualification.

New evidence is additive under `benchmarks/m22_separator_pump/`: predeclared plan,
207 preliminary source-plus-pump checks and 221 final complete-application checks,
all passing against frozen independent physical evidence and retained guards.
Fresh M20 regression passes 1,680 checks across all 30 workflows and exact complete
numerical/result-payload equality after excluding run/input/implementation identities.
All old schema branches and shared definitions remain structurally identical.
Current M22 source/preservation manifests are separate from archived M21 identity;
three maintained test files now invoke the M22 adapter. Historical evidence, accepted
M21 records, master prefix and both task-start configuration files are preserved.

Two browser reference loaders explain the boundary reference and explicit pump PT200.
Existing PFD/results/table components retain separate heat duty/fluid power, PT/PH
separator duty attribution, molecular consistency, stale warnings and export agreement.
Manual acceptance remains pending. See `MILESTONE_22.md` for exact CLI/startup commands,
the six-step acceptance checklist and exact inventory; the integration report and
verification.json record individual runs and intermediate test-harness corrections.
No stage, commit, push, deployment or user-service shutdown is authorized/performed.

### M22 CLI and pending browser acceptance

From the repository root:

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --case PT_BUBBLE_BELOW --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --case PT_BUBBLE_ABOVE --calculate
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.milestone22 --unsupported --calculate
```

The third command must reject efficiency 0.81 and exit 1. For manual browser work,
check service availability with `lsof -nP -iTCP -sTCP:LISTEN`; reuse existing matching
services. If 8122/3122 are free, start these in separate terminals, both from the
isolated `.local/m22-validation` directory (preserves original Next/TS files):

```sh
PYTHONPATH=engine engine/.venv/bin/python -B -m riogineer_engine.server --port 8122
RIOGINEER_ENGINE_URL=http://127.0.0.1:8122 npm run dev -- --port 3122
```

At `http://127.0.0.1:3122/digital-engineer`, expand Engineering data / Advanced:

1. Load the M22 below-boundary PT200 reference; validate, generate PFD and calculate.
   Confirm compressed-source semantics and explicit pump PT200/historical separator.
2. Repeat for the above-boundary reference; confirm liquid extracted from a two-phase
   separator, with actual liquid flow rather than total source-feed flow.
3. Compare below/above actual T approximately 232.0029774476092 / 232.1032000731769 K
   and fluid power 20567.978871054584 / 20564.527568835445 W. Compare isentropic T
   231.62864734074992 / 231.7288906905257 K in JSON diagnostics. All balances pass.
4. Change efficiency to 0.81 and validate: unsupported tuple, no current successful
   result panel and no enabled result export/calculation.
5. Recalculate a reference, then edit an input or its profile to `unknown`: immediately
   stale with disabled download; the unknown profile also rejects validation.
6. Recalculate a restored reference; compare all four stream-table columns against
   exported JSON, including component/total/molar rates, molar fractions, T/P, source
   Hdot/lineage, separate process duty/fluid power and explicit profile.

These remain human review steps, not claimed acceptance. Exact changed-file inventory
is recorded below and in `benchmarks/m22_separator_pump/inventory.json`.


### M22 final automated verification — 2026-10-02

One ordinary full Python run passes **693 tests in 871.395 seconds**, with zero
failures/errors and no exclusions. Separate focused runs pass nine M22 methods and
29 historical/M21 compatibility methods; these overlap with the full run. Full
frontend: 280 tests in 28 files; full browser: 42 tests in one run; focused frontend
seven, focused browser two. Schema parity, old-branch structural identity, types,
lint, isolated production build and smoke (17 pages/17 cards plus links/404/indexing/
contact checks) pass. Formatting reports only the pre-existing protected tsconfig.
Original focused harness corrections and separate run counts remain in verification.json.
No cumulative unique-test count or repeated full M21 qualification is claimed.

Both CLI references complete; efficiency 0.81 rejects with exit 1. Final remote main
still equals 253b91472a5007e7bd4749a6751c4efbc5066e14; index empty. At final service
inspection ports 3122/8122/3123 are free; test-owned services have stopped and user
services are untouched. Use the startup instructions above only if matching services
are not already running. Original Next/TS bytes, master prefix and all frozen evidence
are preserved. Human acceptance, staging, commit/push and deployment remain pending.

## Exact M22 file inventory

70 task-owned paths; all unstaged. The two pre-existing configuration edits
are excluded and byte-preserved.

- `MILESTONE_22.md`
- `benchmarks/m22_separator_pump/PLAN.md`
- `benchmarks/m22_separator_pump/README.md`
- `benchmarks/m22_separator_pump/baseline.json`
- `benchmarks/m22_separator_pump/contract_compatibility.json`
- `benchmarks/m22_separator_pump/contracts.py`
- `benchmarks/m22_separator_pump/final_status.txt`
- `benchmarks/m22_separator_pump/finalize.py`
- `benchmarks/m22_separator_pump/historical.json`
- `benchmarks/m22_separator_pump/historical.py`
- `benchmarks/m22_separator_pump/integration.json`
- `benchmarks/m22_separator_pump/integrity.py`
- `benchmarks/m22_separator_pump/inventory.json`
- `benchmarks/m22_separator_pump/logs/browser-focused.log`
- `benchmarks/m22_separator_pump/logs/browser-full.log`
- `benchmarks/m22_separator_pump/logs/build.log`
- `benchmarks/m22_separator_pump/logs/cli-above.json`
- `benchmarks/m22_separator_pump/logs/cli-below.json`
- `benchmarks/m22_separator_pump/logs/cli-unsupported.log`
- `benchmarks/m22_separator_pump/logs/compatibility-focused.log`
- `benchmarks/m22_separator_pump/logs/contract-compatibility.log`
- `benchmarks/m22_separator_pump/logs/contracts.log`
- `benchmarks/m22_separator_pump/logs/diff-check.log`
- `benchmarks/m22_separator_pump/logs/focused-final.log`
- `benchmarks/m22_separator_pump/logs/focused-initial.log`
- `benchmarks/m22_separator_pump/logs/format.log`
- `benchmarks/m22_separator_pump/logs/frontend-focused-final.log`
- `benchmarks/m22_separator_pump/logs/frontend-focused.log`
- `benchmarks/m22_separator_pump/logs/frontend-full.log`
- `benchmarks/m22_separator_pump/logs/historical.log`
- `benchmarks/m22_separator_pump/logs/initial-types.log`
- `benchmarks/m22_separator_pump/logs/integration.log`
- `benchmarks/m22_separator_pump/logs/integrity.log`
- `benchmarks/m22_separator_pump/logs/lint.log`
- `benchmarks/m22_separator_pump/logs/preliminary.log`
- `benchmarks/m22_separator_pump/logs/python-full.log`
- `benchmarks/m22_separator_pump/logs/smoke.log`
- `benchmarks/m22_separator_pump/logs/typecheck-final.log`
- `benchmarks/m22_separator_pump/logs/typecheck.log`
- `benchmarks/m22_separator_pump/manifest.json`
- `benchmarks/m22_separator_pump/preliminary.json`
- `benchmarks/m22_separator_pump/screenshots/above-pfd.png`
- `benchmarks/m22_separator_pump/screenshots/below-pfd.png`
- `benchmarks/m22_separator_pump/source_manifest.json`
- `benchmarks/m22_separator_pump/verification.json`
- `benchmarks/m22_separator_pump/verify.py`
- `contracts/examples/milestone-22-above-requirements.json`
- `contracts/examples/milestone-22-below-requirements.json`
- `contracts/v1/flowsheet.schema.json`
- `contracts/v1/requirements.schema.json`
- `contracts/v1/results.schema.json`
- `contracts/v1/validation.schema.json`
- `docs/RIOGINEER_MASTER_CONTEXT.md`
- `engine/riogineer_engine/core.py`
- `engine/riogineer_engine/milestone22.py`
- `engine/riogineer_engine/network.py`
- `engine/riogineer_engine/separator_liquid_pump.py`
- `engine/riogineer_engine/separator_pump_process.py`
- `engine/riogineer_engine/separator_pump_pt200_cases.json`
- `engine/riogineer_engine/separator_pump_scope.py`
- `engine/tests/test_m22_separator_pump.py`
- `engine/tests/test_pt200_profile.py`
- `engine/tests/test_separator_pump_integration.py`
- `engine/tests/test_variable_pump_evidence.py`
- `src/app/digital-engineer/pfd.tsx`
- `src/app/digital-engineer/separator-pump-results.tsx`
- `src/app/digital-engineer/workspace.tsx`
- `src/lib/digital-engineer/contracts.ts`
- `tests/e2e/m22-separator-pump.spec.ts`
- `tests/m22-separator-pump.test.ts`

## M22 manual review and targeted presentation corrections — 2026-10-02

**Corrections implemented; final user acceptance remains pending.** Giovani Nunes
exercised both references on 2026-10-02, America/Sao_Paulo. The following are
user-session observations and a reported external ChatGPT review of downloaded
JSON, not a claim that the assistant inspected unavailable attachments.

- Below boundary: outlet approximately 232.00297745 K; fluid power 20567.97887105 W;
  efficiency 0.8; zero vapor flow with unavailable composition; passing mass/energy
  checks and current results. Pump PT200 and historical separator settings were
  displayed separately. The inlet summary read “liquid; evidence: unknown”.
- Above boundary: outlet approximately 232.10320007 K; fluid power 20564.52756884 W;
  liquid approximately 18395.9051504 kg/h and vapor 3.3636496 kg/h; passing balances,
  current results and source_vle evidence.
- Changing efficiency 0.8 → 0.81 marked retained results STALE with an explicit
  warning, disabled PFD/calculation/download and rejected validation with
  `M22 unsupported_qualified_tuple`. Old values remained visibly stale.
- The user downloaded the above JSON. External review reported agreement with
  displayed values, schema 1.15, completed status, explicit `pr_high_accuracy_pt200@1`,
  separately recorded historical source/local settings, liquid saturation source_vle,
  pumped outlet compressed_witness, preserved separator lineage and calculated
  separator duty **−2.0256265997886658e-7 W**.

### Root cause and correction

`separator_liquid_state.representation` intentionally sets source saturation metadata
`source_vle` for a VL parent and `unknown` otherwise. The private execution registry
resolves that real separator liquid without changing metadata. `verify` separately
performs the actual local admission check; its accepted return contains
`inlet.local.status = compressed_witness` below the boundary and
`saturated_source_liquid` above it. The pump serializes those diagnostics under
`equipment[pump].thermodynamics.diagnostics.inlet.local`. Thus the below source has
verified compressed-liquid evidence; “unknown” was never a missing admissibility
check. The frontend incorrectly used the saturation metadata as its generic
“evidence” label.

The panel now reports **Source saturation metadata** and **Local phase evidence**
separately. It reads the accepted inlet diagnostics and reports the lower-pressure
compressed witness or verified parent coexistence. Missing, unrecognized or
unaccepted diagnostics report unavailable evidence. Reference names no longer carry
an inferred phase-success description. No source context, lineage, numerical setting,
guard, serialization, solver or admission change was needed.

A shared display formatter suppresses the string `-0` only after Intl rounds at
the requested precision. The summary keeps six decimals and displays **0 W**; the
8-decimal detail retains **−0.0000002 W** for the above calculated duty. Resolved
nonzero signs and scientific residuals remain. PT duty is still calculated, never
reclassified as imposed adiabatic duty. Raw numbers and downloads are unchanged.

For M22's visible Unavailable calculations list only, the old exact M20 sentence is
presented as **“This model qualifies material and fluid-energy integration only.”**
Historical M20 rendering and the raw legacy JSON reason remain unchanged. The visible
wording is a presentation paraphrase; numerical/export agreement is exact and no
serialized value is rewritten. Hydraulic/NPSH/cavitation/electrical exclusions remain.

### Targeted verification and preservation

Both cases were freshly reproduced locally: **221 checks passed**. Complete result
payloads equal the original M22 payloads exactly after excluding only fresh run UUIDs;
implementation/input hashes, temperatures, flows, enthalpies, power, balances, settings,
phase evidence and lineage associations remain unchanged. Fresh evidence is additive
under `benchmarks/m22_separator_pump/manual_review/`; original M22 artifacts/logs and
all earlier frozen evidence remain byte-identical.

- Focused frontend: **13 passed across three files** (six new defect tests, existing
  M22 contract/freshness coverage and four historical M20 rendering checks).
- Targeted browser: **2 passed** against existing services on 3122/8122, with
  Playwright service management disabled. Checks cover phase labels, calculated
  near-zero duty, neutral limitation text, all stream columns/export equality,
  stale input/profile edits and unsupported efficiency.
- `tsc --noEmit`, affected-file ESLint/Prettier and diff checks pass.
- The initial frontend run had two assertion failures because a whole-page search
  included the deliberately unchanged raw JSON viewer. Assertions now target the
  Unavailable calculations section; original failure log is retained. No product or
  numerical expectation was altered to resolve that test-scope error.

Commands: `PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/verify.py --output benchmarks/m22_separator_pump/manual_review/reproduced.json`;
`npx vitest run tests/m22-manual-review.test.ts tests/m22-separator-pump.test.ts tests/separator-pump-summary.test.ts`;
`npx tsc --noEmit`; affected-path `npx eslint` and `npx prettier --check`;
`git diff --check`. In `.local/m22-validation`,
`npx playwright test --config playwright.manual-review.config.ts tests/e2e/m22-separator-pump.spec.ts`
uses a temporary local config with `webServer: []`, preserving running services.

The earlier full **693 Python / 280 frontend / 42 browser** results remain prior
recorded evidence and were **not rerun**. No lengthy full suite, qualification matrix
or build was repeated for these presentation-only corrections. Qualification stays
at the two exact PT200 cases plus 30 historical tuples; no automatic fallback or
scope expansion. The M21 observed 199/200 iteration peak remains prior evidence.

### Review the corrected screens

Corrected application and test files are in the main checkout and synchronized to
`.local/m22-validation`. Existing backend/frontend listeners remain on 8122/3122.
**Refresh the browser; no backend restart is needed.** No running service was stopped
or replaced. Reload/recalculate both references if the page no longer holds results.

Confirm below-source metadata is still unknown/unspecified while local evidence says
verified compressed liquid; above-source metadata is source_vle with verified parent
coexistence. Confirm summary 0 W, calculated PT detail retaining its small negative
value, neutral Unavailable calculations wording, and unchanged results/downloads.
The raw JSON reason retains its legacy wording by design. Recheck the 0.81 rejection
and stale warning if desired. Final acceptance of these corrected screens remains
pending; no acceptance, commit, push or deployment is claimed.

The initial 70-path inventory/manifest above is retained as the initial implementation
record. The current combined inventory, exact correction delta, current hashes and
final Git status are in `benchmarks/m22_separator_pump/manual_review/inventory.json`,
`manifest.json` and `final_status.txt`. Original engine/schema source manifest remains
valid because no backend source changed. Task-start configuration bytes are preserved.

## M22 acceptance and closeout — 2026-10-02

**Current status: accepted by Giovani Nunes on 2026-10-02, America/Sao_Paulo.**
This entry supersedes earlier pending-acceptance and pending-correction-review
statements, which remain historical records. Evidence classification: user-reported
browser acceptance, supported by screenshots and an exported above-boundary results
JSON reviewed in the design conversation. These are the user's observations; Codex
did not perform the human review.

The user accepted both corrected references and the following behavior:

- **PT_BUBBLE_BELOW:** current results and expected separator-to-pump stream mapping;
  discharge 8 MPa absolute, efficiency 0.8, pump outlet approximately 232.00297745 K,
  fluid power approximately 20567.97887105 W. The absent vapor outlet retains
  appropriate unavailable-property semantics; material and energy balances pass.
- **PT_BUBBLE_ABOVE:** current results with separate liquid and small vapor outlets;
  discharge 8 MPa absolute, efficiency 0.8, pump outlet approximately 232.10320007 K,
  fluid power approximately 20564.52756884 W. Material and energy balances pass.
  Downloaded results JSON agrees with displayed values, phase/source context, and
  separate separator and pump numerical settings.
- **Unsupported edit:** changing efficiency from 0.8 to 0.81 invalidates the results,
  explicitly marks previous results stale, and rejects the unsupported tuple.
  Calculation, PFD, and export availability reflect the invalid state. Retained
  historical displays do not represent current acceptance.
- **Corrected presentation, both references:** source-saturation metadata and
  verified local phase evidence are separate. Below-boundary shows verified
  compressed-liquid evidence from the lower-pressure witness with unspecified
  source-saturation metadata. Above-boundary shows verified saturated source-liquid
  evidence from parent equilibrium coexistence with `source_vle` metadata. Summary
  heat duty displays 0 W without negative zero; above-boundary detailed duty retains
  approximately -0.0000002 W, labeled calculated. The corrected M22 limitation reads
  “This model qualifies material and fluid-energy integration only.” No misleading
  M20 reference remains in that visible limitation; the historical raw JSON reason
  remains unchanged, as documented in the correction record.

Acceptance is finite: only the exact documented `PT_BUBBLE_BELOW` and
`PT_BUBBLE_ABOVE` source recipes, 8 MPa absolute discharge, efficiency 0.8, explicit
pump profile `pr_high_accuracy_pt200@1`, and methane/n-hexane with explicit zero
`kij`. Historical separator numerical settings and historical M20 admission with
its 30 workflows remain preserved. There is no automatic fallback/profile selection,
interpolation or continuous operating-envelope qualification, hydraulic sizing,
NPSH, or cavitation qualification. The previously observed 199/200 iteration peak
remains a limitation.

Closeout changes only acceptance documentation and adds closeout bookkeeping.
Solvers, contracts, model scope, numerical outputs, and frozen evidence are unchanged
from the reviewed implementation. The original 70-file inventory and subsequent
90-file combined manual-review inventory remain historical snapshots. The exact
commit inventory is **94 files**: those 90 paths plus four closeout records in
`benchmarks/m22_separator_pump/closeout/` (`baseline.json`, `inventory.json`,
`checks.json`, and `manifest.json`). The closeout manifest records current hashes,
excluding itself; the baseline retains all 90 pre-closeout hashes, allowing the two
updated documents to be distinguished from frozen implementation/evidence files.

Focused closeout verification passed: inventory reconciliation; reviewed evidence
hashes; current engine/schema provenance and archived M21 source identity;
historical artifact and configuration preservation; historical schema branch/shared
definition preservation; generated schema parity; edited-document formatting; and
working-tree whitespace. Explicit staging, staged whitespace, inventory/hash review,
and a normal push are required transaction gates. The final commit and remote
identity are reported in the closeout response, rather than embedded recursively
in the commit itself. `next-env.d.ts` and `tsconfig.json` remain excluded and retain
their task-start bytes. No deployment or service restart/shutdown is authorized.

Earlier automated results retain their original scope and caveats: the implementation
record contains 693 Python, 280 frontend, and 42 browser tests; the later correction
record separately contains 13 final focused frontend tests, two browser workflows,
and 221 numerical comparisons across two cases. Those runs were not repeated or
combined into a new full-suite pass during closeout. Historical intermediate failures
and the documented pre-existing configuration-formatting condition remain recorded.

Next conversation: M22 is accepted only within the finite scope above. Use this
entry and the closeout inventory alongside the earlier qualification evidence;
any broader admission, numerical strategy, or hydraulic claims require separate
work. This closeout does not start M23.

Staged whitespace review found 16 warnings in 10 frozen raw tool logs (trailing
spaces, terminal output indentation, and blank lines at EOF). The full
`git diff --cached --check` returned 2; this is recorded, not a clean full check.
Every affected log matches its reviewed pre-closeout hash. An explicit check of
all other staged paths passed. The logs remain unchanged under the requirement to
preserve frozen evidence; exact diagnostics and paths are in `closeout/checks.json`.
