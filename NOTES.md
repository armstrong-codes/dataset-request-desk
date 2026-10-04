# Engineering Notes

## 1. Design

The relational model is intentionally small:

```text
users 1 ---- * dataset_requests
users 1 ---- * status_history
users 1 ---- * assignments

dataset_requests 1 ---- * assignments * ---- 1 episodes
```

`dataset_requests.status` is the current state. `status_history` is the append-only audit trail. `assignments` is a join table with a unique constraint on `episode_id`, enforcing the rule that an episode is assigned to at most one request.

### Hard decisions

1. **PostgreSQL + migrations:** PostgreSQL matches the task and gives strong constraints and aggregation functions. Alembic keeps schema changes reproducible.
2. **Server-side workflow rules:** transition validation lives in the backend service, not React. This means a malicious client cannot bypass the workflow by calling the API directly.
3. **CSV policy:** valid records are imported; invalid records are skipped with a reason. IDs are the idempotency key. Normalizing task/quality text avoids treating casing/whitespace differences as different values.

## 2. Deliberately simplified

- The UI is intentionally small rather than a polished production dashboard.
- Admin user-management endpoints/UI are not implemented in this first pass even though the role model exists. With another day, I would add create/deactivate/change-role screens and tests.
- Analytics has no charts; the API is the important part for the test.
- JWT access tokens are stateless and short-lived; production would likely add refresh-token rotation or an SSO provider.
- Episode assignment does not yet expose a dedicated "assigned" filter in the UI.

## 3. Something that went wrong

The seed CSV intentionally contains malformed rows, duplicates, missing values, inconsistent casing, and an unknown robot. During import design, a tempting approach was to insert each row and roll back when a duplicate appeared. That can accidentally roll back earlier valid inserts in the same transaction. The final importer therefore checks the episode ID before insertion and accumulates valid rows in one transaction.

## 4. Security

Passwords are hashed with scrypt and are never stored as plaintext in the database. API authorization is enforced from the authenticated user's role and ownership checks. Pydantic validates request bodies, and SQLAlchemy parameterizes database queries.

Two major risks I would worry about next:

1. **Broken object-level authorization:** a client must never be able to access another client's request by changing an ID in the URL. The request endpoints explicitly check ownership.
2. **Credential/token abuse:** production would require HTTPS, a strong secret from a secret manager, token expiry/rotation, rate limiting on login, audit alerts, and preferably organization SSO.

## 5. Scale

At 10x users, database connection pooling, login rate limiting, and frontend/API observability become more important. At 100x episodes, analytics and inventory queries are the first likely pressure points. PostgreSQL indexes support the main filters. For substantially larger volume I would inspect `EXPLAIN ANALYZE`, add workload-specific composite/partial indexes, consider date partitioning, and move expensive analytics to pre-aggregated tables or a warehouse. Import could become a background job with progress reporting.

## 6. AI tooling

AI assistance was used for scaffolding, debugging ideas, and documentation.
