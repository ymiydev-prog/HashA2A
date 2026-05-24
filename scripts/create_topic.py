"""Create an HCS topic on Hedera mainnet."""
import asyncio
import sys
sys.path.insert(0, "src")

from core.config import Settings
from core.hedera_manager import HederaManager


async def main():
    settings = Settings()
    hm = HederaManager(settings)

    memo = sys.argv[1] if len(sys.argv) > 1 else "HashA2A Test Topic"
    with_fees = "--fees" in sys.argv

    if with_fees:
        fee_hbar = float(sys.argv[sys.argv.index("--fees") + 1]) if "--fees" in sys.argv and len(sys.argv) > sys.argv.index("--fees") + 1 else 1.0
        topic_id = await hm.create_topic_with_fees(memo, fee_hbar)
        print(f"Topic with fees ({fee_hbar} HBAR): {topic_id}")
    else:
        topic_id = await hm.create_topic(memo)
        print(f"Topic: {topic_id}")

    hm.close()


if __name__ == "__main__":
    asyncio.run(main())
