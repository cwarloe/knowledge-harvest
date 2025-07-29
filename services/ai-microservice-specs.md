# AI Microservice Specifications

The Knowledge Harvest platform is built as a collection of small, independent services that communicate over HTTP APIs.  Such a microservices architecture structures an application from loosely coupled services, each autonomous and self‑contained, that communicate through APIs or messaging protocols【756389315289057†screenshot】.  This design allows individual services to scale independently and be updated without redeploying the entire system.

| Service | Endpoint | Method | Request | Response | Description |
|---|---|---|---|---|---|
| **Capture Service** | `/capture/start` | POST | `{ "sessionId": string, "metadata": object }` | `{ "uploadUrl": string }` | Initiates a recording session and returns a pre‑signed URL for uploading raw screen/video data. |
| | `/capture/stop` | POST | `{ "sessionId": string }` | `{ "status": "stopped" }` | Signals that recording is complete.  The service finalises storage and triggers downstream processing. |
| **Transcription Service** | `/transcribe` | POST | `multipart/form-data` containing the video file and `sessionId` | `{ "transcript": [ { "start": float, "end": float, "text": string } ] }` | Uses automatic speech recognition to convert the audio narration into time‑stamped text. |
| **Summarisation Service** | `/summarise` | POST | `{ "transcript": string, "context": object }` | `{ "summary": string, "tags": [string] }` | Generates a concise summary and topical tags from the transcript. |
| **Knowledge‑Indexer Service** | `/index` | POST | `{ "sessionId": string, "summary": string, "transcript": string, "metadata": object }` | `{ "id": string }` | Stores metadata, transcript and summary in the knowledge database and returns a unique identifier. |
| **Search Service** | `/search` | GET | query parameters `q`, `tags`, `page` | `{ "results": [ { "id": string, "title": string, "summary": string } ], "nextPage": string }` | Provides full‑text and tag‑based search over the indexed knowledge. |

Each service should define OpenAPI specifications for validation and contract tests.  Authentication and authorisation are handled via bearer tokens configured at the API gateway.

## Data flow

When an SME records a session, the Capture Service uploads the raw video to object storage.  The Transcription Service converts audio to text.  The Summarisation Service distils key points and generates tags.  The Knowledge‑Indexer persists the result and notifies the front‑end that the content is available in the knowledge library.