import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
d=80.0
def roots(a,b,M):
    N=2*M+1
    # r^M * (a + b/N sum r^l) = 0 -> poly in r of degree 2M
    c=np.full(2*M+1,b/N); c[M]+=a
    r=np.roots(c[::-1])
    dec=r[(np.abs(r)<1-1e-12)&(np.abs(r.imag)>1e-12)]
    k=dec[np.argmax(np.abs(dec))]
    th=abs(np.angle(k)); rho=abs(k)
    return 2*np.pi*d/th, -np.log(rho)/d*1000, rho  # period nm, gamma per um
def A_op(a,b,M,n):
    N=2*M+1
    diags=[np.full(n-abs(l),b/N) for l in range(-M,M+1)]
    A=sp.diags(diags,list(range(-M,M+1)),format='csr')+a*sp.eye(n)
    return A
def wmin(M):
    k=np.linspace(1e-6,np.pi,200001); N=2*M+1
    return (np.sin(N*k/2)/(N*np.sin(k/2))).min()
for M in [9,12,13,18,24]:
    print("M",M,"Wmin",round(wmin(M),4))
for ab in [0.25,0.3,0.35,0.5,1.0]:
    print("a/b",ab, [ (M,)+tuple(np.round(roots(ab,1,M)[:2],3)) for M in [9,12,13,18,24]])
print("--- near finite-stencil threshold")
for ab in [0.2196,0.22,0.221,0.223]:
    print(ab,[(M,)+tuple(np.round(roots(ab,1,M)[:2],3)) for M in [9,12]])
print("--- P iteration, E = delta at j=0")
for ab,M in [(0.25,9),(0.3,9),(0.3,13)]:
    a,b=ab,1.0; n=4096; A=A_op(a,b,M,n); E=np.zeros(n); E[0]=1.0
    us=spl.spsolve(A.tocsc(),E); u=np.zeros(n); eta=1/(a+b)
    for it in range(1,20000):
        e=E-A@u; u=u+eta*e
        if np.abs(E-A@u).max()<1e-10*abs(E).max(): break
    x=np.arange(n)*d/1000; w=(x>=0.8)&(x<=8)
    print(ab,M,"iters",it,"|u-u*|",np.abs(u-us).max(),"u0",us[0],"ptp(0.8-8um)",np.ptp(us[w]), "ptp 3-8", np.ptp(us[(x>=3)&(x<=8)]))
