#!/usr/bin/env python3
"""
Quick Start Script for MonadBFT Research Aggregator

Runs a demo of all major features:
1. Research aggregation
2. Consensus simulation
3. Tail-forking prevention demo
4. Speculative finality demo
5. Performance benchmarks
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from loguru import logger

console = Console()


async def run_consensus_demo():
    """Run basic consensus simulation."""
    console.print(Panel.fit(
        "[bold cyan]1. BFT Consensus Simulation[/bold cyan]\n"
        "Simulating MonadBFT consensus with 7 validators...",
        border_style="cyan"
    ))
    
    from implementations.bft_consensus_sim import MonadBFTSimulator
    
    sim = MonadBFTSimulator(
        num_validators=7,
        byzantine_count=2,
        network_delay_ms=30.0
    )
    
    # Simulate 5 blocks
    for i in range(5):
        block = sim.propose_block(f"Transaction batch {i}")
        result = await sim.run_consensus(block)
        console.print(f"Block {i}: {result.status} ({result.latency_ms:.1f}ms)")
        await asyncio.sleep(0.1)
    
    sim.print_statistics()
    console.print("")


async def run_tail_fork_demo():
    """Run tail-forking prevention demo."""
    console.print(Panel.fit(
        "[bold red]2. Tail-Forking Prevention Demo[/bold red]\n"
        "Demonstrating Byzantine leader attack prevention...",
        border_style="red"
    ))
    
    from implementations.tail_fork_prevention import TailForkDemo
    
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    
    # Scenario 1: Honest
    result1 = demo.simulate_honest_scenario()
    await asyncio.sleep(0.5)
    
    # Scenario 2: Byzantine attack
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    result2 = demo.simulate_byzantine_leader_attack()
    
    console.print(
        f"\n[bold green]Fork Prevention: {'SUCCESS' if result2['fork_prevented'] else 'FAILED'}[/bold green]\n"
    )


async def run_speculative_finality_demo():
    """Run speculative finality demo."""
    console.print(Panel.fit(
        "[bold yellow]3. Speculative Finality Demo[/bold yellow]\n"
        "Testing adaptive 1-round vs 2-round commits...",
        border_style="yellow"
    ))
    
    from implementations.speculative_finality import SpeculativeFinalityEngine
    
    engine = SpeculativeFinalityEngine(num_validators=10, byzantine_count=1)
    engine._init_genesis()
    
    # Test under good network conditions
    engine.network.set_quality(0.9)
    
    for i in range(10):
        await engine.propose_and_commit(f"Block {i}")
        await asyncio.sleep(0.05)
    
    engine.print_statistics()
    console.print("")


async def run_mini_benchmark():
    """Run mini performance benchmark."""
    console.print(Panel.fit(
        "[bold magenta]4. Performance Benchmark[/bold magenta]\n"
        "Running quick performance test...",
        border_style="magenta"
    ))
    
    from benchmarks.consensus_benchmark import ThroughputTest
    
    test = ThroughputTest()
    results = await test.measure_tps(duration=5, validator_count=7)
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Average TPS: {results['avg_tps']:.2f}")
    console.print(f"  Average Latency: {results['avg_latency']:.2f}ms")
    console.print(f"  P99 Latency: {results['p99_latency']:.2f}ms\n")


async def run_fork_resistance_test():
    """Run fork resistance test."""
    console.print(Panel.fit(
        "[bold blue]5. Fork Resistance Testing[/bold blue]\n"
        "Testing resistance to various attacks...",
        border_style="blue"
    ))
    
    from benchmarks.fork_resistance import ForkResistanceTest
    
    test = ForkResistanceTest()
    await test.run_attack_scenarios([
        "double_spend",
        "nothing_at_stake"
    ])
    console.print("")


async def main():
    """Run all demos."""
    console.clear()
    
    console.print(Panel.fit(
        "[bold white]MonadBFT Research Aggregator[/bold white]\n"
        "[cyan]Quick Start Demo[/cyan]\n\n"
        "This demo showcases:",
        border_style="white"
    ))
    
    console.print("• BFT Consensus Simulation")
    console.print("• Tail-Forking Prevention")
    console.print("• Speculative Finality")
    console.print("• Performance Benchmarking")
    console.print("• Fork Resistance Testing")
    console.print("")
    
    try:
        await run_consensus_demo()
        await run_tail_fork_demo()
        await run_speculative_finality_demo()
        await run_mini_benchmark()
        await run_fork_resistance_test()
        
        console.print(Panel.fit(
            "[bold green]✓ Quick Start Complete![/bold green]\n\n"
            "Next steps:\n"
            "  1. Explore individual demos in src/implementations/\n"
            "  2. Run full benchmarks: python src/benchmarks/consensus_benchmark.py\n"
            "  3. Generate documentation: python src/documentation/doc_generator.py\n"
            "  4. Analyze code: python src/analysis/code_analyzer.py\n",
            border_style="green"
        ))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Demo error")


if __name__ == "__main__":
    asyncio.run(main())