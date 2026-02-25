#!/usr/bin/env python3
"""
Code Analysis Framework for MonadBFT Implementations

Analyzes MonadBFT implementations for:
- Code structure and organization
- Safety and liveness properties
- Performance characteristics
- Security vulnerabilities
- Best practices compliance
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import json
from dataclasses import dataclass, asdict
from loguru import logger
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class AnalysisResult:
    """Results from code analysis."""
    repo: str
    language: str
    files_analyzed: int
    total_lines: int
    consensus_components: List[str]
    safety_properties: List[str]
    liveness_properties: List[str]
    security_issues: List[Dict]
    performance_score: int  # 0-100
    test_coverage: float  # 0-100
    code_quality_score: int  # 0-100
    recommendations: List[str]


class MonadBFTAnalyzer:
    """Analyzer for MonadBFT implementations."""
    
    # Key components to look for
    CONSENSUS_COMPONENTS = [
        "propose",
        "vote",
        "commit",
        "view_change",
        "quorum",
        "leader",
        "validator",
        "block",
        "certificate"
    ]
    
    # Safety properties
    SAFETY_PROPERTIES = [
        "agreement",
        "validity",
        "integrity",
        "lock",
        "fork_prevention"
    ]
    
    # Liveness properties
    LIVENESS_PROPERTIES = [
        "termination",
        "progress",
        "timeout",
        "view_change",
        "leader_rotation"
    ]
    
    def __init__(self):
        self.results = []
    
    def analyze_python_file(self, file_path: Path) -> Dict:
        """Analyze a Python file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            info = {
                "path": str(file_path),
                "lines": len(content.split('\n')),
                "classes": [],
                "functions": [],
                "imports": [],
                "consensus_refs": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    info["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    info["functions"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info["imports"].append(node.module)
            
            # Check for consensus components
            content_lower = content.lower()
            for component in self.CONSENSUS_COMPONENTS:
                if component in content_lower:
                    info["consensus_refs"].append(component)
            
            return info
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {"error": str(e)}
    
    def analyze_directory(self, directory: Path) -> Dict:
        """Analyze all Python files in a directory."""
        files_info = []
        total_lines = 0
        all_classes = []
        all_functions = []
        consensus_components_found = set()
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            
            info = self.analyze_python_file(py_file)
            if "error" not in info:
                files_info.append(info)
                total_lines += info["lines"]
                all_classes.extend(info["classes"])
                all_functions.extend(info["functions"])
                consensus_components_found.update(info["consensus_refs"])
        
        return {
            "files": files_info,
            "total_files": len(files_info),
            "total_lines": total_lines,
            "total_classes": len(all_classes),
            "total_functions": len(all_functions),
            "consensus_components": list(consensus_components_found)
        }
    
    def check_safety_properties(self, directory: Path) -> List[str]:
        """Check for implementation of safety properties."""
        found_properties = []
        
        for py_file in directory.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read().lower()
                
                for prop in self.SAFETY_PROPERTIES:
                    if prop in content:
                        found_properties.append(prop)
            
            except Exception as e:
                logger.debug(f"Could not check {py_file}: {e}")
        
        return list(set(found_properties))
    
    def check_liveness_properties(self, directory: Path) -> List[str]:
        """Check for implementation of liveness properties."""
        found_properties = []
        
        for py_file in directory.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read().lower()
                
                for prop in self.LIVENESS_PROPERTIES:
                    if prop in content:
                        found_properties.append(prop)
            
            except Exception as e:
                logger.debug(f"Could not check {py_file}: {e}")
        
        return list(set(found_properties))
    
    def detect_security_issues(self, directory: Path) -> List[Dict]:
        """Detect potential security issues."""
        issues = []
        
        patterns = [
            (r'eval\(', "Use of eval() is dangerous", "high"),
            (r'exec\(', "Use of exec() is dangerous", "high"),
            (r'random\.random\(', "Use cryptographically secure random", "medium"),
            (r'time\.sleep\(\d+\)', "Blocking sleep in async code", "low"),
        ]
        
        for py_file in directory.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                for pattern, message, severity in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            "file": str(py_file.relative_to(directory)),
                            "line": line_num,
                            "severity": severity,
                            "message": message
                        })
            
            except Exception as e:
                logger.debug(f"Could not check {py_file}: {e}")
        
        return issues
    
    def calculate_performance_score(self, code_analysis: Dict) -> int:
        """Calculate performance score based on code analysis."""
        score = 100
        
        # Deduct points for missing consensus components
        expected_components = 6
        found_components = len(code_analysis.get("consensus_components", []))
        if found_components < expected_components:
            score -= (expected_components - found_components) * 5
        
        # Deduct for large files (possible poor organization)
        if code_analysis.get("total_lines", 0) > 5000:
            score -= 10
        
        return max(0, min(100, score))
    
    def calculate_quality_score(self, security_issues: List[Dict]) -> int:
        """Calculate code quality score."""
        score = 100
        
        for issue in security_issues:
            if issue["severity"] == "high":
                score -= 15
            elif issue["severity"] == "medium":
                score -= 10
            else:
                score -= 5
        
        return max(0, score)
    
    def generate_recommendations(self, analysis: Dict, safety: List[str], liveness: List[str]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Check for missing components
        missing_safety = set(self.SAFETY_PROPERTIES) - set(safety)
        if missing_safety:
            recommendations.append(
                f"Implement missing safety properties: {', '.join(missing_safety)}"
            )
        
        missing_liveness = set(self.LIVENESS_PROPERTIES) - set(liveness)
        if missing_liveness:
            recommendations.append(
                f"Implement missing liveness properties: {', '.join(missing_liveness)}"
            )
        
        # Check test coverage
        test_files = sum(1 for f in analysis.get("files", []) if "test" in f["path"])
        total_files = analysis.get("total_files", 0)
        if total_files > 0 and test_files / total_files < 0.3:
            recommendations.append("Increase test coverage to at least 30%")
        
        # Code organization
        if analysis.get("total_lines", 0) > 5000 and analysis.get("total_files", 0) < 10:
            recommendations.append("Consider splitting large files for better organization")
        
        return recommendations
    
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """Analyze a complete repository."""
        logger.info(f"\nAnalyzing repository: {repo_path}")
        
        path = Path(repo_path)
        if not path.exists():
            logger.error(f"Path does not exist: {repo_path}")
            return None
        
        # Analyze code structure
        code_analysis = self.analyze_directory(path)
        
        # Check properties
        safety_props = self.check_safety_properties(path)
        liveness_props = self.check_liveness_properties(path)
        
        # Security analysis
        security_issues = self.detect_security_issues(path)
        
        # Calculate scores
        performance_score = self.calculate_performance_score(code_analysis)
        quality_score = self.calculate_quality_score(security_issues)
        
        # Estimate test coverage (simplified)
        test_files = sum(1 for f in code_analysis.get("files", []) if "test" in f["path"])
        total_files = code_analysis.get("total_files", 0)
        test_coverage = (test_files / total_files * 100) if total_files > 0 else 0
        
        # Generate recommendations
        recommendations = self.generate_recommendations(code_analysis, safety_props, liveness_props)
        
        result = AnalysisResult(
            repo=repo_path,
            language="Python",
            files_analyzed=code_analysis.get("total_files", 0),
            total_lines=code_analysis.get("total_lines", 0),
            consensus_components=code_analysis.get("consensus_components", []),
            safety_properties=safety_props,
            liveness_properties=liveness_props,
            security_issues=security_issues,
            performance_score=performance_score,
            test_coverage=test_coverage,
            code_quality_score=quality_score,
            recommendations=recommendations
        )
        
        self.results.append(result)
        return result
    
    def print_results(self, result: AnalysisResult):
        """Print analysis results in a formatted way."""
        console.print(f"\n[bold cyan]Analysis Results: {result.repo}[/bold cyan]\n")
        
        # Overview table
        overview = Table(title="Overview")
        overview.add_column("Metric", style="cyan")
        overview.add_column("Value", style="yellow")
        
        overview.add_row("Files analyzed", str(result.files_analyzed))
        overview.add_row("Total lines", str(result.total_lines))
        overview.add_row("Language", result.language)
        overview.add_row("Performance score", f"{result.performance_score}/100")
        overview.add_row("Code quality", f"{result.code_quality_score}/100")
        overview.add_row("Test coverage", f"{result.test_coverage:.1f}%")
        
        console.print(overview)
        
        # Components table
        components = Table(title="\nConsensus Components Found")
        components.add_column("Component", style="green")
        
        for comp in result.consensus_components:
            components.add_row(comp)
        
        console.print(components)
        
        # Properties
        console.print(f"\n[bold]Safety Properties:[/bold] {', '.join(result.safety_properties)}")
        console.print(f"[bold]Liveness Properties:[/bold] {', '.join(result.liveness_properties)}")
        
        # Security issues
        if result.security_issues:
            console.print(f"\n[bold red]Security Issues ({len(result.security_issues)}):[/bold red]")
            for issue in result.security_issues[:5]:  # Show first 5
                console.print(f"  [{issue['severity']}] {issue['file']}:{issue['line']} - {issue['message']}")
        
        # Recommendations
        if result.recommendations:
            console.print(f"\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in result.recommendations:
                console.print(f"  • {rec}")
    
    def save_results(self, output_path: str):
        """Save analysis results to JSON."""
        with open(output_path, 'w') as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2
            )
        
        logger.success(f"Results saved to {output_path}")


def main():
    """Example usage."""
    analyzer = MonadBFTAnalyzer()
    
    # Analyze current directory
    result = analyzer.analyze_repository(".")
    
    if result:
        analyzer.print_results(result)
        analyzer.save_results("reports/code_analysis.json")


if __name__ == "__main__":
    main()