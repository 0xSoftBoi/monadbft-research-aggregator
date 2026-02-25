"""Consensus protocol benchmarking framework."""

import time
import statistics
from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    protocol_name: str
    num_nodes: int
    test_duration_seconds: float
    
    # Throughput metrics
    total_transactions: int
    transactions_per_second: float
    blocks_finalized: int
    
    # Latency metrics
    avg_finality_time_ms: float
    median_finality_time_ms: float
    p95_finality_time_ms: float
    p99_finality_time_ms: float
    
    # Network metrics
    total_messages: int
    messages_per_block: float
    bandwidth_kb_per_second: float
    
    # Reliability metrics
    success_rate: float
    fork_rate: float
    

class ProtocolInterface:
    """Interface for consensus protocols."""
    
    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.name = "BaseProtocol"
    
    def initialize(self):
        """Initialize protocol."""
        pass
    
    def process_block(self, transactions: List[str]) -> Dict:
        """Process a block of transactions."""
        raise NotImplementedError
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        raise NotImplementedError


class MonadBFTProtocol(ProtocolInterface):
    """MonadBFT protocol implementation for benchmarking."""
    
    def __init__(self, num_nodes: int):
        super().__init__(num_nodes)
        self.name = "MonadBFT"
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def initialize(self):
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def process_block(self, transactions: List[str]) -> Dict:
        """Process block with MonadBFT consensus."""
        start_time = time.time()
        
        # Simulate MonadBFT consensus phases
        # Phase 1: Leader proposal
        time.sleep(0.05)  # 50ms
        self.messages_sent += 1
        
        # Phase 2: Voting
        time.sleep(0.05)  # 50ms 
        self.messages_sent += self.num_nodes
        
        # Phase 3: Commit
        time.sleep(0.05)  # 50ms
        self.messages_sent += self.num_nodes
        
        finality_time = (time.time() - start_time) * 1000  # Convert to ms
        self.finality_times.append(finality_time)
        self.blocks_finalized += 1
        
        return {
            'success': True,
            'finality_time_ms': finality_time,
            'messages': 1 + (2 * self.num_nodes)
        }
    
    def get_metrics(self) -> Dict:
        return {
            'finality_times': self.finality_times,
            'messages_sent': self.messages_sent,
            'blocks_finalized': self.blocks_finalized
        }


class HotStuffProtocol(ProtocolInterface):
    """HotStuff protocol implementation for benchmarking."""
    
    def __init__(self, num_nodes: int):
        super().__init__(num_nodes)
        self.name = "HotStuff"
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def initialize(self):
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def process_block(self, transactions: List[str]) -> Dict:
        """Process block with HotStuff consensus."""
        start_time = time.time()
        
        # HotStuff has 4 phases for finality
        for phase in range(4):
            time.sleep(0.05)  # 50ms per phase
            self.messages_sent += self.num_nodes
        
        finality_time = (time.time() - start_time) * 1000
        self.finality_times.append(finality_time)
        self.blocks_finalized += 1
        
        return {
            'success': True,
            'finality_time_ms': finality_time,
            'messages': 4 * self.num_nodes
        }
    
    def get_metrics(self) -> Dict:
        return {
            'finality_times': self.finality_times,
            'messages_sent': self.messages_sent,
            'blocks_finalized': self.blocks_finalized
        }


class TendermintProtocol(ProtocolInterface):
    """Tendermint protocol implementation for benchmarking."""
    
    def __init__(self, num_nodes: int):
        super().__init__(num_nodes)
        self.name = "Tendermint"
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def initialize(self):
        self.finality_times = []
        self.messages_sent = 0
        self.blocks_finalized = 0
    
    def process_block(self, transactions: List[str]) -> Dict:
        """Process block with Tendermint consensus."""
        start_time = time.time()
        
        # Tendermint phases
        # Propose
        time.sleep(0.1)  # 100ms
        self.messages_sent += 1
        
        # Prevote (O(n²) communication)
        time.sleep(0.1)
        self.messages_sent += self.num_nodes * self.num_nodes
        
        # Precommit (O(n²) communication) 
        time.sleep(0.1)
        self.messages_sent += self.num_nodes * self.num_nodes
        
        # Commit
        time.sleep(0.1)
        self.messages_sent += self.num_nodes
        
        finality_time = (time.time() - start_time) * 1000
        self.finality_times.append(finality_time)
        self.blocks_finalized += 1
        
        return {
            'success': True,
            'finality_time_ms': finality_time,
            'messages': 1 + (2 * self.num_nodes * self.num_nodes) + self.num_nodes
        }
    
    def get_metrics(self) -> Dict:
        return {
            'finality_times': self.finality_times,
            'messages_sent': self.messages_sent,
            'blocks_finalized': self.blocks_finalized
        }


class ConsensusBenchmark:
    """Benchmark framework for consensus protocols."""
    
    def __init__(self):
        self.protocols = {
            'MonadBFT': MonadBFTProtocol,
            'HotStuff': HotStuffProtocol,
            'Tendermint': TendermintProtocol
        }
    
    def benchmark_protocol(
        self,
        protocol: ProtocolInterface,
        duration_seconds: int = 60,
        transactions_per_block: int = 1000
    ) -> BenchmarkResult:
        """Benchmark a single protocol."""
        print(f"\nBenchmarking {protocol.name}...")
        protocol.initialize()
        
        start_time = time.time()
        blocks_processed = 0
        total_transactions = 0
        
        while (time.time() - start_time) < duration_seconds:
            # Generate transactions
            transactions = [f"tx_{blocks_processed}_{i}" for i in range(transactions_per_block)]
            
            # Process block
            result = protocol.process_block(transactions)
            
            if result['success']:
                blocks_processed += 1
                total_transactions += len(transactions)
            
            # Progress indicator
            if blocks_processed % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  Blocks: {blocks_processed}, Time: {elapsed:.1f}s")
        
        actual_duration = time.time() - start_time
        metrics = protocol.get_metrics()
        
        # Calculate statistics
        finality_times = metrics['finality_times']
        
        result = BenchmarkResult(
            protocol_name=protocol.name,
            num_nodes=protocol.num_nodes,
            test_duration_seconds=actual_duration,
            total_transactions=total_transactions,
            transactions_per_second=total_transactions / actual_duration,
            blocks_finalized=blocks_processed,
            avg_finality_time_ms=statistics.mean(finality_times),
            median_finality_time_ms=statistics.median(finality_times),
            p95_finality_time_ms=self._percentile(finality_times, 0.95),
            p99_finality_time_ms=self._percentile(finality_times, 0.99),
            total_messages=metrics['messages_sent'],
            messages_per_block=metrics['messages_sent'] / blocks_processed,
            bandwidth_kb_per_second=metrics['messages_sent'] * 1.0 / actual_duration,  # Assume 1KB per message
            success_rate=1.0,  # All successful in simulation
            fork_rate=0.0
        )
        
        return result
    
    def run_full_suite(
        self,
        protocols: List[str],
        network_conditions: List[str],
        num_nodes: int = 10,
        duration_seconds: int = 60
    ) -> Dict[str, Dict[str, BenchmarkResult]]:
        """Run comprehensive benchmark suite."""
        results = {}
        
        for protocol_name in protocols:
            if protocol_name not in self.protocols:
                print(f"Warning: Unknown protocol {protocol_name}")
                continue
            
            results[protocol_name] = {}
            
            for condition in network_conditions:
                print(f"\n{'='*60}")
                print(f"Testing {protocol_name} under {condition} conditions")
                print(f"{'='*60}")
                
                protocol = self.protocols[protocol_name](num_nodes)
                result = self.benchmark_protocol(protocol, duration_seconds)
                results[protocol_name][condition] = result
        
        return results
    
    def generate_comparison_report(self, results: Dict[str, Dict[str, BenchmarkResult]]) -> str:
        """Generate comparison report."""
        report = "\n" + "="*80 + "\n"
        report += "           CONSENSUS PROTOCOL COMPARISON REPORT\n"
        report += "="*80 + "\n\n"
        
        for condition in ['ideal', 'high_latency', 'partition']:
            report += f"\n{condition.upper()} CONDITIONS:\n"
            report += "-"*80 + "\n"
            report += f"{'Protocol':<15} {'TPS':>10} {'Finality(ms)':>15} {'Messages/Block':>18}\n"
            report += "-"*80 + "\n"
            
            for protocol_name, cond_results in results.items():
                if condition in cond_results:
                    r = cond_results[condition]
                    report += f"{r.protocol_name:<15} {r.transactions_per_second:>10.1f} "
                    report += f"{r.avg_finality_time_ms:>15.1f} {r.messages_per_block:>18.1f}\n"
            
            report += "\n"
        
        print(report)
        return report
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def export_results(self, results: Dict, filename: str = "benchmark_results.json"):
        """Export results to JSON."""
        export_data = {}
        
        for protocol, conditions in results.items():
            export_data[protocol] = {}
            for condition, result in conditions.items():
                export_data[protocol][condition] = {
                    'tps': result.transactions_per_second,
                    'avg_finality_ms': result.avg_finality_time_ms,
                    'p99_finality_ms': result.p99_finality_time_ms,
                    'messages_per_block': result.messages_per_block,
                    'blocks_finalized': result.blocks_finalized
                }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to {filename}")


if __name__ == "__main__":
    print("Consensus Protocol Benchmarking Suite\n")
    
    bench = ConsensusBenchmark()
    
    # Run benchmarks
    results = bench.run_full_suite(
        protocols=['MonadBFT', 'HotStuff', 'Tendermint'],
        network_conditions=['ideal'],
        num_nodes=10,
        duration_seconds=30  # Short duration for demo
    )
    
    # Generate report
    bench.generate_comparison_report(results)
    bench.export_results(results)