import numpy as np
import eMOGA.MOGA_replica_float as M
import matplotlib.pyplot as plt
import math as m


eMOGA=M.eMOGA()
eMOGA.objfun=M.Funcion_analisis_Prueba
eMOGA.Objfun_dim=2
eMOGA.searchspaceLB=np.array([-m.pi,-m.pi])
eMOGA.searchspaceUB=np.array([m.pi,m.pi])
eMOGA.Nind_P= 250
eMOGA.Generations=100
eMOGA.n_div=200*np.ones((eMOGA.Objfun_dim),dtype=int)

Frente,Set,eMOGA=M.evMOGA(eMOGA)

X=Frente[:,0]
Y=Frente[:,1]
plt.plot(X,Y,'r.')

eMOGA.subpobIni=Set
eMOGA.subpobIni_obj=Frente
Frente,Set,eMOGA=M.evMOGA(eMOGA)


X=Frente[:,0]
Y=Frente[:,1]
plt.plot(X,Y,'b.')
plt.show()