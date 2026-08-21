#!/usr/bin/env python3
"""
Produces an action_ref for a synthetic Coinbase AgentKit x402 provider call
(X402ActionProvider.retryWithX402 -> retry_http_request_with_x402), following
action-ref-v1 (argentum-core, JCS RFC 8785 + SHA-256) byte-for-byte, and
emits the artifacts needed to anchor + independently verify it.

PROVENANCE: this is NOT captured from a running AgentKit instance or real
x402 payment. The tool-call shape (request params, response fields) is
modeled on coinbase/agentkit's own public source
(typescript/agentkit/src/action-providers/x402/x402ActionProvider.ts,
retryWithX402): a successful call returns
{status: "success", details: {paymentUsed: {network, asset, amount},
paymentProof}} where paymentProof is decoded straight from the
payment-response / x-payment-response header the facilitator sent back —
the provider's own account of settlement, not independently checked. No
claim that AgentKit emits action_ref today, and no claim of integration,
adoption, or endorsement by Coinbase.
"""
import hashlib
import json
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md: only these four fields enter the
# hash. Modeled on X402ActionProvider.retryWithX402's real call shape
# (retry_http_request_with_x402 action), terminal executing agent is this
# worked example's synthetic identity.
timestamp = "2026-08-20T22:00:00.000Z"
preimage = {
    "agent_id": "worked-example.coinbase-x402-action-ref-anchor",
    "action_type": "agentkit.x402.retry_http_request_with_x402",
    "scope": "base:usdc:pay-and-fetch",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

# --- 2. Additive envelope fields — x402/AgentKit-specific context ----------
# These do NOT enter the action_ref hash (per action-ref-v1: only the 4
# preimage fields are hashed). They travel alongside as declared context a
# downstream verifier can check independently. request/result shape mirrors
# retryWithX402's real inputs (RetryWithX402Schema: url, method,
# selectedPaymentOption{network,asset,amount}) and its real success response
# (status, details.paymentUsed, details.paymentProof) — see
# x402ActionProvider.ts, retryWithX402().
request = {
    "url": "https://api.example.com/premium-data",
    "method": "GET",
    "selectedPaymentOption": {
        "network": "base",
        "asset": "USDC",
        "amount": "0.05",
    },
}
request_digest = sha256_hex(jcs(request))

result = {
    "status": "success",
    "details": {
        "paymentUsed": {"network": "base", "asset": "USDC", "amount": "0.05"},
        # paymentProof is decoded from the payment-response/x-payment-response
        # header the facilitator returns — the provider's own account of
        # settlement, per x402ActionProvider.ts:retryWithX402. Synthetic here.
        "paymentProof": {
            "success": True,
            "transaction": "0x" + "22" * 32,  # synthetic — not a real settled tx
            "network": "base",
            "payer": "0x" + "33" * 20,
        },
    },
}
result_digest = sha256_hex(jcs(result))

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "provider": "X402ActionProvider (coinbase/agentkit)",
    "action_name": "retry_http_request_with_x402",
    "request_digest": request_digest,
    "result_digest": result_digest,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "coinbase-x402-retry-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "request": request,
    "result": result,
    "related_work": (
        "coinbase/agentkit#1170 (giskard09, opened 2026-05-07, still open) adds "
        "a read-only MyceliumTrails action provider to AgentKit itself "
        "(verify_trail/compute_action_ref/get_trails) for verifying agent "
        "trails generically. This worked example is a separate, narrower "
        "piece: a standalone, independently-reproducible anchor of one "
        "specific action (X402ActionProvider.retryWithX402's payment dispatch) "
        "— same pattern as the Binance/OKX/Kraken worked examples published "
        "the same day, not a duplicate of #1170."
    ),
    "provenance": (
        "Synthetic worked example. Tool-call shape modeled on coinbase/agentkit's "
        "own public source "
        "(typescript/agentkit/src/action-providers/x402/x402ActionProvider.ts, "
        "retryWithX402 / retry_http_request_with_x402 action). NOT captured "
        "from a running AgentKit instance, a real wallet, or a real x402 "
        "payment. result.details.paymentProof.transaction is not a real "
        "transaction. No claim that AgentKit emits action_ref today, and no "
        "claim of integration, adoption, or endorsement by Coinbase."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")

print("=== coinbase-x402-action-ref-anchor : producer ===")
print(f"jcs_payload = {jcs_payload}")
print(f"action_ref  = {action_ref}")
print(f"anchor ref (bytes32) = 0x{action_ref}")
print(f"wrote {OUT_DIR}/manifest.json")
