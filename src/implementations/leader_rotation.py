#!/usr/bin/env python3
"""
Leader Rotation and View-Change Simulation

Demonstrates MonadBFT's view-change mechanism for leader rotation when:
- Current leader is unresponsive
- Current leader is Byzantine
- Network partition detected
- Timeout occurs

Key features:
- Fast leader rotation on timeout
- Preservation of safety during view changes
- Recovery from Byzantine leaders
- Liveness guarantee through leader rotation
"""

import asyncio
import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import hashlib
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

console = Console()


class ViewChangeReason(Enum):
    """Reasons for triggering view change."""
    TIMEOUT = "timeout"
    BYZANTINE_LEADER = "byzantine_leader"
    NO_PROPOSAL = "no_proposal"
    INVALID_PROPOSAL = "invalid_proposal"
    QUORUM_FAILURE = "quorum_failure"


class LeaderStatus(Enum):
    """Leader node status."""
    ACTIVE = "active"
    UNRESPONSIVE = "unresponsive"
    BYZANTINE = "byzantine"
    CRASHED = "crashed"


@dataclass
class Block:
    height: int
    data: str
    parent_hash: str
    proposer: int
    view: int
    
    @property
    def hash(self) -> str:
        content = f"{self.height}{self.data}{self.parent_hash}{self.proposer}{self.view}"
        return hashlib.sha256(content.encode()).hexdigest()[:10]


@dataclass
class ViewChangeMessage:
    """Message sent by validators to trigger view change."""
    from_validator: int
    old_view: int
    new_view: int
    reason: ViewChangeReason
    timestamp: float = field(default_factory=time.time)


@dataclass
class NewViewMessage:
    """Message sent by new leader to start new view."""
    new_leader: int
    view: int
    highest_qc: Optional[str]  # Hash of highest QC seen
    timestamp: float = field(default_factory=time.time)


@dataclass
class ViewChangeStats:
    """Statistics for a view change event."""
    old_view: int
    new_view: int
    old_leader: int
    new_leader: int
    reason: ViewChangeReason
    duration_ms: float
    messages_sent: int
    success: bool


class Validator:
    """Validator node participating in consensus."""
    
    def __init__(self, validator_id: int, is_byzantine: bool = False):
        self.id = validator_id
        self.is_byzantine = is_byzantine
        self.current_view = 0
        self.view_change_votes: Dict[int, List[int]] = {}  # new_view -> list of voter IDs
        self.highest_qc_view = 0
    
    def detect_timeout(self, expected_proposal_time: float, timeout_ms: float) -> bool:
        """Detect if leader has timed out."""
        elapsed = (time.time() - expected_proposal_time) * 1000
        return elapsed > timeout_ms
    
    def create_view_change_message(self, reason: ViewChangeReason) -> ViewChangeMessage:
        """Create view change message."""
        return ViewChangeMessage(
            from_validator=self.id,
            old_view=self.current_view,
            new_view=self.current_view + 1,
            reason=reason
        )
    
    def vote_for_view_change(self, new_view: int) -> bool:
        """Vote for a view change."""
        if self.is_byzantine and random.random() > 0.6:
            # Byzantine validators sometimes don't participate
            return False
        
        if new_view not in self.view_change_votes:
            self.view_change_votes[new_view] = []
        
        if self.id not in self.view_change_votes[new_view]:
            self.view_change_votes[new_view].append(self.id)
            return True
        
        return False


class LeaderRotationSimulator:
    """Simulator for leader rotation and view changes."""
    
    def __init__(
        self,
        num_validators: int = 7,
        byzantine_count: int = 2,
        timeout_ms: float = 1000.0
    ):
        self.num_validators = num_validators
        self.byzantine_count = byzantine_count
        self.timeout_ms = timeout_ms
        self.quorum = 2 * byzantine_count + 1
        
        self.validators = [
            Validator(i, is_byzantine=(i < byzantine_count))
            for i in range(num_validators)
        ]
        
        self.current_view = 0
        self.current_leader = 0
        self.leader_statuses: Dict[int, LeaderStatus] = {
            i: LeaderStatus.ACTIVE for i in range(num_validators)
        }
        
        self.view_change_history: List[ViewChangeStats] = []
        self.blocks_committed = 0
    
    def get_leader(self, view: int) -> int:
        """Get leader for a given view (round-robin)."""
        return view % self.num_validators
    
    def set_leader_status(self, leader_id: int, status: LeaderStatus):
        """Set leader status (for simulation)."""
        self.leader_statuses[leader_id] = status
        logger.info(f"Leader {leader_id} status set to: {status.value}")
    
    async def leader_proposes_block(self, leader_id: int) -> Optional[Block]:
        """Simulate leader proposing a block."""
        status = self.leader_statuses[leader_id]
        
        if status == LeaderStatus.UNRESPONSIVE or status == LeaderStatus.CRASHED:
            logger.warning(f"Leader {leader_id} is {status.value}, no proposal")
            return None
        
        if status == LeaderStatus.BYZANTINE:
            if random.random() > 0.5:
                # Byzantine leader sometimes proposes
                logger.warning(f"Byzantine leader {leader_id} proposes invalid block")
                return Block(
                    height=self.blocks_committed,
                    data="INVALID",
                    parent_hash="invalid",
                    proposer=leader_id,
                    view=self.current_view
                )
            else:
                logger.warning(f"Byzantine leader {leader_id} withholds proposal")
                return None
        
        # Normal proposal
        await asyncio.sleep(0.05)  # Simulate proposal delay
        
        return Block(
            height=self.blocks_committed,
            data=f"Transactions {self.blocks_committed}",
            parent_hash="prev_hash",
            proposer=leader_id,
            view=self.current_view
        )
    
    async def collect_view_change_votes(self, reason: ViewChangeReason) -> int:
        """Collect votes for view change."""
        new_view = self.current_view + 1
        votes = 0
        
        logger.info(f"Collecting view-change votes for view {new_view}")
        
        for validator in self.validators:
            await asyncio.sleep(0.01)  # Simulate network delay
            
            if validator.vote_for_view_change(new_view):
                votes += 1
                logger.debug(f"  Validator {validator.id} voted for view change")
        
        logger.info(f"Collected {votes}/{self.num_validators} votes (quorum: {self.quorum})")
        return votes
    
    async def execute_view_change(self, reason: ViewChangeReason) -> ViewChangeStats:
        """Execute view change protocol."""
        start_time = time.time()
        old_view = self.current_view
        old_leader = self.get_leader(old_view)
        
        logger.warning(f"\n{'='*60}")
        logger.warning(f"VIEW CHANGE INITIATED")
        logger.warning(f"Reason: {reason.value}")
        logger.warning(f"Current view: {old_view}, Leader: {old_leader}")
        logger.warning(f"{'='*60}\n")
        
        # Phase 1: Collect view-change votes
        votes = await self.collect_view_change_votes(reason)
        messages_sent = votes
        
        if votes < self.quorum:
            logger.error("Failed to reach quorum for view change!")
            duration_ms = (time.time() - start_time) * 1000
            return ViewChangeStats(
                old_view=old_view,
                new_view=old_view,
                old_leader=old_leader,
                new_leader=old_leader,
                reason=reason,
                duration_ms=duration_ms,
                messages_sent=messages_sent,
                success=False
            )
        
        # Phase 2: Transition to new view
        self.current_view += 1
        new_leader = self.get_leader(self.current_view)
        
        logger.info(f"\nTransitioning to new view: {self.current_view}")
        logger.info(f"New leader: {new_leader}")
        
        # Update validator views
        for validator in self.validators:
            validator.current_view = self.current_view
        
        # Phase 3: New leader broadcasts NEW-VIEW message
        await asyncio.sleep(0.05)
        new_view_msg = NewViewMessage(
            new_leader=new_leader,
            view=self.current_view,
            highest_qc=None
        )
        
        logger.success(f"\n✓ VIEW CHANGE COMPLETE")
        logger.success(f"View: {old_view} → {self.current_view}")
        logger.success(f"Leader: {old_leader} → {new_leader}\n")
        
        duration_ms = (time.time() - start_time) * 1000
        
        stats = ViewChangeStats(
            old_view=old_view,
            new_view=self.current_view,
            old_leader=old_leader,
            new_leader=new_leader,
            reason=reason,
            duration_ms=duration_ms,
            messages_sent=messages_sent,
            success=True
        )
        
        self.view_change_history.append(stats)
        return stats
    
    async def run_consensus_round(self) -> bool:
        """Run one round of consensus."""
        leader_id = self.get_leader(self.current_view)
        
        console.print(f"\n[cyan]View {self.current_view}: Leader {leader_id}[/cyan]")
        
        # Wait for proposal with timeout
        proposal_start = time.time()
        
        try:
            # Leader proposes
            block = await asyncio.wait_for(
                self.leader_proposes_block(leader_id),
                timeout=self.timeout_ms / 1000.0
            )
            
            if block is None:
                console.print("[red]No proposal received[/red]")
                await self.execute_view_change(ViewChangeReason.NO_PROPOSAL)
                return False
            
            # Validate proposal
            if block.data == "INVALID":
                console.print("[red]Invalid proposal detected[/red]")
                await self.execute_view_change(ViewChangeReason.INVALID_PROPOSAL)
                return False
            
            # Simulate voting
            console.print(f"[green]Block proposed: {block.hash}[/green]")
            votes = random.randint(self.quorum, self.num_validators)
            
            if votes >= self.quorum:
                console.print(f"[green]✓ Block committed ({votes} votes)[/green]")
                self.blocks_committed += 1
                return True
            else:
                console.print(f"[yellow]✗ Quorum not reached ({votes} votes)[/yellow]")
                await self.execute_view_change(ViewChangeReason.QUORUM_FAILURE)
                return False
        
        except asyncio.TimeoutError:
            console.print("[red]Timeout waiting for proposal[/red]")
            await self.execute_view_change(ViewChangeReason.TIMEOUT)
            return False
    
    def print_statistics(self):
        """Print view change statistics."""
        if not self.view_change_history:
            console.print("\nNo view changes occurred")
            return
        
        table = Table(title="View Change History")
        table.add_column("#", style="cyan")
        table.add_column("View Change", style="yellow")
        table.add_column("Leader Change", style="magenta")
        table.add_column("Reason", style="red")
        table.add_column("Duration (ms)", style="green")
        table.add_column("Status", style="blue")
        
        for i, stats in enumerate(self.view_change_history, 1):
            view_change = f"{stats.old_view} → {stats.new_view}"
            leader_change = f"{stats.old_leader} → {stats.new_leader}"
            status = "✓ Success" if stats.success else "✗ Failed"
            
            table.add_row(
                str(i),
                view_change,
                leader_change,
                stats.reason.value,
                f"{stats.duration_ms:.1f}",
                status
            )
        
        console.print("\n")
        console.print(table)
        
        # Summary statistics
        total_duration = sum(s.duration_ms for s in self.view_change_history)
        avg_duration = total_duration / len(self.view_change_history)
        success_rate = sum(1 for s in self.view_change_history if s.success) / len(self.view_change_history)
        
        summary = Table(title="Summary Statistics")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="yellow")
        
        summary.add_row("Total view changes", str(len(self.view_change_history)))
        summary.add_row("Blocks committed", str(self.blocks_committed))
        summary.add_row("Success rate", f"{success_rate:.1%}")
        summary.add_row("Avg view change time", f"{avg_duration:.1f} ms")
        summary.add_row("Total consensus views", str(self.current_view + 1))
        
        console.print("\n")
        console.print(summary)


async def demo_scenarios():
    """Demonstrate various view-change scenarios."""
    console.print("\n[bold]MonadBFT Leader Rotation & View-Change Demo[/bold]\n")
    
    # Scenario 1: Unresponsive leader
    console.print("[bold yellow]Scenario 1: Unresponsive Leader[/bold yellow]")
    sim1 = LeaderRotationSimulator(num_validators=7, byzantine_count=2, timeout_ms=500)
    sim1.set_leader_status(0, LeaderStatus.UNRESPONSIVE)
    await sim1.run_consensus_round()
    await asyncio.sleep(0.5)
    
    # Scenario 2: Byzantine leader
    console.print("\n[bold yellow]Scenario 2: Byzantine Leader[/bold yellow]")
    sim2 = LeaderRotationSimulator(num_validators=7, byzantine_count=2)
    sim2.set_leader_status(0, LeaderStatus.BYZANTINE)
    await sim2.run_consensus_round()
    await asyncio.sleep(0.5)
    
    # Scenario 3: Multiple view changes
    console.print("\n[bold yellow]Scenario 3: Multiple Faulty Leaders[/bold yellow]")
    sim3 = LeaderRotationSimulator(num_validators=10, byzantine_count=3)
    
    # Make first 3 leaders faulty
    sim3.set_leader_status(0, LeaderStatus.BYZANTINE)
    sim3.set_leader_status(1, LeaderStatus.UNRESPONSIVE)
    sim3.set_leader_status(2, LeaderStatus.BYZANTINE)
    
    # Run several rounds
    for i in range(5):
        success = await sim3.run_consensus_round()
        await asyncio.sleep(0.3)
    
    sim3.print_statistics()


async def main():
    """Run all demonstrations."""
    await demo_scenarios()
    
    console.print("\n[bold green]Key Takeaways[/bold green]")
    console.print("• View changes enable recovery from faulty leaders")
    console.print("• Leader rotation guarantees liveness")
    console.print("• Fast timeout detection minimizes delays")
    console.print("• Safety preserved during view changes")
    console.print("• Byzantine fault tolerance maintained\n")


if __name__ == "__main__":
    asyncio.run(main())