"""Interactive Streamlit dashboard for the 2U CubeSat thermal model.

Run with: streamlit run app.py
"""
from dataclasses import asdict, replace
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from parameters import Parameters, FACE_ORDER
from scenarios import create_scenario
from solver import solve

st.set_page_config(page_title='CubeSat Thermal | Málaga Space Team',
                   page_icon='🛰️', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
    .block-container {max-width: 1480px; padding-top: 1.45rem; padding-bottom: 2.4rem}
    [data-testid="stMetricValue"] {font-size: 1.7rem}
    .mst-corner {position: fixed; right: 22px; bottom: 14px; z-index: 999;
                 font: 600 12px Arial,sans-serif; letter-spacing:.06em;
                 color:#42627a; background:rgba(255,255,255,.9); padding:5px 10px;
                 border-radius:5px}
    .stApp h1, .stApp h2, .stApp h3 {font-family:Arial,sans-serif}
</style>
<div class="mst-corner">MÁLAGA SPACE TEAM</div>''',unsafe_allow_html=True)

st.title('2U CubeSat · Thermal Model')
st.caption('Interactive preliminary analysis  ·  11 temperature nodes  ·  Steady-state 1D conduction network')

@st.cache_data(show_spinner=False, ttl=3600)
def solutions_for(p, sun_angle):
    sun=solve(p,create_scenario(p,True,sun_angle))
    eclipse=solve(p,create_scenario(p,False,sun_angle))
    return sun,eclipse

with st.sidebar:
    st.markdown('### Simulation settings')
    st.caption('Adjust a control to update the results.')

    with st.expander('Orbit & external heating',expanded=True):
        altitude=st.slider('Altitude · km',200,1200,500,25)
        sun_angle=st.slider('Sun direction · ° from +X toward +Y',-90,180,0,5,
                            help='0° means +X faces the Sun. +Y always points toward Earth (nadir).')
        solar=st.slider('Solar irradiance · W/m²',1200,1450,1361,1)
        earth_ir=st.slider('Earth IR flux · W/m²',160,300,237,1)
        albedo=st.slider('Earth albedo · fraction',0.,0.6,0.30,0.01)

    with st.expander('Surface optical properties',expanded=False):
        alpha_al=st.slider('Aluminum solar absorptivity α',0.05,0.95,0.35,0.01)
        epsilon_al=st.slider('Aluminum infrared emissivity ε',0.03,0.98,0.10,0.01)
        alpha_pv=st.slider('PV solar absorptivity α',0.50,1.00,0.90,0.01)
        epsilon_pv=st.slider('PV infrared emissivity ε',0.05,0.98,0.85,0.01)

    with st.expander('Conduction & power',expanded=True):
        r_pv=st.slider('PV effective 1D resistance · K/W',0.1,80.,2.0,0.1,
                       help='Unverified provisional value; not a measured panel/mount resistance.')
        thickness_mm=st.slider('Aluminum thickness · mm',0.5,5.0,2.0,0.1)
        efficiency_pct=st.slider('PV extraction efficiency · %',0,40,29,1,
                                 help='Actual operating-point extraction assumption; not automatic demand.')
        internal_heat=st.slider('Internal dissipation · W',0.0,8.0,1.5,0.1,
                                help='Nominal orbit-averaged power is 1.5 W, assumed constant. Deviations are sensitivity experiments.')

    with st.expander('Advanced coupling sensitivity',expanded=False):
        al_iface=st.slider('Added Al–interior resistance · K/W',0.0,25.0,0.,0.1)
        pv_iface=st.slider('Added PV–interior resistance · K/W',0.0,100.0,0.,0.5)
        st.caption('These are extra idealized resistances, not validated physical interfaces.')

p=replace(Parameters(),altitude_km=float(altitude),solar_flux_W_m2=float(solar),
          earth_ir_W_m2=float(earth_ir),earth_albedo=float(albedo),
          alpha_al=alpha_al,epsilon_al=epsilon_al,alpha_pv=alpha_pv,
          epsilon_pv=epsilon_pv,pv_resistance_K_W=float(r_pv),
          aluminum_thickness_m=thickness_mm/1000.,
          pv_operating_efficiency=efficiency_pct/100.,
          internal_dissipation_W=float(internal_heat),
          aluminum_extra_interface_K_W=float(al_iface),
          pv_extra_interface_K_W=float(pv_iface))
try:
    sun,eclipse=solutions_for(p,float(sun_angle))
except (ValueError,RuntimeError,OverflowError) as exc:
    st.error('The simulation could not be completed with these inputs: '+str(exc))
    st.stop()

if internal_heat!=1.5:
    st.info('The internal heat load is currently a sensitivity override. The agreed reference model uses 1.5 W constant in both cases.')
st.warning('Screening model only: steady-state values are not orbital peak/minimum temperatures. PV-to-interior coupling is idealized; do not use these results as equipment temperature limits.',icon='⚠️')
# Alert when direct sunlight would be geometrically occulted by Earth.
occultation_threshold=np.sqrt(1-(6371.0/(6371.0+altitude))**2)
if np.sin(np.deg2rad(sun_angle)) > occultation_threshold:
    st.info('The chosen Sun direction lies behind the Earth disk for this nadir attitude. The sunlight result is a mathematical what-if; physically the satellite would be in eclipse at this geometry.')

m1,m2,m3,m4=st.columns(4)
m1.metric('Interior · sunlight', f'{sun.interior_C:.2f} °C')
m2.metric('Interior · eclipse', f'{eclipse.interior_C:.2f} °C')
m3.metric('Sunlit PV electricity extracted',f'{sun.summary["electrical_W"]:.2f} W')
m4.metric('Max balance residual',f'{max(sun.max_residual_W,eclipse.max_residual_W):.1e} W')

records=[]
for name,solution in [('Sunlight',sun),('Eclipse',eclipse)]:
    for row in solution.rows:
        records.append({'Scenario':name,'Node':row['node'],
                        'Temperature (°C)':row['temperature_C'],**row})
    records.append({'Scenario':name,'Node':'Interior','Temperature (°C)':solution.interior_C})
results=pd.DataFrame(records)

results_tab,energy_tab,sensitivity_tab=st.tabs(['Temperatures','Heat balance','Sensitivity'])

with results_tab:
    st.subheader('Temperature comparison')
    st.caption('Each lateral face has separate aluminum and PV surface temperatures. The two end faces are aluminum only.')
    temp_plot=px.bar(results,x='Temperature (°C)',y='Node',color='Scenario',
                     barmode='group',orientation='h',
                     category_orders={'Node':[r['node'] for r in sun.rows]+['Interior'],
                                      'Scenario':['Sunlight','Eclipse']},
                     color_discrete_map={'Sunlight':'#D49B35','Eclipse':'#3180A4'},
                     hover_data={'Scenario':True,'Temperature (°C)':':.2f'})
    temp_plot.update_layout(height=530,margin=dict(l=5,r=10,b=20,t=10),
                            legend=dict(orientation='h',y=1.12),
                            yaxis=dict(autorange='reversed'))
    st.plotly_chart(temp_plot,use_container_width=True)
    table=results.pivot(index='Node',columns='Scenario',values='Temperature (°C)')
    table=table.reindex([r['node'] for r in sun.rows]+['Interior'])
    table['Sunlight − eclipse (°C)']=table['Sunlight']-table['Eclipse']
    st.dataframe(table.style.format('{:.2f}'),use_container_width=True)
    st.download_button('Download temperature CSV',data=table.to_csv().encode('utf-8'),
                       file_name='cubesat_temperature_comparison.csv',mime='text/csv')

with energy_tab:
    st.subheader('Whole-spacecraft power budget')
    labels={'solar_W':'Solar absorbed','albedo_W':'Albedo absorbed',
            'earth_ir_W':'Earth IR absorbed','internal_heat_W':'Internal heat',
            'electrical_W':'Electricity extracted','radiation_out_W':'IR emitted'}
    budget=[]
    for phase,sol in [('Sunlight',sun),('Eclipse',eclipse)]:
        for key,label in labels.items():
            budget.append({'Scenario':phase,'Term':label,'Power (W)':sol.summary[key]})
    plot=px.bar(pd.DataFrame(budget),x='Term',y='Power (W)',color='Scenario',
                barmode='group',color_discrete_map={'Sunlight':'#D49B35','Eclipse':'#3180A4'})
    plot.update_layout(height=350,margin=dict(t=20,b=35),legend=dict(orientation='h',y=1.15))
    st.plotly_chart(plot,use_container_width=True)
    col_left,col_right=st.columns(2)
    with col_left:
        st.markdown('**Energy conservation**')
        st.metric('Sunlight global residual',f'{sun.summary["global_residual_W"]:.2e} W')
        st.metric('Eclipse global residual',f'{eclipse.summary["global_residual_W"]:.2e} W')
        st.caption('Absorbed solar + albedo + Earth IR + internal heat − electricity extracted − emitted IR ≈ 0 W.')
    with col_right:
        st.markdown('**Geometry factors**')
        geometry=pd.DataFrame([{'Face':f,
                'Earth view F':sun.scenario.earth_view[f],
                'Sunlit albedo factor b':sun.scenario.albedo_factors[f],
                'Solar incidence c':sun.scenario.incidence[f]} for f in FACE_ORDER]).set_index('Face')
        st.dataframe(geometry.style.format('{:.4f}'),use_container_width=True)
    st.markdown('**Per-surface heat terms**')
    inspected=st.radio('Show scenario',['Sunlight','Eclipse'],horizontal=True,key='term_phase')
    this_solution=sun if inspected=='Sunlight' else eclipse
    cols=['node','solar_W','albedo_W','earth_ir_W','conduction_W','electrical_W',
          'radiation_out_W','residual_W']
    st.dataframe(pd.DataFrame(this_solution.rows)[cols].round(5),use_container_width=True)
    st.download_button('Download surface power CSV',
        data=pd.DataFrame(this_solution.rows).to_csv(index=False).encode('utf-8'),
        file_name=f'cubesat_{inspected.lower()}_surface_power.csv',mime='text/csv')

with sensitivity_tab:
    st.subheader('One-parameter sensitivity')
    st.caption('Change one input at a time while keeping all other parameters fixed. These are hypothetical steady-state comparisons.')
    choices={
        'PV resistance (K/W)':('pv_resistance_K_W',0.2,50.,'K/W'),
        'Aluminum solar absorptivity':('alpha_al',0.10,0.90,'–'),
        'Aluminum infrared emissivity':('epsilon_al',0.05,0.90,'–'),
        'PV solar absorptivity':('alpha_pv',0.55,0.99,'–'),
        'PV infrared emissivity':('epsilon_pv',0.20,0.97,'–'),
        'PV extraction efficiency':('pv_operating_efficiency',0.,0.38,'–'),
        'Earth albedo':('earth_albedo',0.05,0.55,'–'),
        'Solar flux (W/m²)':('solar_flux_W_m2',1200.,1450.,'W/m²'),
        'Orbit altitude (km)':('altitude_km',200.,1200.,'km'),
        'Internal dissipation (W)':('internal_dissipation_W',0.1,6.,'W'),
    }
    selection=st.selectbox('Sweep parameter',list(choices))
    key,minimum,maximum,unit=choices[selection]
    number=st.slider('Simulation points',5,31,13,2)
    if st.button('Calculate sensitivity',type='primary'):
        x=np.linspace(minimum,maximum,number)
        vals=[]
        with st.spinner('Evaluating parameter sweep...'):
            for v in x:
                try:
                    variant=replace(p,**{key:float(v)})
                    a,b=solutions_for(variant,float(sun_angle))
                    vals.extend([{'Parameter':float(v),'Scenario':'Sunlight','Interior (°C)':a.interior_C},
                                 {'Parameter':float(v),'Scenario':'Eclipse','Interior (°C)':b.interior_C}])
                except (ValueError,RuntimeError,OverflowError):
                    continue
        if not vals:
            st.error('No physically valid solution in the requested sweep range.')
        else:
            sweep=pd.DataFrame(vals)
            fig=px.line(sweep,x='Parameter',y='Interior (°C)',color='Scenario',markers=True,
                        color_discrete_map={'Sunlight':'#D49B35','Eclipse':'#3180A4'})
            fig.update_xaxes(title=f'{selection} ({unit})')
            fig.update_layout(height=410,margin=dict(t=20))
            st.plotly_chart(fig,use_container_width=True)
            st.download_button('Download sensitivity CSV',sweep.to_csv(index=False).encode('utf-8'),
                               file_name='cubesat_sensitivity.csv',mime='text/csv')

with st.expander('Model assumptions and export settings',expanded=False):
    st.markdown('''**Model:** ten external surface temperatures (Al and PV separately on four lateral faces, aluminum on two ends), plus one common interior node.

**Environment:** +Y faces Earth (nadir); Sun direction rotates in the +X/+Y plane. Earth view factors are computed by integrating the visible Earth disk. Albedo factors are estimated assuming a uniformly Lambertian-reflecting, sunlit Earth, not measured regional Earth observations.

**Conduction:** 1D through-thickness branches. Panel-to-interior connection is an *idealized boundary assumption*, even though panels are inside openings without an aluminum backing. The 2 K/W starting resistance is illustrative.

**Power:** 1.5 W represents the agreed nominal *orbit-averaged* consumption and is treated as **constant internal heat** for both scenarios. Panel electricity extracted is subtracted separately and depends on the operating efficiency assumption.

**Interpretation:** No orbital timing, heat capacity, interior rear-face radiation, attitude simulation, mounting interfaces or component temperatures. Use parameter studies for screening, not thermal qualification.''')
    st.download_button('Export current parameters (JSON)',json.dumps(asdict(p),indent=2).encode('utf-8'),
                       file_name='cubesat_thermal_parameters.json',mime='application/json')
