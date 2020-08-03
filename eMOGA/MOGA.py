from pylab import *
import random
import Analisis_multiobjetivo as A
import numpy as np

def Creacion_inicial(Numero_miembros,Lim_inf,Lim_sup,Dimensiones): #Crea aleatoriamente N miembros de poblacion
    Poblacion=[]
    for x in range(Numero_miembros):
        Vector=np.random.randint(Lim_inf,Lim_sup,Dimensiones)
        Vector_solucion=A.Funcion_analisis_Prueba(Vector)
        Poblacion.append(A.Individuo(Vector,Vector_solucion))
    return Poblacion

def Evaluar_Ind(Individuo_1,Individuo_2): #Comprueba que el vector esta o no dominado por otro
    solucion = np.subtract(Individuo_1.Coste, Individuo_2.Coste)
    respuesta = False
    for x in solucion:
        if x > 0:
            respuesta = False
            break
        if x < 0:
            respuesta = True
    return respuesta

def Guardar(Poblacion_origen,Poblacion_destino): #Guarda los miembros NO-Dominados en la poblacion de destino
    Lista_eliminados=[]
    for x in range(len(Poblacion_origen)):
       for y in range(len(Poblacion_origen)):
           Domina=Evaluar_Ind(Poblacion_origen[y],Poblacion_origen[x])
           if Domina==True and x not in Lista_eliminados:
               Lista_eliminados.append(x)
    Lista_eliminados.reverse()
    for x in Lista_eliminados:
        Poblacion_origen.pop(x)
    for x in Poblacion_origen:
        Poblacion_destino.append(x)
    return Poblacion_destino

def Cruce(Individuo_1,Individuo_2,Dimensiones): #Se cruzan los miembros recibidos
    Individio_hijo=A.Individuo([0],[0])
    Vector_hijo=[]
    Punto_cruce=random.randint(1,Dimensiones)
    #Padre 1
    for x in range(Punto_cruce):
        Vector_hijo.append(Individuo_1.Instancia[x])
    #Padre 2
    for x in range(Punto_cruce,Dimensiones):
        Vector_hijo.append(Individuo_2.Instancia[x])
    Individio_hijo.Instancia=Vector_hijo
    return Individio_hijo

def Mutacion(Individuo,Dimensiones): #Se muta el vector recibido
    Punto_mutacion = random.randint(0, Dimensiones-1)
    print(Punto_mutacion,'Punto_mutacion')
    Individuo.Instancia[Punto_mutacion]=random.randint(1,10)
    return Individuo


def Creacion(Poblacion_origen1,Poblacion_origen2,Poblacion_destino,Probabilidad_cruce,Probabilidad_mutacion,Dimensiones): # Creamos la poblacion a partir de las dos poblaciones recibidos
    for x in range(int(len(Poblacion_origen1)/2)):
        Indice_1=random.randint(0,(len(Poblacion_origen1)-1))
        Indice_2=random.randint(0,(len(Poblacion_origen2)-1))
        Individuo_1=Poblacion_origen1[Indice_1]
        Individuo_2=Poblacion_origen2[Indice_2]
        cruce=random.random()
        mutacion=random.random()
        if cruce>Probabilidad_cruce:
            Individuo_1=Cruce(Individuo_1,Individuo_2,Dimensiones)
            Individuo_2 = Cruce(Individuo_2, Individuo_1,Dimensiones)
        if mutacion>Probabilidad_mutacion:
            Individuo_1=Mutacion(Individuo_1,Dimensiones)
            Individuo_2=Mutacion(Individuo_2,Dimensiones)
        Individuo_1.Coste=A.Funcion_analisis_Prueba(Individuo_1.Instancia)
        Individuo_2.Coste = A.Funcion_analisis_Prueba(Individuo_2.Instancia)
        Poblacion_destino.append(Individuo_1)
        Poblacion_destino.append(Individuo_2)
    return Poblacion_destino

def Limpiar_poblacion(Poblacion_sucia):
    Poblacion_limpia=[]
    return Poblacion_limpia


class evMOGA():
    Poblacion_inicial=10
    N_dimensiones=2
    N_Iteraciones=10
    N_Divisiones=10
    Poblacion_GA=8
    Subpoblacion=0
    Subpoblacion_objetivo=0
    Probabilildad_Cruce=0.25
    Probabilildad_mutacion=0.25
    Limite_inf_espacio_busqueda = 0
    Limite_sup_espacio_busqueda=100
    def iteracion(self):
        P_instancia = []
        A_instancia = []
        G_instancia = []
        P_instancia = Creacion_inicial(self.Poblacion_inicial, self.Limite_inf_espacio_busqueda, self.Limite_sup_espacio_busqueda, self.N_dimensiones)
        Guardar(P_instancia, A_instancia)
        for iteraciones in range(self.N_Iteraciones):
            Creacion(P_instancia, A_instancia, G_instancia,self.Probabilildad_Cruce, self.Probabilildad_mutacion, self.N_dimensiones)
            Guardar(G_instancia, A_instancia)
        Vector_x = []
        Vector_y = []
        for Individuo in A_instancia:
            Vector_x.append(Individuo.Coste[0])
            Vector_y.append(Individuo.Coste[1])
        p1 = plot(Vector_x, Vector_y, 'o')
        show()



#Prueba funcion cruce
# Vector_1=[1,1,1,1,1,1,1,1]
# Vector_2=[2,2,2,2,2,2,2,2]
# Vector_3=Cruce(Vector_1,Vector_2,0)
# print(len(Vector_1))
# print(len(Vector_3))
# print(Vector_3)

#Prueba creacion
# P1=Creacion_inicial(6,2)
# P2=Creacion_inicial(6,2)
# print(P1)
# print(P2)
# P3=[]
# P3=Creacion(P1,P2,P3,3,1,1)
# print(len(P3))
# print(P3)

#Cruce
# Objeto1=A.Individuo([1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1])
# Objeto2=A.Individuo([2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2])
# print(Cruce(Objeto1,Objeto2,9).Instancia)

# Mutacion
# Objeto1=A.Individuo([1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1])
# print(Mutacion(Objeto1,9).Instancia)
