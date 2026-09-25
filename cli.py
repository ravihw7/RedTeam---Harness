"""
CLI entrypoint.

Usage:
    python cli.py run
    python cli.py run --suite test_suites/core_suite.yaml --model claude-sonnet-5
    python cli.py run --no-llm-judge
"""

import os

import click
from dotenv import load_dotenv

load_dotenv()

from harness.runner import run_suite  # noqa: E402  (import after load_dotenv)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--suite",
    default="test_suites/core_suite.yaml",
    show_default=True,
    help="Path to the test suite YAML file.",
)
@click.option(
    "--model",
    default=None,
    help="Target model to test. Defaults to TARGET_MODEL from .env.",
)
@click.option(
    "--judge-model",
    default=None,
    help="Model used to grade responses. Defaults to JUDGE_MODEL from .env.",
)
@click.option(
    "--no-llm-judge",
    is_flag=True,
    help="Use fast rule-based keyword checks instead of an LLM judge.",
)
def run(suite, model, judge_model, no_llm_judge):
    """Run a red-team/eval suite against a target model."""
    target_model = model or os.environ.get("TARGET_MODEL", "claude-sonnet-5")
    judge = judge_model or os.environ.get("JUDGE_MODEL", "claude-sonnet-5")

    click.echo(f"Running suite '{suite}' against target model '{target_model}'...")
    run_id = run_suite(
        suite_path=suite,
        target_model=target_model,
        judge_model=judge,
        use_llm_judge=not no_llm_judge,
    )
    click.echo(f"\nRun #{run_id} complete.")
    click.echo("Launch the dashboard with: python web/app.py")


if __name__ == "__main__":
    cli()
