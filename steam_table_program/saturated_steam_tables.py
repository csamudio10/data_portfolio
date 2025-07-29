import numpy as np
import pandas as pd

from steam_table_generator import SteamRegion, Region1, Region2, Region3, Region4


P_range = np.arange(1/1000,10/1000,1/1000)
T_range = []
V_range = []
H_range = []
S_range = []
U_range = []

for P in P_range:
    T_sat = Region4().calc_T_sat(P)
    T_range.append(T_sat)
    a = Region1(T_sat, P).properties()
    b = Region2(T_sat, P)
    V_range.append(a["V"])
    H_range.append(a["H"])
    S_range.append(a["S"])
    U_range.append(a["U"])
    
    
print(a)