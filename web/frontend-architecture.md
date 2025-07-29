# Front‑End Architecture

The front‑end of Knowledge Harvest aims to deliver a responsive, accessible and intuitive experience for capturing and consuming tacit knowledge.

* **Framework:** Built with React (or Preact) using TypeScript.  React’s component model facilitates modular UI development.  For state management, we recommend React Query for asynchronous state (e.g. recording status, transcripts) and Zustand or Redux Toolkit for global UI state.
* **Capture component:** Uses the browser’s `MediaRecorder` API to capture screen and audio streams.  A custom hook manages recording state and uploads to the Capture Service.  Annotating highlights is handled by overlay components.
* **Knowledge library:** The library page fetches paginated search results from the Search Service.  Lazy loading and infinite scrolling are used to handle large datasets.  The transcript and summary viewer uses syntax highlighting to emphasise important phrases.
* **Routing & data fetching:** Next.js or React Router provide client‑side routing.  Data fetching is abstracted into API hooks that call the respective microservices.
* **Accessibility:** Keyboard navigation and ARIA labels are provided across components.  Since tacit knowledge is often informal and subjective【261120688409170†screenshot】, transcripts must be presented in a readable, navigable format.
* **Error handling:** Use toast notifications to inform users about upload progress, errors or successful publication.  Retry mechanisms should be in place for network calls.