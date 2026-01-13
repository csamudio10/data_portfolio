from steam_table_generator import Region1, Region2, Region3, Region4
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_saturated_steam_table(T_range = None, P_range = None) -> pd.DataFrame:
    data = []
    if T_range is not None and P_range is not None:
        raise KeyError
    
    if T_range is not None:
        for T in T_range:
            region = Region4(T)
            if not region.in_region():
                raise ValueError ("Temperature {T} is out of the region, please select another one".format(T))
            
            P_sat = Region4(T).calc_P_sat(T)    
            sat_liquid = Region1(T, P_sat).properties()
            sat_vapour = Region2(T, P_sat).properties()
            
            for prop_name in sat_liquid.keys():
                data.append({
                "Temperature" : T,
                "Pressure": P_sat,
                "Property": prop_name,
                "Phase": "Liq",
                "Value": sat_liquid[prop_name]
                })
                data.append({
                    "Temperature" : T,
                    "Pressure": P_sat,
                    "Property": prop_name,
                    "Phase": "Vap",
                    "Value": sat_vapour[prop_name]
                })
        
    if P_range is not None:
        for P in P_range:
            region = Region4(P)
            if not region.in_region():
                raise ValueError ("Pressure {P} is out of the region, please select another one".format(P))
            
            T_sat = Region4(P).calc_T_sat(P)    
            props = region.properties()
            data.append({
                "T": T_sat,
                "P": P,
                "V": props["V"],
                "H": props["H"],
                "S": props["S"],
                "U": props["U"]
            })

    
    df = pd.DataFrame(data)
    return df



T_range = np.linspace(300, 600, 50)  # in Kelvin
P_range = np.linspace(0.1, 30, 50)   # in MPa

steam_table = generate_saturated_steam_table(T_range 
                                             #, P_range
                                             )


print(steam_table.head())

g = sns.FacetGrid(steam_table, col="Phase", sharey=False)  # One plot per phase
g.map(sns.lineplot, "Pressure", "Value")
g.set_titles("{col_name} Phase")
g.set_axis_labels("Pressure (MPa)", "Enthalpy")
g.fig.suptitle("Enthalpy vs Pressure (Liquid & Vapor)", y=1.05)
plt.show()