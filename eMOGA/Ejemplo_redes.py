import numpy as np
import eMOGA.MOGA_replica_float_PCruce as M
import matplotlib.pyplot as plt
import eMOGA.Analisis_multiobjetivo as A
import os
import glob
os.environ['CUDA_VISIBLE_DEVICES'] = '0'


eMOGA=M.eMOGA()
eMOGA.objfun=A.Funcion_analisis
eMOGA.Objfun_dim=4
eMOGA.searchSpace_dim=10
eMOGA.searchspaceUB=np.array([512,6,2,32,4,4,4,4,50,1])
eMOGA.searchspaceLB=np.array([8,3,1,8,1,1,1,1,0,1])
eMOGA.Nind_P= 16
eMOGA.Nind_GA=8
eMOGA.Generations=3

Frente,Set,eMOGA=M.evMOGA(eMOGA)
print(Frente[:0])
print(Frente[:1])

X=Frente[:,0]
Y=Frente[:,1]
plt.plot(X,Y,'b.')

# Imagenes = glob.glob(r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_RGB_256x256_Filtradas\Entrenamiento\Pista\*.jpg')
# Vector = A.Ensayo_2(Imagenes, 3)
# print(Vector)

# eMOGA2=M.eMOGA()
# eMOGA2.objfun=M.Funcion_analisis_Prueba
# eMOGA2.Objfun_dim=2
# eMOGA2.searchspaceUB=np.array([m.pi,m.pi])
# eMOGA2.searchspaceLB=np.array([-m.pi,-m.pi])
# eMOGA2.Nind_P= 100
# eMOGA2.Nind_GA=8
# eMOGA2.Generations=100
# Frente,Set,eMOGA=n.evMOGA(eMOGA2)
#
# X=Frente[:,0]
# Y=Frente[:,1]
# plt.plot(X,Y,'r.')
# plt.show()

# Hola=A.Funcion_analisis([64,6,3,8,2,2,2,2,10,10])
# print(Hola)