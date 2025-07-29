# Knowledge Harvest

The **Knowledge Harvest** project aims to capture tacit subject‑matter‑expert (SME) knowledge and convert it into structured, reusable assets for training and onboarding.  Tacit knowledge is the deep‑rooted, intuitive understanding and expertise that resides within individuals and cannot be easily articulated or transferred【224308209286044†screenshot】.  It often includes hard‑won lessons, insights and instincts that people develop through experience【947879009909907†screenshot】.  These nuanced skills are fragile and can be lost when employees leave the organisation【776182156384248†screenshot】.  Knowledge Harvest provides tools for capturing screen workflows, voice rationales and after‑action reflections so that organisations can preserve this intangible know‑how and make it accessible to others.

## Key principles

* **Focus on tacit knowledge.**  Tacit knowledge includes skills, experiences, intuition and judgement, and is often learned through observation and continuous sharing at work【261120688409170†screenshot】.  It is hard to express with words alone【261120688409170†screenshot】, so the project uses screen recording, voice capture and storytelling to preserve how experts think and act.
* **Knowledge‑friendly culture.**  Capturing knowledge requires an environment that values and encourages knowledge sharing.  Practices such as promoting open communication and recognising employees who actively share their know‑how help build this culture【94584336290138†screenshot】.
* **Mentoring and storytelling.**  Pairing less experienced employees with seasoned mentors, implementing on‑the‑job training and organising storytelling sessions help transfer tacit knowledge【94584336290138†screenshot】【473640312520138†screenshot】.
* **Use technology responsibly.**  Microservices architecture breaks the system into small, self‑contained services that communicate via APIs【756389315289057†screenshot】.  This design increases scalability and reliability.

## Repository structure

This repository is organised as follows:

| Path | Description |
|-----|-------------|
| `docs/ideas.md` | A list of business ideas and features for knowledge capture. |
| `design/wireframes.md` | Mermaid diagrams describing wireframes and user flows. |
| `services/ai-microservice-specs.md` | Specifications for AI microservices (capture, transcription, summarisation). |
| `web/frontend-architecture.md` | Front‑end architecture and state‑management choices. |
| `infra/deployment-manifests.md` | High‑level infrastructure and deployment sketches. |
| `.github/ISSUE_TEMPLATE/…` | Issue templates for features, bugs and tasks. |
| `.github/PULL_REQUEST_TEMPLATE.md` | A pull‑request template. |
| `CONTRIBUTING.md` | Guidelines for contributing. |

## Getting started

1. Clone this repository and install dependencies for the web front‑end and services.
2. Review the `infra/deployment-manifests.md` to understand the expected infrastructure.
3. Run the `scripts/project_setup.sh` script (described in the `scripts/` folder) to generate labels, milestones and the project board using GitHub CLI.
4. Use the issue templates to plan work items and link pull requests to issues.

## References

This project draws on research about tacit knowledge and knowledge transfer strategies【224308209286044†screenshot】【94584336290138†screenshot】 as well as best practices for microservices architecture【756389315289057†screenshot】.