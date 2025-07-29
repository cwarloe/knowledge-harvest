#!/usr/bin/env bash

# Script to set up GitHub labels, milestones, issues and a project board for the
# Knowledge Harvest repository.  This script requires the GitHub CLI (gh)
# version 2.0+ and that you are authenticated (`gh auth login`).

set -euo pipefail

REPO="cwarloe/knowledge-harvest"

echo "Creating labels..."
# Type labels
gh label create "Type: feature" --color "0E8A16" --description "New feature" -R "$REPO" || true
gh label create "Type: bug"     --color "E7041F" --description "Something is not working" -R "$REPO" || true
gh label create "Type: task"    --color "5319E7" --description "Engineering or documentation task" -R "$REPO" || true
gh label create "Type: research" --color "1D76DB" --description "Research or investigation" -R "$REPO" || true

# Priority labels
gh label create "Priority: P0" --color "B60205" --description "Critical priority" -R "$REPO" || true
gh label create "Priority: P1" --color "D93F0B" --description "High priority" -R "$REPO" || true
gh label create "Priority: P2" --color "FBCA04" --description "Normal priority" -R "$REPO" || true

# Team labels
for team in frontend backend design infra data qa; do
  gh label create "Team: $team" --color "C2E0C6" --description "Owned by the $team team" -R "$REPO" || true
done

# Status labels
for status in "blocked" "in progress" "review" "validated"; do
  gh label create "Status: $status" --color "CCCCCC" --description "Issue is $status" -R "$REPO" || true
done

echo "Creating milestones..."
gh api repos/$REPO/milestones -f title="M1: MVP Pilot" --field due_on="2025-09-30T00:00:00Z" || true
gh api repos/$REPO/milestones -f title="M2: Public Beta" --field due_on="2025-11-30T00:00:00Z" || true
gh api repos/$REPO/milestones -f title="M3: General Launch" --field due_on="2026-01-31T00:00:00Z" || true

echo "Creating issues..."
gh issue create -t "Design wireframes" -b "Create initial wireframes as described in design/wireframes.md" -l "Type: task" -l "Team: design" -l "Priority: P1" -m "M1: MVP Pilot" -R "$REPO"
gh issue create -t "Draft AI specs" -b "Define AI microservice inputs and outputs based on services/ai-microservice-specs.md" -l "Type: task" -l "Team: backend" -l "Priority: P1" -m "M1: MVP Pilot" -R "$REPO"
gh issue create -t "Define frontend architecture" -b "Outline UI/UX stack and state management in web/frontend-architecture.md" -l "Type: task" -l "Team: frontend" -l "Priority: P1" -m "M1: MVP Pilot" -R "$REPO"
gh issue create -t "Sketch infra plan" -b "Write initial infrastructure and IaC sketch in infra/deployment-manifests.md" -l "Type: task" -l "Team: infra" -l "Priority: P1" -m "M1: MVP Pilot" -R "$REPO"

echo "Creating project board..."
# Create a new Project (v2).  Capture the project ID for adding columns.
PROJECT_JSON=$(gh api --method POST -H "Accept: application/vnd.github+json" \
  /user/projects -f name="Product Roadmap" -f body="Roadmap for Knowledge Harvest" )
PROJECT_ID=$(echo "$PROJECT_JSON" | jq -r .id)

# Add columns to the project board
for column in "Backlog" "To Do" "In Progress" "Review/QA" "Done"; do
  gh api --method POST -H "Accept: application/vnd.github.inertia-preview+json" \
    /projects/$PROJECT_ID/columns -f name="$column"
done

echo "Project setup complete."