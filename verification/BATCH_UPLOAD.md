# Batch upload verification

**Observed (source):** A new administrator Batch upload dialog selects multiple local files, prefills titles from filenames, reads native audio duration (with manual fallback), allows shared artist/album/genre and per-track metadata/cover changes, and uploads ready files sequentially through POST /api/admin/songs. Each request remains an independent transaction with existing session, CSRF, ADMIN, upload and ML controls. No backend API/schema changes were needed.

**Observed (source):** Successful tracks are locked in the queue and excluded from subsequent retries. A rejected track can be edited or have its audio replaced. A network/server error whose commit outcome is unknown is marked for manual collection review and excluded from retries. Closing the dialog refreshes the collection. The upload dialog cannot close during an active batch. Limits are 25 selected files, 25 MiB/audio, 5 MiB/cover. Unsaved browser selections are not persisted across closing/reloading.

**Observed:** Frontend tests passed 10/10 (the previous 5 plus 5 batch tests). New tests cover required metadata and prefills, partial success/retrying only rejected tracks, unknown network outcomes, permission-denial stop/close guard, invalid type, duplicate selection and the batch size limit. These use isolated API/metadata mocks and establish client behavior only.

**Observed:** The frontend production build passed. The first build/test attempts caught a Windows resolution collision between BatchUpload.jsx and batchUpload.js. The helper was renamed batchFiles.js; Vite was restarted to clear its stale development module path. Failed results are retained in timestamped previous logs.

**Observed:** Eleven real Edge/API checks passed against running Spring, real isolated MySQL and FastAPI: empty batch state; real native duration/filename prefills/missing details; shared and individual metadata plus cover; two successful uploads around a malformed file (201/400/201); replacement/retry with exactly one extra POST (201); three persisted DTOs with actual READY features; exact authenticated Range bytes; mobile fit; post-batch metadata editing; no page errors; listener role denial (403).

**Observed:** Only test songs identified by the unique test batch were deleted after verification. Credentials remained in private environment/runtime storage. Evidence: batch-results.json, logs/batch-upload-smoke.log and commands.jsonl.

**Observed - exact commands:** `python verification/runtime.py frontend-tests`, `python verification/runtime.py frontend-build`; browser execution through the existing recording helper calls `python verification/batch_upload_smoke.py` from the repository root. The register contains actual argv, working directories and exits. Java/ML source was unchanged, so previous backend/Python results remain historical evidence; they were not rerun for this frontend change.

**Unverified:** Native MP3/OGG duration detection, model accuracy and Docker execution were not re-established by the tested WAV/Edge batch scenario. Genre prediction remains an explicit placeholder when no compatible model is configured.
