# Tool Orchestration Architecture

## Overview
The orchestration layer sits between the application and the model, deciding
what happens after the model responds: answer directly, call a read-only
tool, or call a write tool that first needs human approval. Every path
converges before the model generates its final response, so the model
always sees a consistent "tool result + observation" shape regardless of
which branch was taken.

## Calling Flow (Figure 1)