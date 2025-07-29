import csv
import numpy as np

class SteamRegion:
    def __init__(self, T: float, p: float):
        self.T = T  # temperature in K
        self.P = p  # pressure in MPa
        self.R = 0.461526 # kJ kg-1 K-1.
        self.P_crit = 22.064 # MPa
        self.T_crit = 647.096 # K
        self.rho_crit = 322 # kg m^-3

    def gamma(self):
        raise NotImplementedError

    def properties(self):
        """Return dict with v, h, s, u, cp, w"""
        raise NotImplementedError

    def in_region(self):
        """Return True if T and p fall within this region"""
        raise NotImplementedError

    def region23_line(self, T: float = 1.0, P: float = 1.0):
        P_star = 1 # [MPa]
        T_star = 1 # [K]
        n1 = 0.34805185628969e3
        n2 = -0.11671859879975e1
        n3 = 0.10192970039326e-2
        n4 = 0.57254459862746e3
        n5 = 0.13918839778870e2
        
        theta = T/T_star
        P = (n1 + n2*theta + n3*theta**2) * P_star
        
        pi = P / P_star
        T = (n4 + ((pi - n5) / n3)**0.5) * T_star
        
        return (T, P)


class Region1(SteamRegion):
    COEFFICIENTS = []

    @classmethod
    def load_coefficients(cls, filename="region1_constants.csv"):
        if not cls.COEFFICIENTS:  # Load only once
            with open(filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    n = float(row['n'])
                    I = int(row['I'])
                    J = int(row['J'])
                    cls.COEFFICIENTS.append((n, I, J))

    def __init__(self, T: float, p: float):
        super().__init__(T, p)
        self.pi = p / 16.53
        self.tau = 1386 / T
        self.load_coefficients()
    
    
    def gamma(self):
        # Compute γ and derivatives
        gamma = sum(n * (7.1 - self.pi)**I * (self.tau - 1.222)**J
                    for n, I, J in self.COEFFICIENTS)
        
        d_gamma_d_pi = sum(-n * I *(7.1 - self.pi) ** (I - 1) * (self.tau - 1.222) ** J
                           for n, I, J in self.COEFFICIENTS)
        
        d2_gamma_d_tau = sum(n * (7.1 - self.pi) ** I * J * (self.tau - 1.222) ** (J - 1)
                           for n, I, J in self.COEFFICIENTS)
        
        d2_gamma_d_pi2 = sum(n * I * (I - 1) * (7.1 - self.pi) ** (I - 2) * (self.tau - 1.222) ** J
                           for n, I, J in self.COEFFICIENTS)
        
        d2_gamma_d_tau2 = sum(n * (7.1 - self.pi) ** I * J * (J-1) * (self.tau - 1.222) **(J - 2)
                              for n, I, J in self.COEFFICIENTS)
        
        return {
                "gamma" : gamma,
                "d_pi" : d_gamma_d_pi,
                "d_tau" : d2_gamma_d_tau,
                "dpi2" : d2_gamma_d_pi2,
                "dtau2" : d2_gamma_d_tau2
                }

    def properties(self):
        gammas = self.gamma()
        
        V = self.R * self.T /(self.P * 1000) * self.pi * gammas["d_pi"]
        
        U = self.R * self.T * (self.tau * gammas['d_tau'] - self.pi * gammas['d_pi'])
        
        S = self.R * (self.tau * gammas['d_tau'] - gammas['gamma'])
        
        H = self.R * self.T * self.tau * gammas['d_tau']
        # Return v, h, s, u, cp, w
        return {
            'V' : V,
            'H' : H,
            'S' : S,
            'U' : U
        }
    
    def in_region(self):
        # Check Region 1 limits
        return (273.15 <= self.T <= 623.15) and (self.P <= Region4.calc_P_sat(self.T))


class Region2(SteamRegion):
    IG_COEFFICIENTS = []
    RESID_COEFFICIENTS = []

    @classmethod
    def load_ideal_gas_coefficients(cls, filename="region2_constants_ideal_gas.csv"):
        if not cls.IG_COEFFICIENTS:  # Load only once
            with open(filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    n = float(row['n'])
                    J = int(row['J'])
                    cls.IG_COEFFICIENTS.append((n, J))
                    
    @classmethod
    def load_residual_coefficients(cls, filename="region2_constants_residuals.csv"):
        if not cls.RESID_COEFFICIENTS:  # Load only once
            with open(filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    n = float(row['n'])
                    I = int(row['I'])
                    J = int(row['J'])
                    cls.RESID_COEFFICIENTS.append((n, I, J))

    def __init__(self, T, p):
        super().__init__(T, p)
        self.pi = p / 1
        self.tau = 540 / T
        self.load_ideal_gas_coefficients()
        self.load_residual_coefficients()

    def gamma(self):
        # Compute γ and derivatives
        # gammas
        gamma_ig = np.log(self.pi) + sum(n * self.tau ** J
                    for n, J in self.IG_COEFFICIENTS)
        
        gamma_resid = sum(n * self.pi ** I * (self.tau - 0.5) ** J 
                      for n, I, J in self.RESID_COEFFICIENTS)
        
        gamma = gamma_ig + gamma_resid
        
        # ideal gas gamma derivatives
        d_gamma_ig_d_pi = 1 / self.pi
        d2_gamma_ig_d_pi2 = -1 / (self.pi ** 2)
        
        d_gamma_ig_d_tau = sum(n * J * self.tau ** (J - 1)
                                for n, J in self.IG_COEFFICIENTS)
        d2_gamma_ig_d_tau2 = sum(n * J * (J - 1) * self.tau ** (J - 2)
                                 for n, J in self.IG_COEFFICIENTS)
        
        # residual gamma derivatives
        d_gamma_resid_d_pi = sum(n * I * self.pi ** (I - 1) * (self.tau - 0.5) ** J
                                 for n, I, J in self.RESID_COEFFICIENTS)
        d2_gamma_resid_d_pi2 = sum(n * I * (I - 1) * self.pi ** (I - 2) * (self.tau - 0.5) ** J
                                   for n, I, J in self.RESID_COEFFICIENTS)
        
        d_gamma_resid_d_tau = sum(n * self.pi ** I * J * (self.tau - 0.5) ** (J - 1)
                                  for n, I, J in self.RESID_COEFFICIENTS)
        d2_gamma_resid_d_tau2 = sum(n * self.pi ** I * J * (J - 1) * (self.tau - 0.5) ** (J - 2)
                                  for n, I, J in self.RESID_COEFFICIENTS)
        
        return {
                "gamma" : gamma,
                "ig_dpi" : d_gamma_ig_d_pi,
                "ig_dpi2" : d2_gamma_ig_d_pi2,
                "ig_dtau" : d_gamma_ig_d_tau,
                "ig_dtau2" : d2_gamma_ig_d_tau2,
                "resid_dpi" : d_gamma_resid_d_pi,
                "resid_dpi2" : d2_gamma_resid_d_pi2,
                "resid_dtau" : d_gamma_resid_d_tau,
                "resid_dtau2" : d2_gamma_resid_d_tau2
                }

    def properties(self):
        gammas = self.gamma()
        
        V = self.R * self.T /(self.P * 1000) * self.pi * (gammas["ig_dpi"] + gammas['resid_dpi'])
        
        U = self.R * self.T * (self.tau * (gammas['ig_dtau'] + gammas['resid_dtau']) - self.pi * (gammas['ig_dpi'] + gammas['resid_dpi']))
        
        S = self.R * (self.tau * (gammas['ig_dtau'] + gammas['resid_dtau']) - gammas['gamma'])
        
        H = self.R * self.T * self.tau * (gammas['ig_dtau'] + gammas['resid_dtau'])
        
        # Return v, h, s, u, cp, w
        return {
            'V' : V,
            'H' : H,
            'S' : S,
            'U' : U
        }

    def in_region(self):
        # Check Region 2 limits
        valid = False
        
        if (273.15 <= self.T <= 623.15) and (0 <= self.P <= Region4.calc_P_sat(self.T)):
            valid = True
        
        if (623.15 <= self.T <= 863.15) and (0 <= self.P <= self.region23_line(self.T)[1]):
            valid = True
        
        if (863.15 <= self.T <= 1073.15) and (0 <= self.P <= 100):
            valid = True
        
        return valid
    

class Region3(SteamRegion):
    COEFFICIENTS = []
    
    @classmethod
    def load_coefficients(cls, filename="region2_constants_ideal_gas.csv"):
        if not cls.COEFFICIENTS:  # Load only once
            with open(filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    n = float(row['n'])
                    J = int(row['J'])
                    cls.COEFFICIENTS.append((n, J))

    def __init__(self, T, p, rho):
        super().__init__(T, p)
        self.rho = rho
        self.delta = rho / self.rho_crit
        self.tau = self.T_crit / T
        self.load_coefficients()

    def phi(self):

        n1 = 1.0658070028513
        
        phi = n1 * np.log(self.delta * sum(n * self.delta**I * self.tau**J
                                                   for n, I, J in self.COEFFICIENTS)
                                       )

        d_phi_d_delta =  n1 / (self.delta + sum(n * I * self.delta**(I-1) * self.tau**J
                                           for n, I, J in self.COEFFICIENTS))
        
        d_phi_d_tau = sum(n * self.delta**I * J * self.tau**(J-1)
                                           for n, I, J in self.COEFFICIENTS)
        
        d2_phi_d_delta2 = -n1 / (self.delta**2 + sum(n * I * (I - 1) * self.delta**(I - 2) * self.tau**J
                                           for n, I, J in self.COEFFICIENTS))
        
        d2_phi_d_tau2 = sum(n * self.delta**I * J * (J-1) * self.tau**(J-2)
                                           for n, I, J in self.COEFFICIENTS)

        return {
                "phi" : phi,
                "d_phi_d_delta" : d_phi_d_delta,
                "d_phi_d_tau" : d_phi_d_tau,
                "d2_phi_d_delta2" : d2_phi_d_delta2,
                "d2_phi_d_tau2" : d2_phi_d_tau2
                }
        
    def properties(self):
        phis = self.phi()
        
        P = self.delta * phis["d_phi_d_delta"] * self.rho * self.R * self.T
        
        U = self.tau * phis["d_phi_d_tau"] * self.R * self.T
        
        S = (self.tau*phis["d_phi_d_tau"] - phis["phi"]) * self.R
        
        H = (self.tau*phis["d_phi_d_tau"] + self.delta * phis["d_phi_d_delta"]) * self.R * self.T

                # Return v, h, s, u, cp, w
        return {
            'P' : P,
            'H' : H,
            'S' : S,
            'U' : U
        }

    def in_region(self):
        # Check Region 1 limits
        T_limit, P_limit = self.region23_line(self.T, self.P)
        return (623.15 <= self.T <= T_limit) and (P_limit <= self.P <= 100)


class Region4(SteamRegion):
    # Class-level constants (accessible via cls)
    P_star = 1.0  # MPa
    T_star = 1.0  # K
    
    n1 = 0.11670521452767e4
    n2 = -0.72421316703206e6
    n3 = -0.17073846940092e2
    n4 = 0.12020824702470e5
    n5 = -0.32325550322333e7
    n6 = 0.14915108613530e2
    n7 = -0.48232657361591e4
    n8 = 0.40511340542057e6
    n9 = -0.23855557567849
    n10 = 0.65017534844798e3

    def __init__(self, T=1.0, P=1.0):
        super().__init__(T, P)

    @classmethod
    def calc_P_sat(cls, T_sat: float):
        theta = T_sat / cls.T_star
        gamma = theta + cls.n9 / (theta - cls.n10)
        
        A = gamma**2 + cls.n1 * gamma + cls.n2
        B = cls.n3 * gamma**2 + cls.n4 * gamma + cls.n5
        C = cls.n6 * gamma**2 + cls.n7 * gamma + cls.n8
        
        sqrt_term = (B**2 - 4 * A * C) ** 0.5
        P_sat = ((2 * C) / (-B + sqrt_term))**4 * cls.P_star
        
        return P_sat

        
    @classmethod
    def calc_T_sat(cls, P_sat: float):
        beta = (P_sat / cls.P_star) ** 0.25
        
        E = beta**2 + cls.n3*beta + cls.n6
        
        F = cls.n1*beta**2 + cls.n4*beta + cls.n7
        
        G = cls.n2*beta**2 + cls.n5*beta + cls.n8
        
        D = 2*G / (-F - (F**2 -4*E*G)**0.5)
        
        T_sat = (cls.n10 + D - ((cls.n10 + D)**2 - 4*(cls.n9 + cls.n10*D))**0.5)/2 * cls.T_star
        
        return T_sat





if __name__ == "__main__":
    a = Region2(100+273.15, 0.10141797792131013)
    props = a.properties()
    print(props)
    # print(f"Specific Volume: {props['V']:.10f} m³/kg")    

    b = Region4()
    print(b.calc_P_sat(100+273.15))
    print(b.calc_T_sat(0.10141797792131013))

