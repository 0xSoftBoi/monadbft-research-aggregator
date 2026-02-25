#!/usr/bin/env python3
"""
Basic Usage Examples for MonadBFT Research Aggregator
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Example 1: Simple Consensus Simulation
async def example_basic_consensus():
    """Run a basic consensus simulation."""
    print("\n=== Example 1: Basic Consensus ===")
    
    from implementations.bft_consensus_sim import MonadBFTSimulator
    
    # Create simulator with 4 validators
    sim = MonadBFTSimulator(
        num_validators=4,
        byzantine_count=0,  # All honest
        network_delay_ms=50.0
    )
    
    # Propose and commit a block
    block = sim.propose_block("My first block")
    result = await sim.run_consensus(block)
    
    print(f"Status: {result.status}")
    print(f"Latency: {result.latency_ms:.2f}ms")
    print(f"Rounds: {result.rounds}")


# Example 2: Byzantine Fault Tolerance
async def example_byzantine_tolerance():
    """Test consensus with Byzantine validators."""
    print("\n=== Example 2: Byzantine Fault Tolerance ===")
    
    from implementations.bft_consensus_sim import MonadBFTSimulator
    
    # 10 validators, 3 Byzantine (maximum tolerable)
    sim = MonadBFTSimulator(
        num_validators=10,
        byzantine_count=3,
        network_delay_ms=40.0
    )
    
    successes = 0
    for i in range(10):
        block = sim.propose_block(f"Block {i}")
        result = await sim.run_consensus(block)
        if result.status == "committed":
            successes += 1
    
    print(f"Committed: {successes}/10 blocks")
    print(f"Success rate: {successes/10*100:.1f}%")


# Example 3: Tail-Forking Prevention
async def example_fork_prevention():
    """Demonstrate tail-forking prevention."""
    print("\n=== Example 3: Tail-Forking Prevention ===")
    
    from implementations.tail_fork_prevention import TailForkDemo
    
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    result = demo.simulate_byzantine_leader_attack()
    
    print(f"Fork prevented: {result['fork_prevented']}")
    print(f"Block A votes: {result['block_a_votes']}")
    print(f"Block B votes: {result['block_b_votes']}")


# Example 4: Speculative Finality
async def example_speculative_finality():
    """Test speculative finality under different conditions."""
    print("\n=== Example 4: Speculative Finality ===")
    
    from implementations.speculative_finality import SpeculativeFinalityEngine, FinalityMode
    
    engine = SpeculativeFinalityEngine(num_validators=10, byzantine_count=1)
    engine._init_genesis()
    
    # Good network conditions
    engine.network.set_quality(0.95)
    
    speculative_count = 0
    for i in range(10):
        record = await engine.propose_and_commit(f"Block {i}")
        if record and record.mode == FinalityMode.SPECULATIVE:
            speculative_count += 1
    
    print(f"Speculative commits: {speculative_count}/10")
    print(f"Percentage: {speculative_count/10*100:.1f}%")


# Example 5: Performance Measurement
async def example_performance_measurement():
    """Measure consensus performance."""
    print("\n=== Example 5: Performance Measurement ===")
    
    from benchmarks.consensus_benchmark import ThroughputTest
    
    test = ThroughputTest()
    results = await test.measure_tps(
        duration=3,
        validator_count=7,
        concurrent_proposals=False
    )
    
    print(f"Duration: {results['duration_s']:.1f}s")
    print(f"Blocks committed: {results['blocks_committed']}")
    print(f"Average TPS: {results['avg_tps']:.2f}")
    print(f"Average latency: {results['avg_latency']:.2f}ms")


# Example 6: Fork Resistance
async def example_fork_resistance():
    """Test fork resistance."""
    print("\n=== Example 6: Fork Resistance ===")
    
    from benchmarks.fork_resistance import ForkResistanceTest
    
    test = ForkResistanceTest()
    results = await test.run_attack_scenarios(["double_spend", "nothing_at_stake"])
    
    for attack_type, result in results.items():
        status = "VULNERABLE" if result.attack_successful else "RESISTANT"
        print(f"{attack_type}: {status}")


# Example 7: Code Analysis
def example_code_analysis():
    """Analyze code for consensus properties."""
    print("\n=== Example 7: Code Analysis ===")
    
    from analysis.code_analyzer import MonadBFTAnalyzer
    
    analyzer = MonadBFTAnalyzer()
    result = analyzer.analyze_repository(".")
    
    if result:
        print(f"Files analyzed: {result.files_analyzed}")
        print(f"Total lines: {result.total_lines}")
        print(f"Consensus components: {len(result.consensus_components)}")
        print(f"Safety properties: {len(result.safety_properties)}")
        print(f"Performance score: {result.performance_score}/100")


# Example 8: Generate Documentation
def example_generate_docs():
    """Generate documentation."""
    print("\n=== Example 8: Generate Documentation ===")
    
    from documentation.doc_generator import DocumentationGenerator
    
    gen = DocumentationGenerator()
    
    # Generate research summary
    gen.generate_research_summary(
        sources=["arxiv:2502.20692"],
        output="examples/sample_summary.md"
    )
    
    print("Documentation generated: examples/sample_summary.md")


async def main():
    """Run all examples."""
    print("\nMonadBFT Research Aggregator - Usage Examples\n")
    print("="*50)
    
    # Run async examples
    await example_basic_consensus()
    await example_byzantine_tolerance()
    await example_fork_prevention()
    await example_speculative_finality()
    await example_performance_measurement()
    await example_fork_resistance()
    
    # Run sync examples
    example_code_analysis()
    example_generate_docs()
    
    print("\n" + "="*50)
    print("\nAll examples completed!\n")


if __name__ == "__main__":
    asyncio.run(main())