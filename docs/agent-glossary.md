# Agent Architecture Glossary

| Term                 | Definition                                                                                                                                                     |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent**            | An autonomous or semi-autonomous system that perceives its environment, makes decisions based on context, and executes actions to reach a specific goal.       |
| **Bounded Autonomy** | Agency constrained within explicit, hard-coded limits (such as max iterations, fixed tool allow-lists, and human approval checkpoints).                        |
| **Sense**            | The initial phase where the agent gathers context, reads state, and parses the latest user query or environment observation.                                   |
| **Plan**             | The decision-making phase where the model determines the next logical action (calling a tool, querying RAG, or generating a response) based on state and goal. |
| **Act**              | Executing the chosen action (e.g., executing a database write, running a vector search, or invoking an API).                                                   |
| **Observe**          | Reading and storing the execution output from the **Act** step to update internal memory and context state.                                                    |
| **Evaluate**         | Checking active stop conditions (e.g., goal reached, limit hit) to decide whether to iterate again or terminate.                                               |
| **Stop Condition**   | A hard rule or metric that immediately halts the agent's loop to prevent infinite execution or runaway API usage.                                              |
| **Human Hand-off**   | Escalating control to a human supervisor when high-impact side effects (like write operations) or restricted actions are requested.                            |
| **Execution Trace**  | A structured, step-by-step audit record logging all inputs, tool calls, RAG queries, decisions, and outputs for a single agent session.                        |
| **Iteration**        | One complete sequence through the **Sense → Plan → Act → Observe → Evaluate** loop.                                                                            |
| **Tool Allow-list**  | The explicitly defined, static set of executable functions or APIs available to the agent.                                                                     |
| **Approval Gate**    | A safety checkpoint requiring explicit human authorization before executing specific sensitive actions.                                                        |
