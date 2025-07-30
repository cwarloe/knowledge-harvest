# Wireframes & User Flows

The wireframes below describe the core user journeys for capturing tacit knowledge.  Mermaid diagrams are used to visualise flows; you can render them in supported viewers.

## Capture workflow

```mermaid
flowchart TD
    A[Start capture] --> B[Record screen & audio]
    B --> C[Add highlights / annotations]
    C --> D[Stop capture]
    D --> E[Review & edit]
    E --> F[Submit to transcription service]
    F --> G[AI summarisation & tagging]
    G --> H[Publish to knowledge library]
```

**Description:**  The SME launches the recorder (`A`), which captures both the screen and spoken explanation (`B`).  During recording, the user can add highlights or on‑screen notes (`C`).  After stopping (`D`), they review the recording and trim sections (`E`).  The video is then sent to microservices for transcription and summarisation (`F`,`G`) before being published (`H`).

## Knowledge library page

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#E3F2FD', 'secondaryColor': '#BBDEFB', 'borderRadius': '4px' }}}%%
flowchart LR
    A[Search bar] --> B[Knowledge list]
    B --> C[Recording card]
    C --> D[View details]
    D --> E[Transcript & summary]
    D --> F[Linked case studies]
```

The library page contains a search bar for filtering content and a list of recording cards (`B`).  Selecting a card opens a detail view (`D`) with the transcript, summary, tags and related case studies (`E`,`F`).


## 📊 Annotation Extraction Workflow

```mermaid
flowchart TD
  A[Recording Complete] --> B[Metadata Extraction Service]
  B --> C{Contains Annotations?}
  C -- Yes --> D[Parse Highlights + Narration Timing]
  D --> E[Generate Structured Callouts]
  E --> F[Attach Callouts to Training Docs]
  C -- No --> G[Log and Flag for Manual Review]
```

> TIP: This flow assumes successful recording ingestion and structured timestamping. Future enhancements may include NLP validation or audio confidence scoring.
