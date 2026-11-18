# Daniel González Rete

Senior AI Engineer | Agentic Systems & Data Platforms

Contact: LinkedIn https://linkedin.com/in/daniel-gonzalez-r

## Professional Summary

Senior AI Engineer with 11 years in data engineering across fintech, retail, and banking, the last two and a half building multi-agent AI in production. At DEUNA, I designed, built, and iterated the subsystems that make answers trustworthy in ATHIA, an agent-based payment analytics platform: its root-cause analysis mode, the deterministic statistical detection engine, the semantic metrics layer used across the platform, and data-quality monitoring. Root-cause analysis cut anomaly diagnosis from days of cross-team work to minutes. Previously led teams of up to 12 engineers; currently completing a Master's in Artificial Intelligence.

## Key Achievements

- Cut payment anomaly diagnosis from days of cross-team analysis (data, operations, fraud, business) to minutes with the root-cause analysis mode I designed and built for ATHIA, an agent-based payment analytics platform.
- Core contributor to ATHIA's 2026 launch to its merchant clients; the platform is used by merchant users and by internal teams across operations, data, commercial, key account, BI, and C-level.
- Built the semantic metrics layer that lets a new metric go live in minutes with no schema changes, on a platform that onboards a new merchant in days.
- Cut data freshness from tens of minutes to minutes by migrating about 20 production sources to near-real-time ingestion in about a month, with zero failed loads across hundreds of thousands of files.

## Technical Skills

- **AI & Agentic Systems:** LangGraph, LangChain, Multi-agent workflow design, Structured outputs (Pydantic), LLM cost optimization and model selection, Non-vector RAG and context engineering, Prompt engineering, Statistical anomaly detection (MAD, robust z-score, linear regression, Gaussian smoothing)
- **AI-Assisted Engineering:** Spec-driven development with Claude Code, using self-authored specs, runbook templates, linters, and custom skills as guardrails; MCP
- **Snowflake:** Advanced SQL, Snowpipe (auto-ingest), Dynamic Tables, Iceberg, Snowpipe Streaming, Alerts and notification integrations, Stored procedures, ACCOUNT_USAGE cost and latency analysis, Cortex LLM functions (lightweight tasks)
- **AWS:** Glue, Glue Schema Registry, DMS (CDC), Kinesis Firehose, DynamoDB Streams, Lambda, SNS, S3, KMS, CDK, SAM
- **Data Engineering:** Python (Pandas, NumPy, SciPy, PySpark), SQL, ETL/ELT, Lakehouse architecture, Semantic metrics layer (YAML + Jinja2), Data quality monitoring, Schema governance, FastAPI, Infrastructure as Code, Apache Airflow, PostgreSQL, MongoDB, GCP (BigQuery, Dataflow), Azure

## Professional Experience

### Sr. AI Data Engineer, DEUNA
05/2024 - Present | Remote

**Agentic AI platform (ATHIA)**

- Designed, built, and iterated the root-cause analysis mode of ATHIA, a web payment analytics platform powered by dozens of specialized agents: users ask in natural language about acceptance rate, fraud, and cost and receive a root-cause analysis from a multi-agent workflow (LangGraph/LangChain, Python, Snowflake).
- Designed and built the deterministic statistical engine that replaced LLM-driven anomaly detection (MAD, linear regression, Gaussian smoothing), with a hierarchical drill-down, volatility-scaled thresholds, and early stopping; validated on millions of transactions over several months, so results are reproducible and auditable.
- Grounded agent calculations in the semantic metrics layer: agents retrieve metric formulas from it instead of generating them, a retrieval approach that needs no vector search.
- Led the first LLM cost-reduction iteration: tuned prompts and retrieved context, and matched model size to the complexity of each agent's task.

**Data platform and reliability**

- Designed and built the Metrics Semantic Layer (Pydantic + Jinja2 SQL + YAML, transitive JOIN resolution) that centralizes metric definitions for the whole platform and its APIs, replacing hardcoded metric SQL; it now serves 30+ production metrics.
- Designed and built a 5-dimension data-quality monitor (volume, completeness, freshness, distribution, immutability) with day-of-week baselines and load lineage via ACCESS_HISTORY; fixed several classes of false-positive and missed-failure bugs, cutting freshness incidents per monitored table by about 40%.
- Designed and built a dimension standardization engine with fuzzy matching for bank names, cities, countries, and error codes, so analysts and agents work on consistent, well-defined dimensions.
- Designed the near-real-time ingestion pattern (Snowpipe auto-ingest + incremental Dynamic Tables) behind the near-real-time migration, with alerting from Snowflake notification integrations through SNS and Lambda to Slack, deployed via CDK.
- Onboarded multiple data domains across environments using several source patterns (CDC, streaming, batch, and external tables), each verified by exact row-count reconciliation, and stabilized Glue jobs from run history (one from frequent failures to zero at about half the compute cost).

**Documentation and engineering practices**

- Authored the architecture, deployment, and data-quality documentation the data team works from, plus runbook templates, linters, and Claude Code skills that keep AI-assisted development within guardrails.
- Shipped production code outside my core stack, in Go (a service using AWS KMS envelope encryption) and Scala/Spark (a reconciliation job migrated from PySpark), written with Claude Code under my own design and review.

### Career Break
09/2023 - 04/2024

### Data Team Lead, Digital@Femsa
11/2022 - 08/2023 | Remote

- Led two simultaneous squads of 6 data engineers each (12 engineers), achieving a 90%+ quarterly delivery rate through active priority management and balanced workload distribution.
- Reduced loyalty points notification time from 24 hours to under 50 seconds by optimizing the purchase event pipeline for real-time balance updates at the moment of transaction.
- Established the data area foundations (development guidelines, policies, naming standards, engineering practices) as the base to scale the team.

### Data Team Lead / Data Architect, Konfío
07/2021 - 11/2022 | Remote

- Led a team of 5 engineers owning the critical billing data ingestion process (scrapers and Snowpark on AWS Glue) that feeds credit decisions, reducing processing time from 4 hours to 14 minutes.
- Designed and provisioned AWS infrastructure (Glue, S3, Redshift, Airflow, DMS, Athena) via IaC and led the migration from a Data Warehouse to a Lakehouse architecture.

### Data Team Lead / Data Architect, EPA Digital
06/2020 - 07/2021 | Remote

- Built the data function from scratch at a digital advertising agency with no prior data infrastructure: CI/CD, standardized deployment, and data engineering foundations.
- Designed scalable Data Warehouse models and architected GCP platforms for ingestion and analysis of structured and unstructured media (images, videos).

### Solution Data Architect Jr, Santander Bank
08/2019 - 06/2020 | Mexico City

- Designed an advanced analytics platform for banking operations and took part in architecture evaluations for internal and external initiatives.
- Implemented next-generation data storage POCs to modernize the bank's analytical infrastructure.

### Sr. Data Engineer, Linio Mexico
08/2018 - 08/2019 | Mexico City

- Developed KPIs and automated pipelines for commercial performance monitoring across LATAM and contributed to the data platform migration to GCP (Dataflow, BigQuery, AutoML).

### BI & Analytics Lead, Televisa
10/2017 - 08/2018 | Mexico City

- Led POCs and deployed BI platforms (Power BI, SharePoint, Neo4j), and optimized ETL pipelines while strengthening data governance practices.

### BI Analyst, Intellego
11/2015 - 10/2017 | Mexico City

- Developed and administered MDM platforms and data-quality dashboards, and designed ETL processes with IBM DataStage.

## Education

- Master's in Artificial Intelligence (in progress), Tecnológico de Monterrey, 2025 - 2027
- B.S. Computer Engineering, Databases Specialization, Facultad de Ingeniería, UNAM, 2010 - 2016

## Certifications

- Microsoft Certified: Azure Fundamentals, Microsoft, 01/2020

## Languages

- Spanish (native)
- English (intermediate, B1/B2)
