# Issue publication recovery record — 2026-10-25

## Frozen public content

- Title SHA-256: c9b4826b3c8ce272792fb4fc29ae22e27a5354c70958e8562f3b17d019938bc7
- Body SHA-256: 3365a1d990c7c698fce80db7917806fe198b0d85cee95e8e80dcaa23ef2b71ce
- Intended target: tester-army/e2e, label bug.

## Bounded attempts

1. `gh issue create` with the frozen title/body failed before a URL was returned: `Post "https://api.github.com/graphql": net/http: TLS handshake timeout`.
2. A read probe authenticated as BiBoyang and an author listing showed no new issue. A GraphQL title query also timed out; a REST title search returned no match. The same `gh issue create` command was retried once and returned the same GraphQL TLS handshake timeout.
3. After another empty REST title search, the same frozen content was submitted once through the REST issue endpoint to avoid the repeatedly failing GraphQL channel. `POST /repos/tester-army/e2e/issues` also failed with `net/http: TLS handshake timeout`.

No fourth create was attempted. Three public-write attempts are the hard stop for this run.

## Final read-only state

- The final REST title search for `thrown store write` returned no matching issue.
- A second recent-author query failed with a TLS handshake timeout and was not retried.
- No issue URL was obtained. The evidence branch was not pushed, and no PR was started.

Recorded at 2026-10-25 11:04:28. The next publication attempt should start from the frozen title/body and the duplicate-title check, not from an assumption that the timeout meant either success or failure.

## Resumed publication and permission note

- On the user-requested resume, the first REST title query timed out and no create ran. A fallback read of the current account's recent issues succeeded and showed no matching title. The next `gh issue create` succeeded as [tester-army/e2e#1371](https://github.com/tester-army/e2e/issues/1371).
- Remote title, body, and OPEN state were compared with the frozen local files and matched.
- The create request's `bug` label did not take effect. A follow-up `gh issue edit --add-label bug` was rejected: `GraphQL: BiBoyang does not have the correct permissions to execute AddLabelsToLabelable`. No alternative write or permission bypass was attempted; the issue remains unlabeled for a maintainer to classify.

- The evidence branch was subsequently pushed through commit `85babcf0ee145fe4c7d7babba8647c23a6fde830`; local and upstream SHA matched. Disclosure public-status fields are finalized in the following commit.
