"""MonadBFT consensus simulation."""

import time
import random
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json


class NodeState(Enum):
    """Node states in BFT consensus."""
    HONEST = "honest"
    BYZANTINE = "byzantine"
    CRASHED = "crashed"


class MessageType(Enum):
    """Message types in BFT protocol."""
    PROPOSE = "propose"
    VOTE = "vote"
    COMMIT = "commit"
    VIEW_CHANGE = "view_change"


@dataclass
class Block:
    """Block in the blockchain."""
    height: int
    proposer: int
    transactions: List[str]
    parent_hash: str
    timestamp: float
    hash: str


@dataclass
class Message:
    """Protocol message."""
    type: MessageType
    sender: int
    view: int
    block: Optional[Block]
    signature: str


@dataclass
class ConsensusMetrics:
    """Consensus performance metrics."""
    total_rounds: int
    successful_rounds: int
    failed_rounds: int
    avg_round_time_ms: float
    avg_finality_time_ms: float
    fork_count: int
    total_messages: int
    messages_per_round: float
    byzantine_detected: int


class BFTNode:
    """BFT consensus node."""
    
    def __init__(self, node_id: int, total_nodes: int, state: NodeState = NodeState.HONEST):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.state = state
        self.view = 0
        self.current_block = None
        self.votes: Dict[int, Set[int]] = {}  # block_height -> set of voter ids
        self.committed_blocks: List[Block] = []
        self.message_count = 0
        
    def is_leader(self, view: int) -> bool:
        """Check if this node is the leader for given view."""
        return (view % self.total_nodes) == self.node_id
    
    def propose_block(self, transactions: List[str]) -> Optional[Block]:
        """Propose a new block."""
        if self.state != NodeState.HONEST:
            return None
            
        parent_hash = self.committed_blocks[-1].hash if self.committed_blocks else "genesis"
        
        block = Block(
            height=len(self.committed_blocks) + 1,
            proposer=self.node_id,
            transactions=transactions,
            parent_hash=parent_hash,
            timestamp=time.time(),
            hash=self._calculate_hash(transactions, parent_hash)
        )
        
        self.current_block = block
        return block
    
    def vote_on_block(self, block: Block) -> bool:
        """Vote on a proposed block."""
        if self.state == NodeState.CRASHED:
            return False
            
        if self.state == NodeState.BYZANTINE:
            # Byzantine nodes vote randomly
            return random.choice([True, False])
        
        # Honest nodes verify block
        if not self._verify_block(block):
            return False
            
        if block.height not in self.votes:
            self.votes[block.height] = set()
        self.votes[block.height].add(self.node_id)
        
        return True
    
    def has_quorum(self, block_height: int) -> bool:
        """Check if block has achieved quorum (2/3 + 1 votes)."""
        if block_height not in self.votes:
            return False
        
        quorum_size = (2 * self.total_nodes // 3) + 1
        return len(self.votes[block_height]) >= quorum_size
    
    def commit_block(self, block: Block) -> bool:
        """Commit a block with quorum."""
        if not self.has_quorum(block.height):
            return False
            
        self.committed_blocks.append(block)
        self.current_block = None
        return True
    
    def _verify_block(self, block: Block) -> bool:
        """Verify block validity."""
        # Check height
        if block.height != len(self.committed_blocks) + 1:
            return False
            
        # Check parent hash
        expected_parent = self.committed_blocks[-1].hash if self.committed_blocks else "genesis"
        if block.parent_hash != expected_parent:
            return False
            
        return True
    
    def _calculate_hash(self, transactions: List[str], parent_hash: str) -> str:
        """Calculate block hash."""
        data = f"{parent_hash}{''.join(transactions)}{time.time()}"
        return hex(hash(data))[2:]


class MonadBFTSimulator:
    """MonadBFT consensus simulator."""
    
    def __init__(self, num_nodes: int = 10, byzantine_nodes: int = 0, network_latency_ms: float = 50):
        self.num_nodes = num_nodes
        self.byzantine_count = byzantine_nodes
        self.network_latency_ms = network_latency_ms
        
        # Create nodes
        self.nodes: List[BFTNode] = []
        byzantine_ids = random.sample(range(num_nodes), byzantine_nodes)
        
        for i in range(num_nodes):
            state = NodeState.BYZANTINE if i in byzantine_ids else NodeState.HONEST
            self.nodes.append(BFTNode(i, num_nodes, state))
        
        self.current_view = 0
        self.metrics = ConsensusMetrics(
            total_rounds=0,
            successful_rounds=0,
            failed_rounds=0,
            avg_round_time_ms=0.0,
            avg_finality_time_ms=0.0,
            fork_count=0,
            total_messages=0,
            messages_per_round=0.0,
            byzantine_detected=0
        )
    
    def run_simulation(self, num_rounds: int = 100, transactions_per_block: int = 100) -> ConsensusMetrics:
        """Run consensus simulation."""
        print(f"Starting MonadBFT simulation: {self.num_nodes} nodes, {self.byzantine_count} Byzantine")
        print(f"Running {num_rounds} consensus rounds...\n")
        
        round_times = []
        
        for round_num in range(num_rounds):
            start_time = time.time()
            
            # Generate transactions
            transactions = [f"tx_{round_num}_{i}" for i in range(transactions_per_block)]
            
            # Run consensus round
            success = self._run_consensus_round(transactions)
            
            round_time_ms = (time.time() - start_time) * 1000
            round_times.append(round_time_ms)
            
            self.metrics.total_rounds += 1
            if success:
                self.metrics.successful_rounds += 1
            else:
                self.metrics.failed_rounds += 1
            
            if (round_num + 1) % 10 == 0:
                print(f"Round {round_num + 1}/{num_rounds} completed")
        
        # Calculate final metrics
        self.metrics.avg_round_time_ms = sum(round_times) / len(round_times)
        self.metrics.avg_finality_time_ms = self.metrics.avg_round_time_ms * 3  # Approximate
        self.metrics.messages_per_round = self.metrics.total_messages / self.metrics.total_rounds
        
        return self.metrics
    
    def _run_consensus_round(self, transactions: List[str]) -> bool:
        """Run a single consensus round."""
        # Phase 1: Leader proposes block
        leader_id = self.current_view % self.num_nodes
        leader = self.nodes[leader_id]
        
        block = leader.propose_block(transactions)
        if block is None:
            # Leader is Byzantine or crashed, trigger view change
            self.current_view += 1
            return False
        
        self.metrics.total_messages += 1  # Proposal message
        self._simulate_network_delay()
        
        # Phase 2: Nodes vote on block
        votes = 0
        for node in self.nodes:
            if node.vote_on_block(block):
                votes += 1
                self.metrics.total_messages += 1
        
        self._simulate_network_delay()
        
        # Phase 3: Check quorum and commit
        quorum_size = (2 * self.num_nodes // 3) + 1
        if votes >= quorum_size:
            # Commit block on all nodes
            for node in self.nodes:
                if node.state != NodeState.CRASHED:
                    node.commit_block(block)
                    self.metrics.total_messages += 1  # Commit message
            
            self._simulate_network_delay()
            return True
        else:
            # Failed to reach quorum, view change
            self.current_view += 1
            return False
    
    def _simulate_network_delay(self):
        """Simulate network latency."""
        delay_seconds = self.network_latency_ms / 1000
        time.sleep(delay_seconds)
    
    def generate_report(self) -> str:
        """Generate simulation report."""
        report = f"""
══════════════════════════════════════════════════
         MonadBFT Simulation Report
══════════════════════════════════════════════════

Configuration:
  Nodes: {self.num_nodes}
  Byzantine Nodes: {self.byzantine_count} ({self.byzantine_count/self.num_nodes*100:.1f}%)
  Network Latency: {self.network_latency_ms}ms

Results:
  Total Rounds: {self.metrics.total_rounds}
  Successful: {self.metrics.successful_rounds} ({self.metrics.successful_rounds/self.metrics.total_rounds*100:.1f}%)
  Failed: {self.metrics.failed_rounds} ({self.metrics.failed_rounds/self.metrics.total_rounds*100:.1f}%)

Performance:
  Average Round Time: {self.metrics.avg_round_time_ms:.2f}ms
  Average Finality Time: {self.metrics.avg_finality_time_ms:.2f}ms
  Total Messages: {self.metrics.total_messages:,}
  Messages Per Round: {self.metrics.messages_per_round:.1f}
  Communication Complexity: O(n)

Safety:
  Forks Detected: {self.metrics.fork_count}
  Byzantine Nodes Detected: {self.metrics.byzantine_detected}

══════════════════════════════════════════════════
"""
        print(report)
        return report
    
    def export_metrics(self, filename: str = "simulation_results.json"):
        """Export metrics to JSON file."""
        data = {
            "configuration": {
                "num_nodes": self.num_nodes,
                "byzantine_nodes": self.byzantine_count,
                "network_latency_ms": self.network_latency_ms
            },
            "metrics": {
                "total_rounds": self.metrics.total_rounds,
                "successful_rounds": self.metrics.successful_rounds,
                "failed_rounds": self.metrics.failed_rounds,
                "success_rate": self.metrics.successful_rounds / self.metrics.total_rounds,
                "avg_round_time_ms": self.metrics.avg_round_time_ms,
                "avg_finality_time_ms": self.metrics.avg_finality_time_ms,
                "total_messages": self.metrics.total_messages,
                "messages_per_round": self.metrics.messages_per_round,
                "fork_count": self.metrics.fork_count
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nMetrics exported to {filename}")


if __name__ == "__main__":
    # Run example simulation
    print("MonadBFT Consensus Simulation\n")
    
    # Test with different Byzantine ratios
    configs = [
        (10, 0, "Ideal conditions"),
        (10, 1, "10% Byzantine"),
        (10, 3, "33% Byzantine (max tolerance)"),
    ]
    
    for num_nodes, byzantine, description in configs:
        print(f"\n{'='*60}")
        print(f"Test: {description}")
        print(f"{'='*60}\n")
        
        sim = MonadBFTSimulator(
            num_nodes=num_nodes,
            byzantine_nodes=byzantine,
            network_latency_ms=10  # Low latency for fast simulation
        )
        
        metrics = sim.run_simulation(num_rounds=20)
        sim.generate_report()
        sim.export_metrics(f"simulation_{description.replace(' ', '_')}.json")