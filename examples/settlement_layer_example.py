#!/usr/bin/env python3
"""
Settlement Layer Example

Demonstrates using MonadBFT for blockchain settlement applications.
Relevant to cross-chain settlement-layer architecture.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from implementations.bft_consensus_sim import MonadBFTSimulator
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class Settlement:
    """Represents a cross-chain settlement."""
    id: str
    source_chain: str
    dest_chain: str
    amount: float
    timestamp: float
    finalized: bool = False
    finality_time: float = 0.0


class SettlementLayerSimulator:
    """Simulates a settlement layer using MonadBFT."""
    
    def __init__(
        self,
        validators: int = 10,
        finality_time_target: float = 1.0,  # seconds
        transaction_throughput_target: int = 10000  # TPS
    ):
        self.validators = validators
        self.finality_time_target = finality_time_target
        self.throughput_target = transaction_throughput_target
        
        # Initialize MonadBFT consensus
        self.consensus = MonadBFTSimulator(
            num_validators=validators,
            byzantine_count=(validators - 1) // 3,
            network_delay_ms=30.0
        )
        
        self.settlements: List[Settlement] = []
    
    async def settle_transaction(
        self,
        source: str,
        dest: str,
        amount: float
    ) -> Settlement:
        """Settle a cross-chain transaction."""
        start_time = time.time()
        
        settlement = Settlement(
            id=f"{source}-{dest}-{len(self.settlements)}",
            source_chain=source,
            dest_chain=dest,
            amount=amount,
            timestamp=start_time
        )
        
        # Create block with settlement data
        block = self.consensus.propose_block(
            f"Settlement: {settlement.id} ({amount} from {source} to {dest})"
        )
        
        # Run consensus
        result = await self.consensus.run_consensus(block)
        
        if result.status == "committed":
            settlement.finalized = True
            settlement.finality_time = result.latency_ms / 1000.0
            self.settlements.append(settlement)
        
        return settlement
    
    async def batch_settle(
        self,
        settlements: List[tuple]
    ) -> Dict:
        """Settle multiple transactions in batch."""
        start_time = time.time()
        results = []
        
        for source, dest, amount in settlements:
            settlement = await self.settle_transaction(source, dest, amount)
            results.append(settlement)
        
        total_time = time.time() - start_time
        finalized = sum(1 for s in results if s.finalized)
        
        return {
            "total_settlements": len(settlements),
            "finalized": finalized,
            "failed": len(settlements) - finalized,
            "total_time": total_time,
            "avg_finality_time": sum(s.finality_time for s in results if s.finalized) / max(finalized, 1),
            "throughput": finalized / total_time if total_time > 0 else 0
        }


async def demo_simple_settlement():
    """Demo: Simple cross-chain settlement."""
    console.print("\n[bold cyan]Demo 1: Simple Cross-Chain Settlement[/bold cyan]\n")
    
    layer = SettlementLayerSimulator(validators=7)
    
    # Settle a transaction from Ethereum to Bitcoin
    settlement = await layer.settle_transaction(
        source="ethereum",
        dest="bitcoin",
        amount=1.5
    )
    
    console.print(f"Settlement ID: {settlement.id}")
    console.print(f"Status: {'FINALIZED' if settlement.finalized else 'PENDING'}")
    console.print(f"Finality time: {settlement.finality_time*1000:.2f}ms")


async def demo_batch_settlement():
    """Demo: Batch settlement across multiple chains."""
    console.print("\n[bold cyan]Demo 2: Batch Cross-Chain Settlement[/bold cyan]\n")
    
    layer = SettlementLayerSimulator(validators=10)
    
    # Create batch of settlements
    batch = [
        ("ethereum", "bitcoin", 1.5),
        ("ethereum", "solana", 100.0),
        ("bitcoin", "ethereum", 0.5),
        ("solana", "ethereum", 250.0),
        ("polygon", "arbitrum", 1000.0),
    ]
    
    console.print(f"Settling {len(batch)} cross-chain transactions...\n")
    
    results = await layer.batch_settle(batch)
    
    table = Table(title="Batch Settlement Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Total settlements", str(results['total_settlements']))
    table.add_row("Finalized", str(results['finalized']))
    table.add_row("Failed", str(results['failed']))
    table.add_row("Total time", f"{results['total_time']:.2f}s")
    table.add_row("Avg finality time", f"{results['avg_finality_time']*1000:.2f}ms")
    table.add_row("Throughput", f"{results['throughput']:.2f} settlements/s")
    
    console.print(table)


async def demo_high_volume_settlement():
    """Demo: High-volume settlement testing."""
    console.print("\n[bold cyan]Demo 3: High-Volume Settlement Testing[/bold cyan]\n")
    
    layer = SettlementLayerSimulator(validators=25)
    
    # Simulate high volume
    chains = ["ethereum", "bitcoin", "solana", "polygon", "arbitrum", "optimism"]
    batch = []
    
    for i in range(100):
        import random
        source = random.choice(chains)
        dest = random.choice([c for c in chains if c != source])
        amount = random.uniform(0.1, 100.0)
        batch.append((source, dest, amount))
    
    console.print(f"Testing {len(batch)} settlements...")
    
    results = await layer.batch_settle(batch)
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Finalized: {results['finalized']}/{results['total_settlements']}")
    console.print(f"  Success rate: {results['finalized']/results['total_settlements']*100:.1f}%")
    console.print(f"  Total time: {results['total_time']:.2f}s")
    console.print(f"  Throughput: {results['throughput']:.2f} settlements/s")
    console.print(f"  Avg finality: {results['avg_finality_time']*1000:.2f}ms")


async def demo_settlement_analytics():
    """Demo: Settlement analytics and reporting."""
    console.print("\n[bold cyan]Demo 4: Settlement Analytics[/bold cyan]\n")
    
    layer = SettlementLayerSimulator(validators=10)
    
    # Settle various transactions
    chains = ["ethereum", "bitcoin", "solana"]
    for i in range(30):
        import random
        source = random.choice(chains)
        dest = random.choice([c for c in chains if c != source])
        amount = random.uniform(0.1, 10.0)
        await layer.settle_transaction(source, dest, amount)
    
    # Analyze settlements
    finalized = [s for s in layer.settlements if s.finalized]
    
    # By chain
    by_chain = {}
    for s in finalized:
        key = f"{s.source_chain}->{s.dest_chain}"
        if key not in by_chain:
            by_chain[key] = {"count": 0, "volume": 0.0}
        by_chain[key]["count"] += 1
        by_chain[key]["volume"] += s.amount
    
    # Print analytics
    table = Table(title="Settlement Analytics")
    table.add_column("Route", style="cyan")
    table.add_column("Count", style="yellow")
    table.add_column("Volume", style="green")
    
    for route, data in sorted(by_chain.items(), key=lambda x: x[1]["count"], reverse=True):
        table.add_row(route, str(data["count"]), f"{data['volume']:.2f}")
    
    console.print(table)
    
    # Performance metrics
    avg_finality = sum(s.finality_time for s in finalized) / len(finalized)
    console.print(f"\n[bold]Performance Metrics:[/bold]")
    console.print(f"  Total settlements: {len(finalized)}")
    console.print(f"  Average finality time: {avg_finality*1000:.2f}ms")
    console.print(f"  Total volume settled: {sum(s.amount for s in finalized):.2f}")


async def main():
    """Run all settlement layer demos."""
    console.clear()
    
    console.print("\n[bold white]Settlement Layer with MonadBFT[/bold white]")
    console.print("[cyan]Blockchain Settlement Architecture Demo[/cyan]\n")
    
    await demo_simple_settlement()
    await demo_batch_settlement()
    await demo_high_volume_settlement()
    await demo_settlement_analytics()
    
    console.print("\n[bold green]Settlement demos complete![/bold green]")
    console.print("\n[bold]Key Takeaways:[/bold]")
    console.print("• MonadBFT provides fast finality for settlements (< 1s)")
    console.print("• High throughput supports large settlement volumes")
    console.print("• Byzantine fault tolerance ensures security")
    console.print("• Suitable for cross-chain settlement layers\n")


if __name__ == "__main__":
    asyncio.run(main())