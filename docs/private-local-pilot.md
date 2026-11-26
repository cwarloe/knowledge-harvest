# Private local pilot (synthetic data only)

This is a **development-only**, opt-in owner pilot. No cloud deployment, client recording, external sharing, or production permission change is authorized by this work. The existing ordinary local development mode remains unchanged; **it is anonymous and must not hold client data**.

The pilot starts only with `KH_PRIVATE_PILOT=1`, a long secret, a localhost-only browser origin, and a dedicated localhost PostgreSQL database and absolute upload directory. Startup refuses missing/unsafe configuration. The API binds only to `127.0.0.1` in pilot mode. Recording metadata, upload, deletion and direct video downloads require a temporary HttpOnly session cookie; logout revokes it. Mutations additionally require an exact browser `Origin`. Five failed access-token attempts block further attempts for 15 minutes per source IP. Restart invalidates all sessions.

## Run locally

1. Install the existing `services` and `web` dependencies with `npm ci` in each directory. Start a separate local PostgreSQL service. Create a **new empty database** named `kh_pilot` and load `services/pilot-schema.sql` into it. Do not run the general `services/schema.sql` because it seeds dummy rows pointing at nonexistent videos.
2. Choose a new, random access token of at least 32 characters. Do not commit it, paste it in an issue, or reuse another account password.
3. In the API shell, set the following local environment variables (substitute a locally generated secret, local PostgreSQL credentials, and a private absolute storage directory):

   ```bash
   export KH_PRIVATE_PILOT=1
   export KH_PILOT_ACCESS_TOKEN='REPLACE_WITH_32_PLUS_RANDOM_CHARACTERS'
   export KH_PILOT_ALLOWED_ORIGIN='http://localhost:3000'
   export KH_PILOT_DATABASE_URL='postgres://pilot:LOCAL_PASSWORD@127.0.0.1:5432/kh_pilot'
   export KH_PILOT_UPLOAD_DIR='/absolute/private/path/kh-pilot-uploads'
   cd services && npm start
   ```

4. In a separate shell, run `cd web && npm start`. Open `http://localhost:3000`, enter the local access token, and make **only a synthetic test recording** (for example a slide saying “FAKE DEMO”). Confirm browse, playback, download, logout and denial after logout. No real client screens, names or files should be used.

This flow deliberately has no public tunnel, hosted endpoint, invite/share mechanism, or remote identity provider. It is not a production-grade multiuser authorization system. Reverse-proxy, CSRF, data retention, backups, end-to-end record deletion, account recovery and deployment design require a separate security/privacy review before any remote use.

## Automated safety checks

Run `cd services && npm ci && npm test -- --runInBand` to check rejection of anonymous recording reads/writes/deletes, raw-video access, bad tokens, cross-origin requests, unsafe configuration, and session revocation. The frontend remains the existing React client and sends credentials only to the configured API.
