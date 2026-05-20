# hiero-sdk-python Compatibility: 0.2.0 → 0.2.6

> HashA2A uses `hiero-sdk-python>=0.2.6`. The Hedera Agent Kit (`hedera-agent-kit`)
> pins `hiero-sdk-python==0.2.0`. This doc shows what changed and how we handle it.

## Why the Conflict

```
hasha2a           → hiero-sdk-python>=0.2.6  (latest, preferred)
hedera-agent-kit  → hiero-sdk-python==0.2.0  (pinned, stricter)
```

Installing both in the same environment causes a version conflict.

## Solution: Plugin Bridge

We run `hedera-agent-kit` in an **isolated virtual environment** at `src/plugins/.kit_venv/`.
Communication is via JSON-RPC over stdin/stdout.

```
HashA2A process (hiero 0.2.6)
    ↕ stdin/stdout JSON-RPC
Plugin venv (hiero 0.2.0 + hedera-agent-kit)
```

See: `src/plugins/hedera_kit_bridge.py`, `scripts/setup_kit_plugin.sh`

## API Changes 0.2.0 → 0.2.6

| 0.2.0 (old) | 0.2.6 (new) | Impact |
|---|---|---|
| `tx.execute_async(client)` | `tx.execute(client)` (sync) | Wrap in `asyncio.to_thread()` |
| `receipt = await tx.get_receipt_async(client)` | `receipt = tx.execute(client)` (returns receipt directly) | No separate receipt fetch |
| `.set_topic_memo("...")` | `.set_memo("...")` | Renamed method |
| `.set_amount_in_tinybars(n)` | `.set_hbar_amount(Hbar.from_tinybars(n))` | Deprecated, use Hbar helper |
| No `transaction_fee` default | Default is very high | Must set explicitly |
| `TopicMessageQuery.set_topic_id(TopicId)` | `TopicMessageQuery.set_topic_id(str(topic_id))` | Expects string, not object |
| `PrivateKey.fromString(der)` | `PrivateKey.from_string(der)` (snake_case) | Name normalized |
| `PrivateKey.fromString(raw_hex)` | `PrivateKey.from_string(raw_hex)` | Supports both DER + raw |
| `Hbar.from(n)` | `Hbar.from_tinybars(n)` | Explicit unit |

## Code Migration Examples

### Before (0.2.0)
```python
tx = TransferTransaction().add_hbar_transfer(from_id, Hbar.from(10))
tx.execute_async(client)
receipt = await tx.get_receipt_async(client)
```

### After (0.2.6)
```python
tx = TransferTransaction().add_hbar_transfer(from_id, Hbar.from_tinybars(10))
await asyncio.to_thread(tx.execute, client)  # execute() returns receipt directly
```

### Before (0.2.0)
```python
tx.set_topic_memo("my topic")
tx.set_amount_in_tinybars(1000)
```

### After (0.2.6)
```python
tx.set_memo("my topic")
tx.set_hbar_amount(Hbar.from_tinybars(1000))
```

### Before (0.2.0)
```python
query = TopicMessageQuery().set_topic_id(topic_id)
```

### After (0.2.6)
```python
query = TopicMessageQuery().set_topic_id(str(topic_id))
```

## Running the Plugin

```bash
# One-time setup (creates isolated venv)
bash scripts/setup_kit_plugin.sh

# Then in MCP, call:
# → kit_setup()     — starts the plugin
# → kit_account_balance("0.0.12345") — use hedera-agent-kit
```
