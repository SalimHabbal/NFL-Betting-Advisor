"""Rich terminal UI for NFL Betting Advisor."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from .models import Parlay, EvaluationResult

class RichPresenter:
    def __init__(self):
        self.console = Console()

    def display_parlay_evaluation(self, parlay: Parlay, result: EvaluationResult):
        self.console.print()
        self.console.rule("[bold green]NFL Parlay Advisor[/bold green]")
        self.console.print()

        # 1. Legs Table
        table = Table(box=box.ROUNDED, title="Leg Analysis")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Implied", justify="right", style="magenta")
        table.add_column("Adjusted", justify="right", style="green")
        table.add_column("Delta", justify="right")

        for leg in parlay.legs:
            breakdown = result.leg_breakdown.get(leg.leg_id, {})
            implied = breakdown.get("implied_prob", 0)
            adjusted = breakdown.get("adjusted_prob", leg.adjusted_probability or 0)
            delta = adjusted - implied
            
            delta_str = f"{delta:+.1%}"
            delta_style = "bold green" if delta > 0 else "bold red"
            
            table.add_row(
                leg.leg_id,
                leg.description,
                f"{implied:.1%}",
                f"{adjusted:.1%}",
                f"[{delta_style}]{delta_str}[/{delta_style}]"
            )

        self.console.print(table)
        self.console.print()

        # 2. Summary Panel
        summary_text = f"""
[bold]Verdict:[/bold] {result.verdict}
[bold]Value Score:[/bold] {result.overall_value_score:.2f}
[bold]Expected Value:[/bold] ${result.expected_value:.2f}
[bold]Hit Probability:[/bold] {result.combined_probability:.2%}
"""
        color = "green" if result.overall_value_score > 0 else "yellow"
        if result.overall_value_score < -0.1:
            color = "red"
            
        self.console.print(Panel(summary_text.strip(), title="Summary", border_style=color, expand=False))
        self.console.print()

        # 3. AI Rationale
        # Check if rationale is a single markdown string (LLM) or list of bullets (Heuristic)
        if result.rationale:
            self.console.rule("[bold blue]AI Analysis[/bold blue]")
            self.console.print()
            
            content = result.rationale[0]
            if len(result.rationale) > 1:
                # Fallback for heuristic list
                content = "\n".join(f"- {r}" for r in result.rationale)
            
            md = Markdown(content)
            self.console.print(Panel(md, border_style="blue"))
            self.console.print()
