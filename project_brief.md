# My agent: IT Service Desk Copilot

**One-liner**: A conversational agent that helps IT support engineers quickly diagnose technical issues, search knowledge bases, manage support tickets, and generate troubleshooting diagrams.

## Tool coverage:
- **Memory**: Remembers support engineer preferences (e.g. preferred OS/CLI tools, primary team/department, SLA thresholds, and active issue context across sessions).
- **Tools**:
  - `search_knowledge_base`: Searches technical documentation and resolution guides stored in Firestore.
  - `create_support_ticket`: Creates new IT support tickets with severity, system component, and issue description.
  - `check_ticket_status`: Queries existing tickets and updates status or adds resolution notes.
- **Catalog/UI**: Interactive ticket queue tables, ticket detail cards, and KB article summary cards rendered using A2UI.
- **Image gen**: Generates troubleshooting flowcharts, network topology diagrams, or system architecture visual guides.
- **Sandbox**: Parses raw log files/tracebacks and computes SLA metrics or diagnostic script outputs.

**Recommended for every project**: Memory, Firestore Storage, Function Tools, Image Generation, A2UI Cards
**Agent-specific / stretch**: Code Sandbox for log parsing & SLA calculations, Cloud Trace for request telemetry.
