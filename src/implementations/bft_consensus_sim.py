#!/usr/bin/env python3
"""
MonadBFT Consensus Simulation

Simulates the MonadBFT consensus protocol based on Fast-HotStuff lineage.
Implements proposal, voting, commit phases, and view-change mechanism.

Key features:
- Streamlined communication (O(n) instead of O(n²))
- Tail-forking prevention through validator locking
- Speculative finality (1-2 round confirmation)
- Byzantine fault tolerance (f < n/3)
"""

import asyncio
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from loguru import logger


class Phase(Enum):
    """Consensus phases in MonadBFT."""
    PROPOSE = "propose"
    VOTE = "vote"
    COMMIT = "commit"
    VIEW_CHANGE = "view_change"


class ValidatorStatus(Enum):
    """Validator node status."""
    HONEST = "honest"
    BYZANTINE = "byzantine"
    OFFLINE = "offline"


@dataclass
class Block:
    """Block in the blockchain."""
    height: int
    data: str
    parent_hash: str
    proposer: int
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute block hash."""
        content = f"{self.height}{self.data}{self.parent_hash}{self.proposer}{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class Vote:
    """Vote message from validator."""
    block_hash: str
    voter_id: int
    view: int
    signature: bytes = b""


@dataclass
class QuorumCertificate:
    """Quorum certificate aggregating votes."""
    block_hash: str
    view: int
    votes: List[Vote]
    timestamp: float = field(default_factory=time.time)
    
    @property
    def vote_count(self) -> int:
        return len(self.votes)


@dataclass
class ConsensusResult:
    """Result of consensus execution."""
    status: str  # "committed", "timeout", "failed"
    block: Optional[Block]
    rounds: int
    latency_ms: float
    view_changes: int
    votes_collected: int


class Validator:
    """MonadBFT validator node."""
    
    def __init__(self, validator_id: int, status: ValidatorStatus = ValidatorStatus.HONEST):
        self.id = validator_id
        self.status = status
        self.locked_block: Optional[Block] = None
        self.locked_qc: Optional[QuorumCertificate] = None
        self.view = 0
        self.committed_blocks: List[Block] = []
        
        # Generate key pair for signing
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
    
    def sign_vote(self, block_hash: str) -> bytes:
        """Sign a vote for a block."""
        if self.status == ValidatorStatus.BYZANTINE:
            # Byzantine node might sign multiple conflicting votes
            return b"byzantine_signature"
        
        signature = self.private_key.sign(
            block_hash.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return signature
    
    def create_vote(self, block: Block, view: int) -> Vote:
        """Create a vote for a block."""
        signature = self.sign_vote(block.hash)
        return Vote(
            block_hash=block.hash,
            voter_id=self.id,
            view=view,
            signature=signature
        )
    
    def should_vote(self, block: Block) -> bool:
        """Determine if validator should vote for a block."""
        if self.status == ValidatorStatus.OFFLINE:
            return False
        
        if self.status == ValidatorStatus.BYZANTINE:
            # Byzantine nodes might vote randomly
            return random.random() > 0.3
        
        # Honest validator checks:
        # 1. Block extends from locked block or has higher QC
        # 2. Block is valid
        if self.locked_block and block.parent_hash != self.locked_block.hash:
            if self.locked_qc and self.locked_qc.view >= block.height - 1:
                return False
        
        return True
    
    def lock_on_block(self, block: Block, qc: QuorumCertificate):
        """Lock on a block after voting (tail-forking prevention)."""
        self.locked_block = block
        self.locked_qc = qc
        logger.debug(f"Validator {self.id} locked on block {block.hash}")
    
    def commit_block(self, block: Block):
        """Commit a block to the chain."""
        self.committed_blocks.append(block)
        logger.info(f"Validator {self.id} committed block {block.height}: {block.hash}")


class MonadBFTSimulator:
    """MonadBFT consensus simulator."""
    
    def __init__(
        self,
        num_validators: int = 4,
        byzantine_count: int = 0,
        network_delay_ms: float = 50.0,
        timeout_ms: float = 1000.0
    ):
        self.num_validators = num_validators
        self.byzantine_count = min(byzantine_count, (num_validators - 1) // 3)
        self.network_delay_ms = network_delay_ms
        self.timeout_ms = timeout_ms
        
        # Initialize validators
        self.validators: List[Validator] = []
        for i in range(num_validators):
            if i < byzantine_count:
                status = ValidatorStatus.BYZANTINE
            else:
                status = ValidatorStatus.HONEST
            self.validators.append(Validator(i, status))
        
        self.current_view = 0
        self.current_leader = 0
        self.blockchain: List[Block] = self._init_genesis()
        
        # Statistics
        self.stats = {
            "total_blocks": 0,
            "committed_blocks": 0,
            "failed_proposals": 0,
            "view_changes": 0,
            "total_latency_ms": 0.0,
            "total_rounds": 0
        }
    
    def _init_genesis(self) -> List[Block]:
        """Initialize genesis block."""
        genesis = Block(
            height=0,
            data="GENESIS",
            parent_hash="0" * 16,
            proposer=-1
        )
        return [genesis]
    
    @property
    def quorum_size(self) -> int:
        """Calculate quorum size (2f + 1)."""
        f = self.byzantine_count
        return 2 * f + 1
    
    def get_leader(self, view: int) -> int:
        """Determine leader for a given view (round-robin)."""
        return view % self.num_validators
    
    def propose_block(self, data: str) -> Block:
        """Leader proposes a new block."""
        leader_id = self.get_leader(self.current_view)
        parent = self.blockchain[-1]
        
        block = Block(
            height=len(self.blockchain),
            data=data,
            parent_hash=parent.hash,
            proposer=leader_id
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"VIEW {self.current_view}: Leader {leader_id} proposes block {block.height}")
        logger.info(f"Block hash: {block.hash}")
        logger.info(f"Data: {data}")
        logger.info(f"{'='*60}\n")
        
        return block
    
    async def simulate_network_delay(self):
        """Simulate network delay."""
        delay = random.gauss(self.network_delay_ms, self.network_delay_ms * 0.2) / 1000.0
        await asyncio.sleep(max(0, delay))
    
    async def voting_phase(self, block: Block) -> Optional[QuorumCertificate]:
        """Simulate voting phase."""
        logger.info(f"📊 VOTING PHASE for block {block.hash}")
        
        votes: List[Vote] = []
        
        # Validators vote
        for validator in self.validators:
            await self.simulate_network_delay()
            
            if validator.should_vote(block):
                vote = validator.create_vote(block, self.current_view)
                votes.append(vote)
                logger.debug(f"  ✓ Validator {validator.id} voted for block")
            else:
                logger.debug(f"  ✗ Validator {validator.id} did not vote")
        
        logger.info(f"Votes collected: {len(votes)}/{self.num_validators} (quorum: {self.quorum_size})")
        
        # Check if quorum reached
        if len(votes) >= self.quorum_size:
            qc = QuorumCertificate(
                block_hash=block.hash,
                view=self.current_view,
                votes=votes
            )
            logger.success(f"✓ Quorum reached! QC created with {len(votes)} votes")
            
            # Validators lock on this block (tail-forking prevention)
            for validator in self.validators:
                if any(v.voter_id == validator.id for v in votes):
                    validator.lock_on_block(block, qc)
            
            return qc
        else:
            logger.warning(f"✗ Quorum not reached ({len(votes)}/{self.quorum_size})")
            return None
    
    async def commit_phase(self, block: Block, qc: QuorumCertificate) -> bool:
        """Simulate commit phase."""
        logger.info(f"📝 COMMIT PHASE for block {block.hash}")
        
        # Leader broadcasts QC to all validators
        await self.simulate_network_delay()
        
        # Check for speculative finality (1-round commit)
        # This happens when previous block also had immediate quorum
        speculative = len(self.blockchain) > 1 and random.random() > 0.3
        
        if speculative:
            logger.info("⚡ SPECULATIVE FINALITY: 1-round commit")
            rounds = 1
        else:
            logger.info("🔄 Standard 2-round commit")
            rounds = 2
            
            # Simulate second round
            await self.simulate_network_delay()
        
        # All honest validators commit
        for validator in self.validators:
            if validator.status == ValidatorStatus.HONEST:
                validator.commit_block(block)
        
        self.blockchain.append(block)
        self.stats["committed_blocks"] += 1
        self.stats["total_rounds"] += rounds
        
        logger.success(f"✓ Block {block.height} committed to chain in {rounds} round(s)")
        return True
    
    async def view_change(self) -> bool:
        """Handle view change (leader rotation)."""
        old_leader = self.get_leader(self.current_view)
        self.current_view += 1
        new_leader = self.get_leader(self.current_view)
        
        logger.warning(f"\n🔄 VIEW CHANGE: {self.current_view - 1} → {self.current_view}")
        logger.warning(f"Leader rotation: {old_leader} → {new_leader}\n")
        
        self.stats["view_changes"] += 1
        
        # Simulate view change protocol
        await self.simulate_network_delay()
        
        return True
    
    async def run_consensus(self, block: Block) -> ConsensusResult:
        """Run full consensus protocol for a block."""
        start_time = time.time()
        view_changes = 0
        max_attempts = 3
        
        self.stats["total_blocks"] += 1
        
        for attempt in range(max_attempts):
            # Voting phase
            qc = await self.voting_phase(block)
            
            if qc:
                # Commit phase
                committed = await self.commit_phase(block, qc)
                
                if committed:
                    latency_ms = (time.time() - start_time) * 1000
                    self.stats["total_latency_ms"] += latency_ms
                    
                    return ConsensusResult(
                        status="committed",
                        block=block,
                        rounds=1 if latency_ms < 100 else 2,
                        latency_ms=latency_ms,
                        view_changes=view_changes,
                        votes_collected=qc.vote_count
                    )
            
            # Timeout, trigger view change
            logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed, triggering view change")
            await self.view_change()
            view_changes += 1
        
        # All attempts failed
        self.stats["failed_proposals"] += 1
        latency_ms = (time.time() - start_time) * 1000
        
        return ConsensusResult(
            status="failed",
            block=None,
            rounds=max_attempts,
            latency_ms=latency_ms,
            view_changes=view_changes,
            votes_collected=0
        )
    
    def print_statistics(self):
        """Print simulation statistics."""
        logger.info("\n" + "=" * 70)
        logger.info("SIMULATION STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total blocks proposed: {self.stats['total_blocks']}")
        logger.info(f"Successfully committed: {self.stats['committed_blocks']}")
        logger.info(f"Failed proposals: {self.stats['failed_proposals']}")
        logger.info(f"View changes: {self.stats['view_changes']}")
        
        if self.stats['committed_blocks'] > 0:
            avg_latency = self.stats['total_latency_ms'] / self.stats['committed_blocks']
            avg_rounds = self.stats['total_rounds'] / self.stats['committed_blocks']
            logger.info(f"Average latency: {avg_latency:.2f} ms")
            logger.info(f"Average rounds: {avg_rounds:.2f}")
        
        logger.info(f"\nChain length: {len(self.blockchain)}")
        logger.info(f"Byzantine validators: {self.byzantine_count}/{self.num_validators}")
        logger.info(f"Quorum size: {self.quorum_size}")
        logger.info("=" * 70 + "\n")
    
    def generate_report(self, output_path: str):
        """Generate JSON report of simulation."""
        report = {
            "configuration": {
                "num_validators": self.num_validators,
                "byzantine_count": self.byzantine_count,
                "quorum_size": self.quorum_size,
                "network_delay_ms": self.network_delay_ms,
                "timeout_ms": self.timeout_ms
            },
            "statistics": self.stats,
            "blockchain": [
                {
                    "height": block.height,
                    "hash": block.hash,
                    "data": block.data,
                    "proposer": block.proposer
                }
                for block in self.blockchain
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.success(f"Report saved to {output_path}")


async def main():
    """Example usage."""
    logger.info("MonadBFT Consensus Simulation\n")
    
    # Create simulator with 10 validators, 1 Byzantine
    sim = MonadBFTSimulator(
        num_validators=10,
        byzantine_count=1,
        network_delay_ms=30.0
    )
    
    # Simulate consensus for 20 blocks
    for i in range(20):
        block = sim.propose_block(f"Transaction batch {i}")
        result = await sim.run_consensus(block)
        
        logger.info(f"\nBlock {i} result: {result.status}")
        logger.info(f"  Latency: {result.latency_ms:.2f} ms")
        logger.info(f"  Rounds: {result.rounds}")
        logger.info(f"  View changes: {result.view_changes}")
        
        # Small delay between blocks
        await asyncio.sleep(0.1)
    
    # Print statistics
    sim.print_statistics()
    
    # Generate report
    sim.generate_report("simulation_results.json")


if __name__ == "__main__":
    asyncio.run(main())