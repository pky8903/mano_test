import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
from scipy.optimize import fsolve
d=0.08  # um
def decaying_roots(c,M):
    N=2*M+1; coef=np.full(2*M+1,1/N); coef[M]+=c
    r=np.roots(coef[::-1]); return r[np.abs(r)<1]
def boundary_A0(c,M,E=1.0,b=1.0):
    N=2*M+1; r=decaying_roots(c,M); j=np.arange(M)[:,None]
    B=b*(c*r[None,:]**j + (1/N)*(1-r[None,:]**(j+M+1))/(1-r[None,:]))
    C=np.linalg.solve(B,-E*np.eye(M)[:,0])
    cplx=np.abs(r.imag)>1e-12; k=np.argmax(np.where(cplx,np.abs(r),0))
    rs=r[k]; return 2*abs(C[k]), 2*np.pi*d/abs(np.angle(rs)), -np.log(abs(rs))/d, r, C
c,M=0.22,9
A0,L,g,r,C=boundary_A0(c,M)
print(f"theory M=9 c=0.22: A0={A0:.8f}E  gamma={g:.8f}/um  L={L:.8f}um")
print("  doc:            A0=1.35087026E  gamma=0.10720785/um  L=1.06184467um")
# mode-sum vs banded direct solve (old sign: A u = -E delta)
n=4096; N=2*M+1
A=sp.diags([np.full(n-abs(l),1/N) for l in range(-M,M+1)],list(range(-M,M+1)),format='csc')+c*sp.eye(n)
rhs=np.zeros(n); rhs[0]=-1.0; ud=spl.spsolve(A,rhs)
j=np.arange(200); um=np.real((C[None,:]*r[None,:]**j[:,None]).sum(1))
print("  max|mode sum - direct| over j<200:", np.abs(um-ud[:200]).max())
# continuum c=0.22: sin q/q = -c
f=lambda z:[np.real(np.sin(z[0]+1j*z[1])/(z[0]+1j*z[1])+c),np.imag(np.sin(z[0]+1j*z[1])/(z[0]+1j*z[1]))]
a_,b_=fsolve(f,[4.5,0.2]); print(f"continuum: L={2*np.pi/a_:.6f} Rc, gamma={b_:.6f}/Rc  (doc 1.398897, 0.159433)")
