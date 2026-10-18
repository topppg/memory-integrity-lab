# Security model and reporting

This is an offline engineering regression tool with synthetic fixtures. It is
not a production memory service or a security certification.

Authenticated application code must assign tenant, subject, and source labels.
Those strings are not credentials. A caller who can supply `source="user"` or
change tenant/subject is outside the store-policy threat model. `ScopedAdapter`
enforces an application-assigned scope, not user authentication.

`audit.seal` and `audit.verify` detect changed, reordered, added, removed, or
truncated records only when the original **count and head digest** are held in
a separate trusted location. A digest stored with the archive is insufficient.
An attacker who can replace the anchor and archive can forge a valid chain.
The tool does not provide signatures, secret storage, encryption, rollback
protection for an untrusted anchor, or continuous SQLite file verification.
Take a consistent event snapshot before sealing and keep the anchor externally.

Deletion is logical suppression during retrieval, including historical queries
and replay. SQLite, audit exports, and reports can retain plaintext. This is
not physical erasure, backup erasure, cryptographic erasure, or a regulatory
compliance claim. A later explicit user write after the tombstone can create a
new memory for that key. A missing tombstone in an unverified export cannot be
detected by the memory adapter alone; verify an anchored archive before replay.

Plugins execute trusted local Python code and can access the host. HTML reports
escape dynamic content and contain no external assets, but report files still
contain the supplied values. Never load untrusted plugins.

To report a concern, use the repository owner's private security-reporting
channel when enabled, or contact the owner through their GitHub profile. Avoid
posting exploit payloads containing actual private information in public issues.
