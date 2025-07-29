# Business Ideas Platform

Welcome to the Business Ideas platform repository. This project aims to provide a collaborative space for generating, evaluating, and developing business ideas using modern web technologies and AI-driven microservices.

## Repository structure

- **docs/**: Project requirements, specifications, and user stories.
- **design/**: Wireframes, Figma links, and the style guide.
- **services/**: AI, data, and authentication microservices.
- **web/**: Frontend application code.
- **infra/**: Infrastructure-as-code scripts, GitHub Actions workflows, and deployment manifests.

## Architecture diagram

A simplified representation of the microservice architecture connecting the frontend to backend services:

```
+--------------+       +------------------+
|  Frontend    | <-->  | Gateway/Backend  |
+--------------+       +------------------+
        |                         |
        |                         v
        |                 +------------------+
        |                 |  AI Service      |
        |                 +------------------+
        |                         |
        v                         v
  +--------------+       +------------------+
  | Data Service |       | Auth Service     |
  +--------------+       +------------------+
```

## Local development setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/cwarloe/businessideas.git
   cd businessideas
   ```

2. **Set up services**:

   Each microservice in `services/` has its own README detailing setup instructions. You may need to install dependencies (e.g., Python or Node.js packages) and configure environment variables.

3. **Set up the frontend**:

   Navigate to `web/` and install dependencies:

   ```bash
   cd web
   npm install
   ```

   Then start the development server:

   ```bash
   npm start
   ```

4. **Infrastructure and CI/CD**:

   The `infra/` directory contains infrastructure-as-code definitions and CI workflows. See `infra/README.md` for deployment and automation details.

5. **Running the full stack**:

   Use Docker Compose or scripts provided in `infra/` to spin up the microservices and dependencies together for local development.
