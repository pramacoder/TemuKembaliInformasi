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
