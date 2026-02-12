"""grc-engine CLI: compliance scoring for any codebase."""

import sys
from pathlib import Path

import click

from grc_engine import scan
from grc_engine.patterns import get_pattern_detail, load_patterns


@click.group(invoke_without_command=True)
@click.version_option(package_name="grc-engine")
@click.pass_context
def cli(ctx):
    """GRC Engine \u2014 Regulatory compliance scoring for any codebase."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="scan")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--regulation", "-r", help="Filter to a specific regulation (e.g. DORA)")
@click.option(
    "--extensions", "-e", help="Comma-separated file extensions (e.g. .py,.yaml)"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.option(
    "--fail-under",
    type=float,
    help="Exit code 1 if any regulation score below this percentage",
)
def scan_cmd(path, regulation, extensions, output, fmt, fail_under):
    """Scan a codebase for regulatory compliance patterns."""
    ext_list = [e.strip() for e in extensions.split(",")] if extensions else None
    result = scan(path, regulation=regulation, extensions=ext_list)

    if fmt == "json":
        content = result.to_json()
        if output:
            Path(output).write_text(content)
            click.echo(f"Report written to {output}")
        else:
            click.echo(content)
    elif fmt == "markdown":
        content = result.to_markdown()
        if output:
            Path(output).write_text(content)
            click.echo(f"Report written to {output}")
        else:
            click.echo(content)
    else:
        from grc_engine.report import render_scorecard

        render_scorecard(result)
        if output:
            Path(output).write_text(result.to_json())
            click.echo(f"Full report written to {output}")

    # CI/CD quality gate
    if fail_under is not None:
        for reg, score in result.scores.items():
            if score.pct < fail_under:
                click.echo(
                    f"\nFAILED: {reg} score {score.pct:.1f}%"
                    f" < {fail_under}% threshold",
                    err=True,
                )
                sys.exit(1)


@cli.group()
def evidence():
    """Manage the local evidence store."""


@evidence.command(name="init")
@click.option("--db", default="./evidence.db", help="Database file path")
def evidence_init(db):
    """Create the evidence database."""
    from grc_engine.evidence import EvidenceStore

    store = EvidenceStore(db)
    click.echo(f"Evidence store initialized at {store.db_path}")


@evidence.command(name="list")
@click.option("--db", default="./evidence.db", help="Database file path")
@click.option("--limit", default=20, help="Maximum records to show")
def evidence_list(db, limit):
    """Show recorded evidence."""
    from grc_engine.evidence import EvidenceStore

    store = EvidenceStore(db)
    records = store.get_evidence(limit=limit)
    if not records:
        click.echo("No evidence recorded yet. Run 'grc scan' first.")
        return
    for r in records:
        click.echo(
            f"  {r['created_at'][:19]}  {r['control_id']:25s}"
            f"  {r['status']:8s}  {r.get('file_path', '')}"
        )


@evidence.command(name="export")
@click.option("--db", default="./evidence.db", help="Database file path")
@click.option(
    "--format", "fmt", type=click.Choice(["json"]), default="json"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def evidence_export(db, fmt, output):
    """Export evidence for auditors."""
    import json

    from grc_engine.evidence import EvidenceStore

    store = EvidenceStore(db)
    records = store.get_evidence(limit=10000)
    content = json.dumps(records, indent=2, default=str)
    if output:
        Path(output).write_text(content)
        click.echo(f"Exported {len(records)} records to {output}")
    else:
        click.echo(content)


@cli.group()
def patterns():
    """Inspect available compliance patterns."""


@patterns.command(name="list")
@click.option("--regulation", "-r", help="Filter by regulation")
def patterns_list(regulation):
    """List all available patterns."""
    pats = load_patterns(regulation=regulation)
    if not pats:
        click.echo("No patterns found.")
        return

    click.echo(
        f"{'Pattern ID':25s}  {'Control':25s}  {'Regulation':15s}  Label"
    )
    click.echo("-" * 100)
    for p in pats:
        click.echo(
            f"{p['pattern_id']:25s}  {p['control_id']:25s}"
            f"  {p.get('regulation', ''):15s}  {p.get('label', '')}"
        )
    click.echo(f"\nTotal: {len(pats)} patterns")


@patterns.command(name="show")
@click.argument("control_id")
def patterns_show(control_id):
    """Show details for a specific control."""
    pats = get_pattern_detail(control_id)
    if not pats:
        click.echo(f"No patterns found for {control_id}")
        return

    for p in pats:
        click.echo(f"Pattern:     {p['pattern_id']}")
        click.echo(f"Control:     {p['control_id']}")
        click.echo(f"Label:       {p.get('label', '')}")
        click.echo(f"Description: {p.get('description', '')}")
        click.echo(f"Regulation:  {p.get('regulation', '')}")
        click.echo(f"Language:    {p.get('language', 'any')}")
        click.echo(f"Regex:       {p.get('detection_regex', '')}")
        if p.get("example_code"):
            click.echo(f"Example:     {p['example_code']}")
        click.echo()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
