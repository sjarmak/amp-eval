#!/usr/bin/env python3
"""
CLI interface for Amp evaluation framework.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import click
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import track

from .amp_runner import AmpRunner


console = Console()


@click.group()
@click.version_option()
@click.option("--config", "-c", default="config/agent_settings.yaml", 
              help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def main(ctx: click.Context, config: str, verbose: bool) -> None:
    """Amp Model Evaluation CLI."""
    # Configure logging
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose


@main.command()
@click.argument("prompt")
@click.option("--workspace", "-w", default=".", help="Workspace path")
@click.option("--model", "-m", help="Override model selection")
@click.option("--try-gpt5", is_flag=True, help="Force GPT-5 model")
@click.option("--diff-lines", type=int, default=0, help="Number of diff lines")
@click.option("--touched-files", type=int, default=0, help="Number of touched files")
@click.option("--output", "-o", help="Output file for results")
@click.pass_context
def eval(ctx: click.Context, prompt: str, workspace: str, model: Optional[str],
         try_gpt5: bool, diff_lines: int, touched_files: int, 
         output: Optional[str]) -> None:
    """Evaluate a single prompt with Amp."""
    config_path = ctx.obj["config"]
    
    try:
        runner = AmpRunner(config_path)
        
        # Prepare CLI args
        cli_args = []
        if try_gpt5:
            cli_args.append("--try-gpt5")
        
        # Override model if specified
        if model:
            import os
            os.environ["AMP_MODEL"] = model
        
        with console.status(f"[bold green]Evaluating with model selection..."):
            result = runner.evaluate(
                prompt, 
                workspace, 
                cli_args,
                diff_lines=diff_lines,
                touched_files=touched_files
            )
        
        # Display results
        _display_result(result)
        
        # Save results if output specified
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"✅ Results saved to {output}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


@main.command()
@click.argument("eval_suite", type=click.Path(exists=True))
@click.option("--workspace", "-w", default=".", help="Workspace path")
@click.option("--output-dir", "-o", default="results", help="Output directory")
@click.option("--parallel", "-p", type=int, default=1, help="Parallel evaluations")
@click.pass_context
def suite(ctx: click.Context, eval_suite: str, workspace: str, 
          output_dir: str, parallel: int) -> None:
    """Run a complete evaluation suite."""
    import yaml
    from datetime import datetime
    
    config_path = ctx.obj["config"]
    
    try:
        # Load evaluation suite
        with open(eval_suite, 'r') as f:
            suite_config = yaml.safe_load(f)
        
        runner = AmpRunner(config_path)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Run evaluations
        results = []
        prompts = suite_config.get("prompts", [])
        
        for prompt_config in track(prompts, description="Running evaluations..."):
            prompt = prompt_config["prompt"]
            expected = prompt_config.get("expected", {})
            
            result = runner.evaluate(prompt, workspace)
            result["expected"] = expected
            result["timestamp"] = datetime.utcnow().isoformat()
            results.append(result)
        
        # Save aggregated results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        _display_suite_summary(results)
        console.print(f"✅ Results saved to {output_file}")
        
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


@main.command()
@click.option("--config", help="Override config path")
@click.pass_context
def validate_config(ctx: click.Context, config: Optional[str]) -> None:
    """Validate configuration file."""
    config_path = config or ctx.obj["config"]
    
    try:
        runner = AmpRunner(config_path)
        console.print("✅ Configuration is valid", style="bold green")
        
        # Display config summary
        table = Table(title="Configuration Summary")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Default Model", runner.config["default_model"])
        table.add_row("Oracle Trigger", runner.config["oracle_trigger"]["phrase"])
        table.add_row("Rules Count", str(len(runner.config.get("rules", []))))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Configuration error: {e}", style="bold red")
        sys.exit(1)


def _display_result(result: Dict[str, Any]) -> None:
    """Display evaluation result in a formatted table."""
    table = Table(title="Evaluation Result")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    # Status indicator
    status = "✅ Success" if result["success"] else "❌ Failed"
    table.add_row("Status", status)
    table.add_row("Model", result["model"])
    table.add_row("Latency", f"{result['latency_s']}s")
    table.add_row("Tokens", str(result["tokens"]))
    
    if not result["success"]:
        table.add_row("Error", result.get("error", "Unknown error"))
    
    console.print(table)


def _display_suite_summary(results: list) -> None:
    """Display evaluation suite summary."""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    
    table = Table(title="Evaluation Suite Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Evaluations", str(total))
    table.add_row("Successful", str(successful))
    table.add_row("Failed", str(total - successful))
    table.add_row("Success Rate", f"{(successful/total)*100:.1f}%")
    
    # Model distribution
    models = {}
    for result in results:
        model = result["model"]
        models[model] = models.get(model, 0) + 1
    
    for model, count in models.items():
        table.add_row(f"Used {model}", str(count))
    
    console.print(table)


if __name__ == "__main__":
    main()
