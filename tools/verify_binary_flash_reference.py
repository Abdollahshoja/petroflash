"""Optional independent numerical reference for the test_flash binary fixture.

Requires NumPy and SciPy only when this optional tool is run.
Uses fixed rounded fixture properties, not data/components.json.
This is an independent numerical cross-check, not experimental validation.
"""

import numpy as np
from scipy.optimize import root
R=8.31446261815324;T=250.;P=2e6
Tc=np.array([190.56,425.12]);Pc=np.array([4599200.,3796000.]);omega=np.array([.01142,.2])
m=.37464+1.54226*omega-.26992*omega**2
a=.45724*R**2*Tc**2/Pc*(1+m*(1-np.sqrt(T/Tc)))**2
b=.0778*R*Tc/Pc
aij=np.sqrt(a[:,None]*a[None,:])
def coeff(comp,which):
 am=comp@aij@comp;bm=comp@b;A=am*P/(R*T)**2;B=bm*P/(R*T)
 rs=np.roots([1,B-1,A-2*B-3*B**2,-A*B+B**2+B**3]);rs=sorted(r.real for r in rs if abs(r.imag)<1e-10 and r.real>B)
 Z=rs[which]
 return b/bm*(Z-1)-np.log(Z-B)-A/(2*np.sqrt(2)*B)*(2*(aij@comp)/am-b/bm)*np.log((Z+(1+np.sqrt(2))*B)/(Z+(1-np.sqrt(2))*B))
def f(values):
 x=np.array([values[0],1-values[0]]);y=np.array([values[1],1-values[1]])
 return np.log(x)+coeff(x,0)-np.log(y)-coeff(y,-1)
sol=root(f,[.16,.97],tol=1e-11)
assert sol.success,sol.message
x,y=sol.x;beta=(.5-x)/(y-x)
print('Independent NumPy cubic + SciPy root solver (no PetroFlash imports):')
print('beta',beta,'x_methane',x,'y_methane',y,'residual',max(abs(f(sol.x))))
