# Service/UI interruption — support handoff (not submitted)

## Observed, not a backend diagnosis

The supplied screenshots show these notices:

- “The AI service encountered an error. Please try again.”
- “The connection to the AI service was interrupted. Please try again.”
- “Please respond to the pending question before sending a new message. If you don't see one, refresh the page and try again.”

An earlier clarification tool returned an empty answer list with `skipped: true`.
The later screenshot still showed the pending-question notice. The user reports
that the error recurs; whether Refresh was performed is not independently
verified. No new interactive question/image-choice popup was opened during the
subsequent character-design work.

Arena backend/provider/request logs and the client's pending-question state
are not accessible from this repository. No claim is made about the root cause,
that a server-state reset has happened, or that the service has been repaired.
This note has not been sent to support automatically.

## Local work recovered and verified

A later workspace retained source/receipts but lacked local binary media.
The existing saved Drive ZIP was downloaded; all 13 registered outputs were
restored with matching hashes. No character was regenerated, no source footage
was re-composited, and no user re-upload or choice was required.

A standard-library-only recovery helper now makes that recovery repeatable,
refuses to overwrite differing art, and rejects path traversal. Its four new
regression tests passed. File recovery does not repair the UI/service notices.

## Suggested support message

> This conversation repeatedly displays both “connection to the AI service was
> interrupted” and a “pending question” notice. The earlier question was
> recorded as skipped by the tool, but the UI still reports it as pending.
> Please inspect the conversation's pending-question state and interrupted
> request logs. If the question is confirmed stale, please clear that stale
> state without deleting the conversation or project. I can supply the error
> screenshot. No account credentials or private media are needed in this report.

## Separate production limitation

The delivered artifacts are character/shot-design stills and documents.
Actual photoreal character animation and the final edited film remain unrendered;
the session exposes no direct photoreal image-to-video generation tool. This
capability limitation is separate from the reported service/UI interruption.


## Subsequent production update

After this incident record, the user approved an explicitly limited 2.5D
recreation. A complete V1 is now delivered; see the latest active state and
`records/rigged-full/DELIVERY.json`. This does not change the historical service
observations, constitute an Arena backend repair, or establish exact/natural 3D
performance. No support ticket was submitted automatically.
