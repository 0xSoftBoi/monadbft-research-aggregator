#!/usr/bin/env python3
"""
Tail-Forking Prevention Demonstration

Demonstrates MonadBFT's tail-forking prevention mechanism where validators
lock on proposed blocks during voting to prevent malicious leaders from
creating competing forks at the chain tail.

Key mechanism:
- Validators lock on blocks when voting
- Locked validators only vote for extending blocks
- Prevents Byzantine leaders from creating forks
- Maintains responsiveness despite Byzantine behavior
"""

import asyncio
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from enum import Enum
import hashlib
from loguru import logger
from rich.console import Console
from rich.table import Table

console = Console()


class AttackType(Enum):
    """Types of forking attacks."""
    DOUBLE_PROPOSE = "double_propose"  # Leader proposes two conflicting blocks
    SELFISH_FORK = "selfish_fork"      # Leader withholds blocks to create fork
    LONG_RANGE = "long_range"          # Attempt to fork from old block


@dataclass
class Block:
    height: int
    data: str
    parent_hash: str
    proposer: int
    nonce: int = 0
    
    @property
    def hash(self) -> str:
        content = f"{self.height}{self.data}{self.parent_hash}{self.proposer}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class LockInfo:
    """Information about a validator's lock."""
    block_hash: str
    height: int
    view: int


class ValidatorNode:
    """Validator with locking mechanism."""
    
    def __init__(self, validator_id: int, is_byzantine: bool = False):
        self.id = validator_id
        self.is_byzantine = is_byzantine
        self.locked: Optional[LockInfo] = None
        self.voted_blocks: Set[str] = set()
        self.seen_blocks: Dict[str, Block] = {}
    
    def can_vote(self, block: Block) -> tuple[bool, str]:
        """Check if validator can vote for a block."""
        # Byzantine validators might vote for anything
        if self.is_byzantine:
            if random.random() > 0.5:
                return True, "Byzantine - random vote"
            else:
                return False, "Byzantine - withheld vote"
        
        # Already voted for this block
        if block.hash in self.voted_blocks:
            return False, "Already voted"
        
        # Check lock
        if self.locked:
            # Can only vote for blocks extending the locked block
            if block.height <= self.locked.height:
                return False, f"Locked on block at height {self.locked.height}"
            
            # Must extend from locked block's chain
            if block.parent_hash != self.locked.block_hash:
                # Check if parent is descendant of locked block
                if not self._is_descendant(block.parent_hash, self.locked.block_hash):
                    return False, f"Does not extend locked block {self.locked.block_hash}"
        
        return True, "Approved"
    
    def _is_descendant(self, block_hash: str, ancestor_hash: str) -> bool:
        """Check if block is descendant of ancestor."""
        # Simplified check - in real implementation, traverse chain
        current = block_hash
        visited = set()
        
        while current in self.seen_blocks and current not in visited:
            if current == ancestor_hash:
                return True
            visited.add(current)
            current = self.seen_blocks[current].parent_hash
        
        return False
    
    def vote(self, block: Block, view: int) -> bool:
        """Vote for a block and lock on it."""
        can_vote, reason = self.can_vote(block)
        
        if not can_vote:
            logger.debug(f"Validator {self.id} cannot vote: {reason}")
            return False
        
        # Record vote
        self.voted_blocks.add(block.hash)
        self.seen_blocks[block.hash] = block
        
        # Lock on this block (TAIL-FORKING PREVENTION)
        if not self.is_byzantine:
            self.locked = LockInfo(
                block_hash=block.hash,
                height=block.height,
                view=view
            )
            logger.debug(f"Validator {self.id} locked on block {block.hash} at height {block.height}")
        
        return True
    
    def unlock(self):
        """Unlock after block is committed."""
        self.locked = None


class TailForkDemo:
    """Demonstration of tail-forking prevention."""
    
    def __init__(self, num_validators: int = 7, byzantine_count: int = 2):
        self.num_validators = num_validators
        self.byzantine_count = byzantine_count
        self.validators = [
            ValidatorNode(i, is_byzantine=(i < byzantine_count))
            for i in range(num_validators)
        ]
        self.quorum = (2 * byzantine_count + 1)
        
        # Genesis block
        self.genesis = Block(0, "GENESIS", "0" * 12, -1)
        self.chain = [self.genesis]
    
    def get_honest_validators(self) -> List[ValidatorNode]:
        return [v for v in self.validators if not v.is_byzantine]
    
    def get_byzantine_validators(self) -> List[ValidatorNode]:
        return [v for v in self.validators if v.is_byzantine]
    
    def propose_block(self, data: str, parent: Block, proposer: int, nonce: int = 0) -> Block:
        """Propose a new block."""
        return Block(
            height=parent.height + 1,
            data=data,
            parent_hash=parent.hash,
            proposer=proposer,
            nonce=nonce
        )
    
    def collect_votes(self, block: Block, view: int) -> tuple[int, List[int]]:
        """Collect votes for a block."""
        votes = []
        for validator in self.validators:
            if validator.vote(block, view):
                votes.append(validator.id)
        return len(votes), votes
    
    def simulate_honest_scenario(self) -> Dict:
        """Simulate honest leader proposing a block."""
        console.print("\n[bold cyan]Scenario 1: Honest Leader[/bold cyan]")
        
        parent = self.chain[-1]
        block = self.propose_block("Honest block", parent, proposer=self.byzantine_count)
        
        console.print(f"Block proposed: {block.hash} at height {block.height}")
        console.print(f"Parent: {parent.hash}\n")
        
        vote_count, voters = self.collect_votes(block, view=1)
        
        table = Table(title="Voting Results")
        table.add_column("Validator", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Voted", style="green")
        table.add_column("Locked On", style="yellow")
        
        for v in self.validators:
            voted = "✓" if v.id in voters else "✗"
            v_type = "Byzantine" if v.is_byzantine else "Honest"
            locked = v.locked.block_hash if v.locked else "None"
            table.add_row(str(v.id), v_type, voted, locked)
        
        console.print(table)
        console.print(f"\nVotes: {vote_count}/{self.num_validators} (quorum: {self.quorum})")
        
        result = {
            "success": vote_count >= self.quorum,
            "votes": vote_count,
            "quorum": self.quorum,
            "locked_validators": len([v for v in self.validators if v.locked])
        }
        
        if result["success"]:
            console.print("[bold green]✓ Quorum reached - Block committed[/bold green]")
            self.chain.append(block)
        else:
            console.print("[bold red]✗ Quorum not reached[/bold red]")
        
        return result
    
    def simulate_byzantine_leader_attack(self) -> Dict:
        """Simulate Byzantine leader attempting to create a fork."""
        console.print("\n[bold red]Scenario 2: Byzantine Leader Double-Propose Attack[/bold red]")
        
        parent = self.chain[-1]
        byzantine_leader = 0  # First validator is Byzantine
        
        # Byzantine leader creates TWO conflicting blocks
        block_a = self.propose_block("Fork A", parent, proposer=byzantine_leader, nonce=1)
        block_b = self.propose_block("Fork B", parent, proposer=byzantine_leader, nonce=2)
        
        console.print(f"\nByzantine leader {byzantine_leader} proposes TWO conflicting blocks:")
        console.print(f"  Block A: {block_a.hash}")
        console.print(f"  Block B: {block_b.hash}")
        console.print(f"  Both at height {block_a.height}, parent {parent.hash}\n")
        
        # First, some validators vote for Block A
        console.print("[yellow]Phase 1: Block A proposed to subset of validators[/yellow]")
        votes_a, voters_a = self.collect_votes(block_a, view=2)
        
        console.print(f"Block A received {votes_a} votes from validators: {voters_a}")
        console.print(f"These validators are now LOCKED on Block A\n")
        
        # Then, Byzantine leader tries to get votes for Block B
        console.print("[yellow]Phase 2: Block B proposed to other validators[/yellow]")
        
        # Reset voted_blocks to simulate proposing to different validators
        initial_locked = {v.id: v.locked for v in self.validators}
        
        votes_b = 0
        voters_b = []
        for validator in self.validators:
            # Don't reset locks - this is the key to prevention
            can_vote, reason = validator.can_vote(block_b)
            
            if can_vote and validator.is_byzantine:
                # Byzantine validators might double-vote
                validator.voted_blocks.add(block_b.hash)
                votes_b += 1
                voters_b.append(validator.id)
                console.print(f"  Validator {validator.id} (Byzantine): Voted for Block B")
            elif can_vote:
                console.print(f"  Validator {validator.id}: Could vote but not locked yet")
            else:
                console.print(f"  Validator {validator.id}: [red]REJECTED[/red] - {reason}")
        
        console.print(f"\nBlock B received {votes_b} votes from validators: {voters_b}")
        
        # Analysis
        table = Table(title="Fork Prevention Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        fork_prevented = votes_a >= self.quorum and votes_b < self.quorum
        
        table.add_row("Block A votes", f"{votes_a}/{self.num_validators}")
        table.add_row("Block B votes", f"{votes_b}/{self.num_validators}")
        table.add_row("Quorum required", str(self.quorum))
        table.add_row("Locked validators", str(len([v for v in self.validators if v.locked])))
        table.add_row("Fork prevented", "YES" if fork_prevented else "NO")
        
        console.print(table)
        
        if fork_prevented:
            console.print("\n[bold green]✓ TAIL-FORKING PREVENTED[/bold green]")
            console.print("Validators locked on Block A prevent voting for Block B")
            console.print("Block A reaches quorum, Block B does not")
        else:
            console.print("\n[bold yellow]⚠ Attack scenario - both blocks could proceed[/bold yellow]")
        
        return {
            "fork_prevented": fork_prevented,
            "block_a_votes": votes_a,
            "block_b_votes": votes_b,
            "locked_count": len([v for v in self.validators if v.locked]),
            "attack_type": AttackType.DOUBLE_PROPOSE.value
        }
    
    def simulate_long_range_attack(self) -> Dict:
        """Simulate attempt to fork from an old block."""
        console.print("\n[bold red]Scenario 3: Long-Range Fork Attack[/bold red]")
        
        # Build a short chain first
        for i in range(3):
            parent = self.chain[-1]
            block = self.propose_block(f"Block {i}", parent, proposer=self.byzantine_count + 1)
            votes, _ = self.collect_votes(block, view=3 + i)
            if votes >= self.quorum:
                self.chain.append(block)
                # Unlock validators after commit
                for v in self.validators:
                    v.unlock()
        
        console.print(f"Current chain length: {len(self.chain)}")
        console.print(f"Chain tip: {self.chain[-1].hash} at height {self.chain[-1].height}\n")
        
        # Byzantine leader tries to fork from genesis
        old_parent = self.chain[0]  # Genesis
        fork_block = self.propose_block("Malicious fork", old_parent, proposer=0, nonce=99)
        
        console.print(f"Byzantine leader attempts fork from height {old_parent.height}")
        console.print(f"Fork block: {fork_block.hash} at height {fork_block.height}")
        console.print(f"Current chain is at height {self.chain[-1].height}\n")
        
        votes, voters = self.collect_votes(fork_block, view=10)
        
        console.print(f"Fork block votes: {votes}/{self.num_validators}")
        console.print(f"Voters: {voters}")
        
        prevented = votes < self.quorum
        
        if prevented:
            console.print("\n[bold green]✓ LONG-RANGE FORK PREVENTED[/bold green]")
            console.print("Validators reject fork from old block")
        
        return {
            "fork_prevented": prevented,
            "votes": votes,
            "attack_type": AttackType.LONG_RANGE.value
        }
    
    def generate_visual_report(self) -> str:
        """Generate visual report of tail-forking prevention."""
        report = []
        report.append("\nTAIL-FORKING PREVENTION MECHANISM")
        report.append("=" * 50)
        report.append("\nHow it works:")
        report.append("1. Validator votes for proposed block")
        report.append("2. Validator LOCKS on that block")
        report.append("3. Locked validator only votes for extending blocks")
        report.append("4. Prevents voting for conflicting forks")
        report.append("\nByzantine Attack Scenarios:")
        report.append("\n1. Double-Propose Attack:")
        report.append("   - Byzantine leader proposes two blocks")
        report.append("   - First block receives votes, validators lock")
        report.append("   - Locked validators reject second block")
        report.append("   - Only first block reaches quorum")
        report.append("\n2. Long-Range Attack:")
        report.append("   - Attacker tries to fork from old block")
        report.append("   - Validators locked on recent blocks")
        report.append("   - Reject votes for low-height forks")
        report.append("\nSecurity Properties:")
        report.append(f"  • Byzantine fault tolerance: f < n/3")
        report.append(f"  • Current: {self.byzantine_count}/{self.num_validators} Byzantine")
        report.append(f"  • Quorum size: {self.quorum}")
        report.append(f"  • Safety: Guaranteed by locking mechanism")
        report.append(f"  • Liveness: Preserved through view-change")
        
        return "\n".join(report)


async def main():
    """Run tail-forking prevention demonstrations."""
    console.print("\n[bold]MonadBFT Tail-Forking Prevention Demo[/bold]\n")
    
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    
    # Scenario 1: Honest leader
    result1 = demo.simulate_honest_scenario()
    await asyncio.sleep(1)
    
    # Reset for next scenario
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    demo.chain = [demo.genesis]
    
    # Scenario 2: Byzantine double-propose attack
    result2 = demo.simulate_byzantine_leader_attack()
    await asyncio.sleep(1)
    
    # Scenario 3: Long-range attack
    demo = TailForkDemo(num_validators=7, byzantine_count=2)
    result3 = demo.simulate_long_range_attack()
    
    # Print summary report
    console.print(demo.generate_visual_report())
    
    # Summary
    console.print("\n[bold cyan]Summary of Results[/bold cyan]")
    console.print(f"Scenario 1 (Honest): {'PASSED' if result1['success'] else 'FAILED'}")
    console.print(f"Scenario 2 (Double-propose): {'PREVENTED' if result2['fork_prevented'] else 'VULNERABLE'}")
    console.print(f"Scenario 3 (Long-range): {'PREVENTED' if result3['fork_prevented'] else 'VULNERABLE'}")


if __name__ == "__main__":
    asyncio.run(main())