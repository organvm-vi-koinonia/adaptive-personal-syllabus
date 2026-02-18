"""Core module — CLI entry point for adaptive-personal-syllabus."""
from __future__ import annotations

import json

import click

from .generator import SyllabusGenerator
from .models import DifficultyLevel, LearnerProfile


@click.group()
def cli():
    """Adaptive personal syllabus generator."""
    pass


@cli.command()
@click.option("--organs", required=True, help="Comma-separated organ codes (e.g., I,II,V)")
@click.option(
    "--level",
    type=click.Choice(["beginner", "intermediate", "advanced"]),
    default="beginner",
)
@click.option("--name", default="Learner", help="Learner name")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "md"]), default="text")
def generate(organs: str, level: str, name: str, fmt: str):
    """Generate a personalized learning path."""
    organ_list = [o.strip() for o in organs.split(",")]
    profile = LearnerProfile(
        name=name,
        organs_of_interest=organ_list,
        level=DifficultyLevel(level),
    )
    generator = SyllabusGenerator()
    path = generator.generate(profile)

    if fmt == "json":
        data = {
            "path_id": path.path_id,
            "title": path.title,
            "total_hours": path.total_hours,
            "modules": [
                {
                    "module_id": m.module_id,
                    "title": m.title,
                    "organ": m.organ,
                    "difficulty": m.difficulty.value,
                    "readings": m.readings,
                    "questions": m.questions,
                    "estimated_hours": m.estimated_hours,
                }
                for m in path.modules
            ],
        }
        click.echo(json.dumps(data, indent=2))
    elif fmt == "md":
        click.echo(f"# {path.title}\n")
        click.echo(f"**Learner:** {path.learner.name}  ")
        click.echo(f"**Level:** {path.learner.level.value}  ")
        click.echo(f"**Total hours:** {path.total_hours}  ")
        click.echo(f"**Modules:** {path.module_count}\n")
        for i, m in enumerate(path.modules, 1):
            click.echo(f"## {i}. {m.title}")
            click.echo(f"*{m.organ} | {m.difficulty.value} | ~{m.estimated_hours}h*\n")
            if m.readings:
                click.echo("**Readings:**")
                for r in m.readings:
                    click.echo(f"- {r}")
                click.echo()
            if m.questions:
                click.echo("**Questions:**")
                for q in m.questions:
                    click.echo(f"1. {q}")
                click.echo()
    else:
        click.echo(f"Learning Path: {path.title}")
        click.echo(f"Total: {path.module_count} modules, ~{path.total_hours}h\n")
        for i, m in enumerate(path.modules, 1):
            click.echo(
                f"  {i}. [{m.difficulty.value[:3]}] {m.title} ({m.organ}, ~{m.estimated_hours}h)"
            )


@cli.command()
def version():
    """Show version."""
    click.echo("adaptive-personal-syllabus v0.2.0")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
