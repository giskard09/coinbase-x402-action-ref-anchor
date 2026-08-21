# coinbase-x402-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
for a synthetic **coinbase/agentkit** `X402ActionProvider.retryWithX402` call
(`retry_http_request_with_x402` action), and anchors it permissionlessly
on-chain, giving it a property the call itself does not have on its own: an
**externally verifiable, third-party-checkable record of what happened**,
independent of AgentKit's / the facilitator's own report.

The timestamp of the anchor is the point. This is not outreach and not a
claim of adoption — it is a worked example, byte-exact against the public
spec and AgentKit's own documented tool-call shape.

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> The `action_ref` here is derived exactly per `action-ref-v1` and
> cross-checked against argentum-core's own reference implementation. The
> tool-call shape (`retry_http_request_with_x402`, `selectedPaymentOption`,
> `paymentProof`) is modeled on coinbase/agentkit's **public source**
> ([`coinbase/agentkit`](https://github.com/coinbase/agentkit)) — but it was
> **NOT produced by a running AgentKit instance**: no live
> `retryWithX402` call, no real wallet, no real x402 payment settled.
> Nothing here — on-chain or in this repo — implies that Coinbase
> integrated, endorsed, or participated. It is our worked example applying a
> public spec to their public tool-call shape.

## The gap

`X402ActionProvider.retryWithX402` dispatches a real x402 payment
(EIP-3009 authorization via `wrapFetchWithPayment`) and, on success, reports
`{status: "success", details: {paymentUsed, paymentProof}}` — where
`paymentProof` is decoded straight from the `payment-response` /
`x-payment-response` header the facilitator sent back. That report is the
provider's (and ultimately the facilitator's) own account of settlement — a
third party auditing the agent's behavior after the fact has no
independent way to confirm a declared request/result pair without trusting
that self-report.

`action_ref` closes part of that gap: it's a content-addressed identifier
any party can recompute from four declared fields (`agent_id`, `action_type`,
`scope`, `timestamp`) — no trust in the emitting system required. This repo
extends that with an **envelope** carrying `request_digest` and
`result_digest` — hashes of the exact request and reported result a verifier
would need to confirm what was proposed and what was reported, independently
recomputable from the declared JSON.

```
   AgentKit x402 call (retryWithX402)        public chain (Base)
   ┌───────────────────────────┐            ┌────────────────────────┐
   │ agent_id, action_type,     │  JCS+SHA256│ AnchorRegistry         │
   │ scope, timestamp           │───────────▶│  anchor(bytes32 ref)   │
   │ + request/result digests   │  action_ref│  Anchored(ref,by,time) │
   │   (envelope)                │            └────────────────────────┘
   └───────────────────────────┘             operator-independent
        no external record                   timestamp / finality
```

## Doctrine: spec-agnostic to AgentKit's format

We derive `action_ref` from the four canonical fields only. We do **not**
ask Coinbase or AgentKit to adopt any anchoring infrastructure, change its
API, or emit any new fields. The integration lives entirely in how a receipt
*could* be shaped and anchored; AgentKit's tool-call shape is the input, the
anchor is the added property.

## Related work — not a duplicate

[`coinbase/agentkit#1170`](https://github.com/coinbase/agentkit/pull/1170)
(giskard09, opened 2026-05-07) is a separate, earlier PR that adds a
read-only MyceliumTrails action provider *into* AgentKit itself. This repo
is a standalone worked example anchoring one specific action — it does not
modify, extend, or duplicate that PR. See `PROVENANCE.md`.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256) for a synthetic `retry_http_request_with_x402` call, plus the `request_digest`/`result_digest` envelope. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes both digests from the declared JSON and confirms the matching `Anchored` event on Base mainnet. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, digests, envelope) and `anchor.json` (tx/block, once anchored). |
| `PROVENANCE.md` | Exactly what is and isn't real about this artifact. Read it. |

## Reproduce

```bash
# 1. derive action_ref + the envelope digests
python3 scripts/produce.py artifacts

# 2. anchor action_ref on Base mainnet (permissionless anchor(bytes32) call)

# 3. independently verify the derivation and the on-chain anchor
python3 verifier/verify.py
```

## The anchor

- **Registry:** `0x49fEcA52bC634a9Ab773226D16619deC547794aa` (same CREATE2
  address on Base 8453, Arbitrum One 42161, Ink 57073).
- **Function:** `anchor(bytes32 ref)` — permissionless, no owner/roles/funds.
- **Event:** `Anchored(bytes32 indexed ref, address indexed anchoredBy, uint256 timestamp)`.
- The anchored `ref` for this instance and its tx/block are in
  `artifacts/anchor.json` (once anchored — see PROVENANCE.md status).

## License

MIT.
