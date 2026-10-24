"""Run and export the nominal sunlight/eclipse comparison without the GUI."""
from pathlib import Path
import argparse
import json
import csv
from dataclasses import replace,asdict
from parameters import Parameters
from scenarios import create_scenario
from solver import solve
from plots import save_figures


def run(p,angle=0.,output_dir='outputs'):
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    solutions={}
    for name,sunlight in [('sunlight',True),('eclipse',False)]:
        sol=solve(p,create_scenario(p,sunlight,angle))
        solutions[name]=sol
        with (out/f'{name}_surfaces.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(sol.rows[0].keys()))
            w.writeheader()
            w.writerows(sol.rows)
        print(f'{name.capitalize():8s}: interior = {sol.interior_C:9.3f} °C; '
              f'max residual = {sol.max_residual_W:.2e} W')
    with (out/'simulation_summary.json').open('w',encoding='utf-8') as f:
        json.dump({'parameters':asdict(p),
                   'scenarios':{name:{'internal_temperature_C':sol.interior_C,
                                      'powers_W':sol.summary,
                                      'max_residual_W':sol.max_residual_W}
                                for name,sol in solutions.items()}},f,indent=2)
    save_figures(solutions['sunlight'],solutions['eclipse'],out)
    return solutions


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='2U CubeSat: preliminary thermal analysis')
    parser.add_argument('--pv-resistance',type=float,default=2.,help='Assumed PV thermal resistance (K/W)')
    parser.add_argument('--pv-efficiency',type=float,default=.29,help='Operating electrical efficiency, 0-1')
    parser.add_argument('--sun-angle',type=float,default=0.,help='Sun direction, degrees from +X to +Y')
    parser.add_argument('--output',default='outputs',help='Directory for outputs')
    args=parser.parse_args()
    params=replace(Parameters(),pv_resistance_K_W=args.pv_resistance,
                   pv_operating_efficiency=args.pv_efficiency)
    run(params,args.sun_angle,args.output)
