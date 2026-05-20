# HIP-1261 Simple Fees — Transaction Fee Maximum

> `tx.transaction_fee` is a **MAX cap**, not the actual charge.
> Setting it too high wastes HBAR; setting it too low causes `INSUFFICIENT_TX_FEE`.

## The Problem

Many developers set `transaction_fee` thinking it's the exact cost:

```python
tx.transaction_fee = 5_000_000_000  # 5 HBAR  ← WRONG: this is just a max cap
```

The actual cost is much lower. You're capping how much the network can charge, not paying that amount.

## Recommended Values (HIP-1261)

| Operation | `transaction_fee` (tinybar) | Actual cost | Network fee |
|---|---|---|---|
| TopicCreate (basic) | `50_000_000` (0.05 HBAR) | ~0.01 HBAR | ~$0.0001 |
| TopicCreate (HIP-991) | `100_000_000` (0.1 HBAR) | ~0.01 HBAR | ~$0.0001 |
| TopicMessageSubmit (basic) | `50_000_000` (0.05 HBAR) | ~0.0001 HBAR | ~$0.0001 |
| TopicMessageSubmit (HIP-991 custom fee) | `50_000_000` (0.05 HBAR) | ~0.05 HBAR | ~$0.05 |
| TransferTransaction | `50_000_000` (0.05 HBAR) | ~0.0001 HBAR | ~$0.0001 |

## Before vs After (hasha2a)

| Version | TopicCreate | TopicCreate + HIP-991 | Result |
|---|---|---|---|
| Before (v0.1.x) | `5_000_000_000` (5 HBAR) | `10_000_000_000` (10 HBAR) | Overpaying |
| After (v0.2.x, HIP-1261) | `50_000_000` (0.05 HBAR) | `100_000_000` (0.1 HBAR) | Optimal |

## Implementation

In `src/core/hedera_manager.py`:

```python
# Line 108 — basic topic
tx.transaction_fee = 50_000_000  # 0.05 HBAR max (HIP-1261 Simple Fees)

# Line 137 — HIP-991 topic (custom fee schedule)
tx.transaction_fee = 100_000_000  # 0.1 HBAR max for HIP-991 (HIP-1261 Simple Fees)
```

## How to Verify

Run the fee estimation endpoint:

```bash
curl -s http://localhost:8080/api/v1/network/fees | jq .
```

Or use `HederaManager.estimate_fee()` in `src/core/hedera_manager.py:255`:

```python
estimated = await hedera.estimate_fee(tx)
print(f"Estimated fee: {estimated} tinybar")
```

## When to Raise the Cap

Increase `transaction_fee` only if:

1. The transaction includes many custom fees (HIP-991 schedule with >5 fees)
2. The transaction is large (>10KB body bytes)
3. Network congestion requires higher fees (rare on Hedera)
