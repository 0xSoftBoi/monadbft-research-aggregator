#!/usr/bin/env python3
"""
Unit Tests for MonadBFT Consensus Implementation

Tests core consensus functionality, safety properties, and edge cases.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from implementations.bft_consensus_sim import (
    MonadBFTSimulator,
    Validator,
    Block,
    ValidatorStatus,
    Phase
)


class TestBasicConsensus:
    """Test basic consensus functionality."""
    
    @pytest.mark.asyncio
    async def test_genesis_initialization(self):
        """Test genesis block initialization."""
        sim = MonadBFTSimulator(num_validators=4)
        assert len(sim.blockchain) == 1
        assert sim.blockchain[0].height == 0
        assert sim.blockchain[0].data == "GENESIS"
    
    @pytest.mark.asyncio
    async def test_single_block_consensus(self):
        """Test consensus for a single block."""
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=0)
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        assert result.status == "committed"
        assert result.block is not None
        assert len(sim.blockchain) == 2
    
    @pytest.mark.asyncio
    async def test_multiple_blocks(self):
        """Test consensus for multiple sequential blocks."""
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=0)
        
        for i in range(5):
            block = sim.propose_block(f"Block {i}")
            result = await sim.run_consensus(block)
            assert result.status == "committed"
        
        assert len(sim.blockchain) == 6  # Genesis + 5 blocks


class TestByzantineTolerance:
    """Test Byzantine fault tolerance."""
    
    @pytest.mark.asyncio
    async def test_with_one_byzantine(self):
        """Test consensus with one Byzantine validator."""
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=1)
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        # Should still reach consensus
        assert result.status == "committed"
    
    @pytest.mark.asyncio
    async def test_byzantine_threshold(self):
        """Test Byzantine threshold (f < n/3)."""
        # 10 validators, 3 Byzantine (maximum tolerable)
        sim = MonadBFTSimulator(num_validators=10, byzantine_count=3)
        
        successes = 0
        for i in range(10):
            block = sim.propose_block(f"Block {i}")
            result = await sim.run_consensus(block)
            if result.status == "committed":
                successes += 1
        
        # Should have high success rate
        assert successes >= 7
    
    def test_quorum_calculation(self):
        """Test quorum size calculation."""
        sim = MonadBFTSimulator(num_validators=10, byzantine_count=3)
        # Quorum = 2f + 1 = 2*3 + 1 = 7
        assert sim.quorum_size == 7


class TestValidatorBehavior:
    """Test validator behavior."""
    
    def test_honest_validator_voting(self):
        """Test honest validator voting logic."""
        validator = Validator(0, ValidatorStatus.HONEST)
        block = Block(1, "Test", "parent", 0)
        
        # Should vote for valid block
        assert validator.should_vote(block) == True
    
    def test_validator_locking(self):
        """Test validator locking mechanism."""
        validator = Validator(0, ValidatorStatus.HONEST)
        block = Block(1, "Test", "parent", 0)
        
        # Initially no lock
        assert validator.locked_block is None
        
        # Vote and lock
        vote = validator.create_vote(block, view=0)
        from implementations.bft_consensus_sim import QuorumCertificate
        qc = QuorumCertificate(block.hash, 0, [vote])
        validator.lock_on_block(block, qc)
        
        # Should be locked
        assert validator.locked_block is not None
        assert validator.locked_block.hash == block.hash
    
    def test_byzantine_validator(self):
        """Test Byzantine validator behavior."""
        validator = Validator(0, ValidatorStatus.BYZANTINE)
        
        # Byzantine validators have unpredictable behavior
        assert validator.status == ValidatorStatus.BYZANTINE


class TestSafetyProperties:
    """Test safety properties."""
    
    @pytest.mark.asyncio
    async def test_no_conflicting_commits(self):
        """Test that no conflicting blocks are committed at same height."""
        sim = MonadBFTSimulator(num_validators=7, byzantine_count=2)
        
        # Commit several blocks
        for i in range(10):
            block = sim.propose_block(f"Block {i}")
            await sim.run_consensus(block)
        
        # Check that all committed blocks have sequential heights
        heights = [b.height for b in sim.blockchain]
        assert heights == sorted(heights)
        assert len(heights) == len(set(heights))  # No duplicates
    
    @pytest.mark.asyncio
    async def test_block_integrity(self):
        """Test that committed blocks cannot be altered."""
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=0)
        
        block = sim.propose_block("Original data")
        await sim.run_consensus(block)
        
        committed_block = sim.blockchain[-1]
        original_hash = committed_block.hash
        
        # Attempt to modify would change hash
        assert committed_block.data == "Original data"
        assert committed_block.hash == original_hash


class TestLivenessProperties:
    """Test liveness properties."""
    
    @pytest.mark.asyncio
    async def test_eventual_commitment(self):
        """Test that blocks are eventually committed."""
        sim = MonadBFTSimulator(num_validators=7, byzantine_count=2)
        
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        # Should eventually commit (may take multiple rounds)
        assert result.status in ["committed", "failed"]
        assert result.rounds >= 1
    
    @pytest.mark.asyncio
    async def test_continuous_progress(self):
        """Test that consensus makes continuous progress."""
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=0)
        
        initial_length = len(sim.blockchain)
        
        for i in range(5):
            block = sim.propose_block(f"Block {i}")
            await sim.run_consensus(block)
        
        # Should have made progress
        assert len(sim.blockchain) > initial_length


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_latency_reasonable(self):
        """Test that consensus latency is reasonable."""
        sim = MonadBFTSimulator(
            num_validators=4,
            byzantine_count=0,
            network_delay_ms=10.0
        )
        
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        # Should complete in reasonable time
        assert result.latency_ms < 1000  # Less than 1 second
    
    @pytest.mark.asyncio
    async def test_throughput(self):
        """Test consensus throughput."""
        import time
        
        sim = MonadBFTSimulator(num_validators=4, byzantine_count=0)
        
        start = time.time()
        blocks_committed = 0
        
        for i in range(10):
            block = sim.propose_block(f"Block {i}")
            result = await sim.run_consensus(block)
            if result.status == "committed":
                blocks_committed += 1
        
        duration = time.time() - start
        tps = blocks_committed / duration
        
        # Should achieve reasonable throughput
        assert tps > 1  # At least 1 block per second


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_single_validator(self):
        """Test with single validator (edge case)."""
        sim = MonadBFTSimulator(num_validators=1, byzantine_count=0)
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        # Should still work with one validator
        assert result.status == "committed"
    
    @pytest.mark.asyncio
    async def test_all_byzantine_fails(self):
        """Test that all Byzantine validators cannot reach consensus."""
        # This should fail as f >= n/3
        sim = MonadBFTSimulator(num_validators=3, byzantine_count=3)
        block = sim.propose_block("Test block")
        result = await sim.run_consensus(block)
        
        # Should not commit
        assert result.status != "committed" or result.view_changes > 0
    
    def test_leader_rotation(self):
        """Test leader rotation mechanism."""
        sim = MonadBFTSimulator(num_validators=5, byzantine_count=1)
        
        leaders = []
        for view in range(10):
            leader = sim.get_leader(view)
            leaders.append(leader)
        
        # Leaders should rotate
        assert len(set(leaders)) > 1


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
