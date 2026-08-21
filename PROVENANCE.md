# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`). The value in
  `artifacts/manifest.json` was independently cross-checked against
  argentum-core's own reference implementation
  (`plugins/agt_evidence_anchor/action_ref.py`) and matches byte-for-byte.
- The tool-call shape (`retry_http_request_with_x402`, `selectedPaymentOption`,
  the `paymentProof` field) is modeled on coinbase/agentkit's own public
  source, not invented:
  - [`typescript/agentkit/src/action-providers/x402/x402ActionProvider.ts`](https://github.com/coinbase/agentkit/blob/main/typescript/agentkit/src/action-providers/x402/x402ActionProvider.ts)
    documents `retryWithX402` (`retry_http_request_with_x402` action): a real
    x402 payment is dispatched via `wrapFetchWithPayment`, and on a `200`
    response the provider returns
    `{status: "success", details: {paymentUsed, paymentProof}}` where
    `paymentProof` is decoded straight from the `payment-response` /
    `x-payment-response` response header — "Payment is only settled on 200
    status" (comment in the source), reported by the provider itself.
- The on-chain anchor (once `artifacts/anchor.json` exists) is a real
  transaction on Base mainnet; the tx hash and block are independently
  checkable by anyone via `verifier/verify.py`.

## What is synthetic — declared

- **No running AgentKit instance was called, and no real x402 payment was
  made.** `agent_id`, `timestamp`, `request`, and `result` (including
  `result.details.paymentProof.transaction`, which is not a real
  transaction) are all constructed in `scripts/produce.py`, not captured
  from a live `retryWithX402` call or a real facilitator settlement.
- **The `request_digest` / `result_digest` envelope fields are this repo's
  own addition**, not part of `action-ref-v1`'s four-field hash. They exist
  to demonstrate — concretely, with anchored hashes — what a
  content-addressed, third-party-checkable receipt for an x402 payment
  dispatch could look like. They do not enter the `action_ref` preimage;
  the spec is explicit that only the four canonical fields are hashed.

## Related work — not a duplicate

`coinbase/agentkit#1170` (giskard09, opened 2026-05-07, still open as of this
writing) adds a read-only MyceliumTrails action provider to AgentKit itself
(`verify_trail`/`compute_action_ref`/`get_trails`) for verifying agent trails
generically, from inside an agent's own toolset. This worked example is a
separate, narrower thing: a standalone, independently-reproducible instance
of anchoring one specific action (`X402ActionProvider.retryWithX402`'s
payment dispatch) — same pattern as the Binance/OKX/Kraken worked examples
published the same day. It does not modify, extend, or duplicate #1170.

## What this therefore does and does not show

- **Does show:** the `action_ref` derivation applies unchanged to AgentKit's
  own documented `retryWithX402` call shape — same four fields, same JCS +
  SHA-256 path used by every other emitter in the spec's cross-reference
  list. Given a real x402 payment dispatched through a real AgentKit agent,
  the identical path produces a verifiable, content-addressed identifier for
  that call, independently anchorable by anyone — not just the facilitator
  or Coinbase.
- **Does not show:** that Coinbase, AgentKit, or anyone else has integrated,
  endorsed, or adopted `action_ref`. It is our worked example applying a
  public spec to AgentKit's public tool-call shape. No claim of "Coinbase
  integrated us," no claim of on-chain adoption, no cited quote. If someone
  reads it as adoption, that reading is wrong.
