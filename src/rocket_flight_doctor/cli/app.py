import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
import pandas as pd
from ..parsers import get_parser_for_file
from ..analysis.events import detect_liftoff, detect_burnout, detect_apogee
from ..physics.kinematics import derive_velocity

app = typer.Typer(help="Rocket Flight Doctor - Post-flight autopsy for sport rocketry.")
console = Console()

@app.command()
def inspect(flight_file: Path):
    """
    Inspect a telemetry file and print basic flight info.
    """
    try:
        parser = get_parser_for_file(flight_file)
        df = parser.parse(flight_file)
    except Exception as e:
        console.print(f"[red]Error parsing file: {e}[/red]")
        raise typer.Exit(1)
        
    console.print(f"[green]Successfully parsed {flight_file.name} using {parser.__class__.__name__}[/green]")
    
    # Calculate derived metrics if missing
    if 'altitude_baro_m' in df.columns and 'velocity_z_m_s' not in df.columns:
        df['velocity_z_m_s'] = derive_velocity(df['time_s'].values, df['altitude_baro_m'].values)
        
    liftoff = detect_liftoff(df)
    
    if liftoff:
        # Align time to liftoff
        df['time_s'] = df['time_s'] - liftoff.timestamp_s
        liftoff.timestamp_s = 0.0
        
    burnout = detect_burnout(df, liftoff.timestamp_s if liftoff else 0.0) if liftoff else None
    apogee = detect_apogee(df)
    
    table = Table(title="Flight Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    if 'altitude_baro_m' in df.columns:
        table.add_row("Max Altitude (Baro)", f"{df['altitude_baro_m'].max():.1f} m")
    if 'velocity_z_m_s' in df.columns:
        table.add_row("Max Velocity", f"{df['velocity_z_m_s'].max():.1f} m/s")
    if 'accel_z_m_s2' in df.columns:
        table.add_row("Max Acceleration", f"{df['accel_z_m_s2'].max():.1f} m/s²")
        
    console.print(table)
    
    events_table = Table(title="Key Events")
    events_table.add_column("Event", style="cyan")
    events_table.add_column("Time (s)", style="magenta")
    
    if liftoff:
        events_table.add_row("Liftoff", f"{liftoff.timestamp_s:.2f}")
    if burnout:
        events_table.add_row("Burnout", f"{burnout.timestamp_s:.2f}")
    if apogee:
        events_table.add_row("Apogee", f"{apogee.timestamp_s:.2f}")
        
    console.print(events_table)

@app.command()
def compare(flight_file: Path, sim_file: Path):
    """
    Compare a flight telemetry file with a simulation file.
    """
    console.print(f"Comparing [bold]{flight_file.name}[/bold] to [bold]{sim_file.name}[/bold]...")
    # TODO: Implement full compare logic and display autopsy findings
    
@app.command()
def demo():
    """
    Run a synthetic flight demo to show the capabilities of the doctor.
    """
    console.print("[cyan]Generating synthetic flight data...[/cyan]")
    from ..analysis.synthetic import generate_synthetic_flight
    from ..analysis.autopsy import check_apogee_discrepancy, analyze_coast_drag
    
    act_df, sim_df = generate_synthetic_flight()
    
    # Run some basic event detection
    liftoff = detect_liftoff(act_df)
    burnout = detect_burnout(act_df, liftoff.timestamp_s if liftoff else 0.0) if liftoff else None
    apogee = detect_apogee(act_df)
    
    # Pre-calculate derived velocity for autopsy
    act_df['velocity_z_m_s'] = derive_velocity(act_df['time_s'].values, act_df['altitude_baro_m'].values)
    
    findings = []
    if apogee:
        findings.extend(check_apogee_discrepancy(act_df, sim_df, apogee))
    if burnout and apogee:
        findings.extend(analyze_coast_drag(act_df, sim_df, burnout, apogee))
    if liftoff and burnout:
        from ..analysis.autopsy import check_boost_discrepancy
        findings.extend(check_boost_discrepancy(act_df, sim_df, liftoff, burnout))
        
    console.print("\n[bold]Flight Summary[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value")
    if apogee:
        table.add_row("Measured Apogee", f"{act_df['altitude_baro_m'].max():.1f} m")
    table.add_row("Simulated Apogee", f"{sim_df['altitude_m'].max():.1f} m")
    console.print(table)
    
    console.print("\n[bold]Doctor's Findings (Flight Autopsy)[/bold]")
    for i, finding in enumerate(findings):
        console.print(f"\n[bold yellow]{i+1}. {finding.title}[/bold yellow] (Severity: {finding.severity.value}, Evidence: {finding.evidence_strength.value})")
        console.print(f"{finding.description}")
        if finding.compatible_with:
            console.print("Compatible with:")
            for c in finding.compatible_with:
                console.print(f"  - {c}")

@app.command()
def gui():
    """
    Launch the Rocket Flight Doctor desktop application.
    """
    from ..gui.main_window import launch_gui
    launch_gui()

if __name__ == "__main__":
    app()
