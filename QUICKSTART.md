# MonadBFT Research Aggregator - Quick Start Guide

Welcome to the MonadBFT Research Aggregator! This guide will help you get started quickly.

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/0xSoftBoi/monadbft-research-aggregator.git
cd monadbft-research-aggregator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/papers data/docs data/implementations reports
```

## 🎯 Quick Demo

Run the interactive quick start demo:

```bash
python quickstart.py
```

This will demonstrate:
- ✅ BFT Consensus Simulation
- ✅ Tail-Forking Prevention
- ✅ Speculative Finality
- ✅ Performance Benchmarking
- ✅ Fork Resistance Testing

## 📚 Core Components

### 1. Research Paper Aggregation

Collect research papers and documentation:

```bash
python src/research_scraper.py --sources arxiv,github,documentation
```

### 2. BFT Consensus Simulation

Run a basic consensus simulation:

```python
from implementations.bft_consensus_sim import MonadBFTSimulator

# Create simulator with 7 validators
sim = MonadBFTSimulator(num_validators=7, byzantine_count=2)

# Propose and commit a block
block = sim.propose_block("My transaction batch")
result = await sim.run_consensus(block)

print(f"Status: {result.status}")
print(f"Latency: {result.latency_ms:.2f}ms")
```

### 3. Tail-Forking Prevention Demo

Demonstrate Byzantine attack prevention:

```bash
python src/implementations/tail_fork_prevention.py
```

### 4. Speculative Finality

Test adaptive 1-round vs 2-round commits:

```bash
python src/implementations/speculative_finality.py
```

### 5. Performance Benchmarks

Run comprehensive benchmarks:

```bash
python src/benchmarks/consensus_benchmark.py
```

### 6. Code Analysis

Analyze implementations for security and correctness:

```bash
python src/analysis/code_analyzer.py --repo .
```

### 7. Documentation Generation

Generate research summaries and reports:

```bash
python src/documentation/doc_generator.py
```

## 🔬 Example Use Cases

### For Blockchain Settlement Research

```python
from examples.settlement_layer_example import SettlementLayerSimulator

# Create settlement layer
layer = SettlementLayerSimulator(validators=10)

# Settle cross-chain transaction
settlement = await layer.settle_transaction(
    source="ethereum",
    dest="bitcoin",
    amount=1.5
)

print(f"Settlement finalized in {settlement.finality_time*1000:.2f}ms")
```

### For Protocol Comparison

```python
from benchmarks.consensus_benchmark import ConsensusComparison

comparison = ConsensusComparison()
results = await comparison.compare_protocols([
    "MonadBFT",
    "HotStuff",
    "Tendermint"
])

comparison.plot_comparison(results, ["latency", "throughput"])
```

### For Security Analysis

```python
from benchmarks.fork_resistance import ForkResistanceTest

test = ForkResistanceTest()
results = await test.run_attack_scenarios([
    "double_spend",
    "selfish_mining",
    "nothing_at_stake",
    "long_range_attack"
])
```

## 📊 Understanding Results

### Consensus Metrics

- **Latency**: Time to commit a block (target: < 200ms)
- **Throughput**: Transactions per second (target: > 1000 TPS)
- **Success Rate**: Percentage of successful commits
- **View Changes**: Number of leader rotations needed

### Safety Properties

- **Agreement**: All honest validators commit same blocks
- **Validity**: Only valid blocks are committed
- **Integrity**: Committed blocks cannot be altered

### Liveness Properties

- **Termination**: Consensus eventually completes
- **Progress**: Continuous block commitment
- **Responsiveness**: Fast finality under good conditions

## 🎓 Key Concepts

### Streamlined Communication

MonadBFT uses **O(n)** communication instead of O(n²):

```
Traditional BFT:        MonadBFT:
V1 ↔ V2 ↔ V3 ↔ V4       V1 → Leader ← V2
 ↕    ↕    ↕    ↕               ↕
V5 ↔ V6 ↔ V7 ↔ V8       V3 → Leader ← V4
```

### Tail-Forking Prevention

Validators **lock** on blocks when voting:

```python
# Validator votes for Block A
validator.vote(block_a, view=1)
validator.lock_on_block(block_a)

# Byzantine leader proposes Block B (conflicts with A)
# Validator REJECTS Block B because locked on A
can_vote = validator.can_vote(block_b)  # Returns False
```

### Speculative Finality

Adaptive confirmation in 1 or 2 rounds:

```python
# Good network conditions → 1 round
if network_quality > 0.7 and recent_performance_good:
    commit_in_1_round()  # ⚡ Speculative finality

# Poor conditions → 2 rounds
else:
    commit_in_2_rounds()  # 🔄 Standard safety
```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_consensus.py -v

# Run with coverage
pytest --cov=src tests/
```

## 📈 Benchmarking Guide

### Quick Benchmark

```bash
# 30-second quick test
python src/benchmarks/consensus_benchmark.py --duration 30
```

### Comprehensive Benchmark

```bash
# Full benchmark suite (may take 5-10 minutes)
python src/benchmarks/consensus_benchmark.py \
    --validators 4,7,10,25 \
    --delays 10,50,100 \
    --blocks 100
```

### Custom Benchmark

```python
from benchmarks.consensus_benchmark import LatencyBenchmark

bench = LatencyBenchmark()
results = await bench.run(
    validator_counts=[4, 7, 10],
    network_delays=[10, 50, 100],
    num_blocks=50
)

bench.plot_results("my_benchmark.png")
```

## 🔍 Code Analysis Guide

### Analyze Your Implementation

```bash
python src/analysis/code_analyzer.py --repo /path/to/your/monadbft/impl
```

### Analysis Output

The analyzer checks for:
- ✅ Consensus component presence
- ✅ Safety property implementation
- ✅ Liveness guarantees
- ✅ Security vulnerabilities
- ✅ Code quality metrics

## 📝 Documentation Generation

### Generate Research Summary

```bash
python -c "
from documentation.doc_generator import DocumentationGenerator
gen = DocumentationGenerator()
gen.generate_research_summary(
    sources=['arxiv:2502.20692', 'docs.monad.xyz'],
    output='reports/summary.md'
)
"
```

### Generate Implementation Guide

```bash
python -c "
from documentation.doc_generator import DocumentationGenerator
gen = DocumentationGenerator()
gen.generate_implementation_guide(
    language='rust',
    output='reports/rust_guide.md'
)
"
```

## 🎯 Next Steps

1. **Explore Examples**: Check `examples/` directory for detailed use cases
2. **Run Demos**: Try `python src/implementations/[demo].py` for individual features
3. **Customize**: Modify configurations in `config/sources.yaml`
4. **Extend**: Add your own implementations and tests
5. **Contribute**: See GitHub issues for contribution opportunities

## 📖 Additional Resources

- **MonadBFT Paper**: [arXiv:2502.20692](https://arxiv.org/abs/2502.20692)
- **Official Docs**: [docs.monad.xyz](https://docs.monad.xyz)
- **Category Labs**: [GitHub](https://github.com/category-labs)
- **HotStuff Paper**: [arXiv:1803.05069](https://arxiv.org/abs/1803.05069)

## 🐛 Troubleshooting

### Import Errors

```bash
# Make sure you're in the right directory
cd monadbft-research-aggregator

# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Network Issues

```bash
# If scraping fails, check internet connection
# Or run offline with cached data
python src/research_scraper.py --offline --cache data/cache.json
```

### Performance Issues

```bash
# Reduce validator count or block count for faster tests
python quickstart.py --validators 4 --blocks 10
```

## 💡 Tips

- **Start Small**: Begin with 4-7 validators for faster iteration
- **Use Caching**: Enable caching for research aggregation
- **Profile Code**: Use `--profile` flag to identify bottlenecks
- **Visualize**: Generate plots to understand performance characteristics
- **Test Edge Cases**: Try Byzantine ratios near f = (n-1)/3

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/0xSoftBoi/monadbft-research-aggregator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/0xSoftBoi/monadbft-research-aggregator/discussions)
- **Email**: Open an issue for support requests

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details

---

**Happy researching!** 🚀

Built with ❤️ for blockchain settlement research and Global Settlement architecture work.
