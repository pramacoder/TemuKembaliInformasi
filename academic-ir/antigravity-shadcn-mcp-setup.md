# Antigravity + shadcn/ui MCP — Executable Setup

Target: Windows + Google Antigravity IDE/CLI + Next.js + TypeScript + shadcn/ui.

Official references:
- shadcn MCP: https://ui.shadcn.com/docs/mcp
- shadcn installation: https://ui.shadcn.com/docs/installation
- Antigravity MCP: https://www.antigravity.google/docs/mcp

## 1. Prerequisites

Run:

```powershell
node --version
npm --version
```

If the Next.js project does not exist:

```powershell
npx create-next-app@latest academic-ir
cd academic-ir
```

Recommended answers:

```text
TypeScript:       Yes
ESLint:           Yes
Tailwind CSS:     Yes
src/ directory:   Yes
App Router:       Yes
Import alias:     @/*
```

## 2. Initialize shadcn/ui

From the project root:

```powershell
npx shadcn@latest init
```

Test it:

```powershell
npx shadcn@latest add button card input
```

## 3. Initialize shadcn MCP

Run:

```powershell
npx shadcn@latest mcp init
```

If Antigravity is not offered as a client, configure it manually as described below.

## 4. Configure workspace MCP for Antigravity

Antigravity supports project-level MCP configuration at:

```text
.agents/mcp_config.json
```

Create the directory:

```powershell
New-Item -ItemType Directory -Force .agents
```

If no MCP config exists yet, create it:

```powershell
@'
{
  "mcpServers": {
    "shadcn": {
      "command": "npx",
      "args": ["shadcn@latest", "mcp"]
    }
  }
}
'@ | Set-Content -Encoding UTF8 .agents\mcp_config.json
```

If `.agents/mcp_config.json` already contains other servers, DO NOT overwrite it. Add this entry inside `mcpServers`:

```json
"shadcn": {
  "command": "npx",
  "args": ["shadcn@latest", "mcp"]
}
```

Validate the JSON:

```powershell
Get-Content .agents\mcp_config.json -Raw | ConvertFrom-Json
```

## 5. Restart/reload Antigravity

In Antigravity IDE:

```text
Agent panel
  -> ...
  -> MCP Servers
  -> Manage MCP Servers
  -> View raw config
```

Confirm that `shadcn` is present and connected.

For Antigravity CLI, use:

```text
/mcp
```

to inspect MCP status and logs.

## 6. Test the MCP

### Test A — registry discovery

Ask the Agent:

```text
Use the shadcn MCP.

List the available components from the shadcn registry.
Do not modify the project.
```

### Test B — search

```text
Use the shadcn MCP to find components suitable for:
- search input
- filters
- result cards
- tabs
- pagination

Do not modify the project.
Return the component names and explain briefly why each is relevant.
```

### Test C — install

```text
Use the shadcn MCP to install:
- button
- card
- input
- badge
- separator

Only install components that are not already present.
```

### Test D — compose

```text
Use the existing shadcn components to create an academic
document search result card.

Requirements:
- title
- document type badge
- year
- source
- relevance score
- snippet
- open button

Do not introduce another UI library.
```

## 7. Create AGENTS.md

Create this file in the project root:

```text
academic-ir/
├── AGENTS.md
├── .agents/
│   └── mcp_config.json
├── components.json
├── package.json
└── src/
```

Use the following content:

```md
# Agent Development Rules

## Project

This project is an academic document information retrieval system.

Frontend:
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide Icons

Backend will use Python/FastAPI separately.

## UI Rule

Before creating a new UI component:

1. Inspect the existing project.
2. Check `src/components/ui`.
3. Use the shadcn MCP to search for an existing component.
4. Prefer an existing shadcn component when appropriate.
5. Only create a custom component when an existing component does not satisfy the requirement.

Never recreate a shadcn component manually without a reason.

## Component Rule

Prefer these components when applicable:

- Button
- Card
- Input
- Badge
- Dialog
- Sheet
- Select
- Checkbox
- DropdownMenu
- Tabs
- Table
- Pagination
- Skeleton
- Tooltip
- Separator

## Styling Rule

Use:
- Tailwind CSS
- shadcn design tokens
- CSS variables
- responsive classes

Avoid:
- unnecessary custom CSS
- inline styles when Tailwind can solve the problem
- introducing another component library without explicit approval

## Icon Rule

Use Lucide icons when an appropriate icon exists.

Do not manually create SVG icons unless necessary.

## Accessibility

Components must:
- have accessible labels
- support keyboard interaction
- use semantic HTML
- maintain readable contrast
- have visible focus states

## Responsive Design

Every page must work on:
- mobile
- tablet
- desktop

## Agent Workflow

Before implementing a UI feature:

1. Inspect existing code.
2. Identify reusable components.
3. Search shadcn MCP.
4. Install missing shadcn components if required.
5. Implement the feature.
6. Run lint/type checks.
7. Fix errors.
8. Only then consider the feature complete.

## Important

Do not install another UI framework unless explicitly requested.

Do not replace shadcn/ui with another component library.

Do not unnecessarily rewrite existing components.

Keep components modular and reusable.
```

## 8. Test the application

Run:

```powershell
npm run lint
```

Then:

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

## 9. First real Agent task

After MCP is connected, give Antigravity this prompt:

```text
Build the initial UI for my Academic Information Retrieval system.

Before coding:

1. Inspect AGENTS.md.
2. Inspect the existing project.
3. Use the shadcn MCP to find suitable components.
4. Reuse existing shadcn components.
5. Install missing components through shadcn MCP when necessary.

Create:
- application header
- academic document search bar
- filter sidebar
- search result cards
- document type badge
- relevance score
- pagination

Use only:
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide icons

Do not add another UI library.

Do not implement the backend yet.
Use mock search results.
```

## 10. Recommended architecture for Academic IR

```text
                         ANTIGRAVITY AGENT
                                |
                    +-----------+-----------+
                    |                       |
               shadcn MCP              Project
                    |                   AGENTS.md
                    |                       |
                    +-----------+-----------+
                                |
                         Next.js Frontend
                                |
                         REST API / JSON
                                |
                         FastAPI Backend
                                |
              +-----------------+-----------------+
              |                 |                 |
          Retrieval         Metadata DB         Files
              |                 |                 |
            TF-IDF            SQLite              PDF
              |
       Cosine Similarity
```

## 11. Troubleshooting

### MCP does not appear

Check:

```powershell
Get-Content .agents\mcp_config.json
```

Expected:

```json
{
  "mcpServers": {
    "shadcn": {
      "command": "npx",
      "args": ["shadcn@latest", "mcp"]
    }
  }
}
```

Then reload/restart Antigravity.

### MCP has no tools

Try:

```powershell
npx clear-npx-cache
```

Then restart/reload the MCP server.

Also verify that:

```powershell
npx shadcn@latest add button
```

works from the project root.

### Component installation fails

Check:

```powershell
Get-Content components.json
```

and make sure the project has a valid shadcn configuration.

## 12. Definition of Done

- [ ] Next.js runs
- [ ] shadcn/ui initialized
- [ ] `components.json` exists
- [ ] `.agents/mcp_config.json` exists
- [ ] Antigravity detects `shadcn`
- [ ] Agent can discover the registry
- [ ] Agent can search components
- [ ] Agent can install components
- [ ] `AGENTS.md` exists
- [ ] `npm run lint` succeeds
- [ ] `npm run dev` succeeds
- [ ] First UI uses shadcn/ui
- [ ] No unnecessary UI framework is added

## 13. Development order

```text
Phase 1
Next.js + shadcn + MCP
        |
Phase 2
Academic IR UI with mock data
        |
Phase 3
FastAPI
        |
Phase 4
TF-IDF retrieval
        |
Phase 5
SQLite metadata
        |
Phase 6
PDF/document preview
        |
Phase 7
Search + filters
        |
Phase 8
Evaluation
        |
Phase 9
Production refinement
```

Start by making the MCP connection work. Only after the Agent can successfully discover and install shadcn components should you proceed to the full Academic IR UI.
