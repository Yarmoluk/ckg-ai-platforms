# Agent Platform Atlas MCP Plan

Date: 2026-09-10

## Objective

Make `ckg-ai-platforms` the public GitHub/PyPI MCP package for the agent-platform atlas use case.

## Scope

- Keep the existing PyPI package name: `ckg-ai-platforms`.
- Add public-facing atlas tools for cross-platform inspection.
- Add the Microsoft Agent Framework CKG as a packaged domain.
- Update README and server metadata so the GitHub repo explains what people can do with it.
- Bump to a minor version because the MCP surface gains new tools and a new domain.

## Guardrails

- Public vendor documentation only.
- No private notes, session files, customer graphs, contact research, or strategy graphs.
- Do not claim Palantir as packaged until a clean standalone public graph source exists.
- Local stdio remains the supported transport for this PyPI package.
- HTTP, A2A, x402, and hosted distribution remain future scope.

## Verification

- Import/package smoke tests.
- Direct function tests for new atlas tools.
- Build wheel/sdist locally.
- Inspect final git diff before any remote push or PyPI release.
