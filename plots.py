"""Portable figures for batch-mode results; interactive app uses Plotly."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def save_figures(sun,eclipse,destination):
    dest=Path(destination)
    dest.mkdir(parents=True,exist_ok=True)
    names=[r['node'] for r in sun.rows]+['Interior']
    y=np.arange(len(names))
    fig,ax=plt.subplots(figsize=(10,6))
    ax.barh(y-0.18, sun.temperatures_K-273.15,height=0.36,label='Sunlight')
    ax.barh(y+0.18,eclipse.temperatures_K-273.15,height=0.36,label='Eclipse')
    ax.set(yticks=y,yticklabels=names,xlabel='Equilibrium temperature (°C)',
           title='2U CubeSat | Preliminary steady-state temperature comparison')
    ax.axvline(0,color='gray',linewidth=0.6)
    ax.legend()
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(dest/'temperature_comparison.png',dpi=170)
    plt.close(fig)

    cols=['solar_W','albedo_W','earth_ir_W','internal_heat_W','electrical_W','radiation_out_W']
    title=['Solar absorbed','Albedo absorbed','Earth IR absorbed','Internal heat',
           'PV electric extracted','Thermal IR emitted']
    a=[sun.summary[k] for k in cols]
    b=[eclipse.summary[k] for k in cols]
    x=np.arange(len(cols))
    fig,ax=plt.subplots(figsize=(11,5))
    ax.bar(x-0.2,a,width=.4,label='Sunlight')
    ax.bar(x+0.2,b,width=.4,label='Eclipse')
    ax.set(xticks=x,xticklabels=title,ylabel='Power (W)',title='Thermal and electrical power budget')
    ax.tick_params(axis='x',rotation=20)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest/'power_budget.png',dpi=170)
    plt.close(fig)
