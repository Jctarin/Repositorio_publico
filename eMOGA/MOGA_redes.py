import numpy as np
import random as rd
import math as M





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------OBJETO eMOGA--------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

class eMOGA():
    objfun = 0  # Funcion objetivo
    Objfun_dim = 2  # Dimensiones del espacio objetivo
    searchSpace_dim = 2  # Dimensiones espacio de busqueda
    searchspaceUB = np.ones((Objfun_dim))  # Limite superior del espacio de busqueda
    searchspaceLB = np.ones((Objfun_dim))  # Limite inferior del espacio de busqueda
    # param=0 #Objetivos adicionales
    Nind_P = 100  # Numero de individuos en la poblacion P
    Generations = 100  # Numero de generaciones
    n_div = 50 * np.ones((Objfun_dim), dtype=int)  # Divisiones por dimension para construir la rejilla
    Nind_GA = 8  # Individuos de la poblacion auxiliar GA
    subpobIni = np.empty((1, searchSpace_dim))  # Subpoblacion inicial
    subpobIni_obj = np.empty((1, Objfun_dim))  # Valores objetivo para la subpoblacion inicial
    dd_ini = 0.25  # Parametro para crossover
    dd_fin = 0.1  # Parametro para crossover
    Pm = 0.2  # Parametro para la mutacion
    Sigma_Pm_ini = 20  # Parametro para la mutacion
    Sigma_Pm_fin = 0.1  # Parametro para la mutacion
    epsilon = np.ones((Objfun_dim), dtype=float)  # Tamaño de las cajas
    max_f = np.ones((Objfun_dim), dtype=int)  # Maximo valor objetivo de cada dimension
    min_f = np.ones((Objfun_dim), dtype=int)  # Minimo valor objetivo de cada dimension
    ele_P = np.ones((Nind_P, searchSpace_dim), dtype=int)  # Poblacion P
    coste_P = np.ones((Nind_P, Objfun_dim), dtype=int)  # Valores objetivos de la poblacion P
    mod = np.ones((Nind_P), dtype=int)  # Parametro de dominancia
    ele_A = np.ones((1, searchSpace_dim), dtype=int)  # Poblacion A
    coste_A = np.ones((1, Objfun_dim), dtype=int)  # Valores objetivo de la poblacion A
    box_A = np.ones((1, Objfun_dim), dtype=int)  # Caja para el individuo A
    Nind_A = 0  # Tamaño del frente de pareto
    ele_GA = np.ones((Nind_GA, searchSpace_dim), dtype=int)  # Individuos de la poblacion GA
    coste_GA = np.ones((Nind_GA, Objfun_dim), dtype=int)  # Valores objetivo de la poblacion GA
    box_GA = np.ones((Nind_GA, Objfun_dim), dtype=int)  # Caja para el individuo GA
    gen_counter = 2  # Contador de generaciones




#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------CALCULA BOX---------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Calcula_box(eMOGA,coste): #Funcion que determina en que caja debe estar cada dimension del vector de costes que recibe
    box=np.zeros((eMOGA.Objfun_dim),dtype=int) #Inicializa la matriz de cajas
    for i in range(eMOGA.Objfun_dim): #Analiza cada dimension del espacio objetivo
        if eMOGA.epsilon[i]==0: #Si el valor del ancho de caja (epsilon) es 0 determina que pertenece a la primera caja
            box[i]=0
        else: #En caso que no sea 0 Calcula la caja a la que pertenece
            box[i]=round((coste[i]-eMOGA.min_f[i])/eMOGA.epsilon[i]) #Divide la distancia entre el coste y el limite inferior en regiones del ancho de caja (epsilon)
    return np.array([box]) #Devuelve un vector con las cajas para cada dimension del espacio objetivo





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------DOMINA--------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def domina(f,g): #Funcion que determina la dominancia entre dos individuos recibiendo sus vectores de costes (f,g)
    a=0
    b=0
    for i in range(len(f)): #Para cada elemento del vector de costes, se asume que f y g tienen el mismo tamaño
        if f[i]<g[i]: #Si en la posicion i-esima f domina a g (es menor) se marca
            a=1
        elif f[i]>g[i]: #Si en la posicion i-esima g domina a f (es menor) se marca
            b=1
    aux=3-a*2-b #Los posibles valores de aux son : 0 --> No se dominan entre ellos, 1-->f domima a g, 2--> g domina a f, 3--> son el mismo individuo
    return aux





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------BOX DOMINA----------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def box_domina(box_f, box_g):
    a=0
    b=0
    for i in range(np.size(box_f)):
        if box_f[i]<box_g[i]:
            a=1
        elif box_f[i]>box_g[i]:
            b=1
    aux=3-a*2-b
    return aux





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------ARCHIVAR------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Archivar(eMOGA,x,coste_f,box_f):
    j = 0
    while (j < eMOGA.Nind_A):
        a = box_domina(box_f, eMOGA.box_A[j])
        if(a == 2):
            return eMOGA
        elif(a == 0):
            j = j + 1
            continue
        elif(a == 3):
            b = domina(coste_f, eMOGA.coste_A[j])
            if b==0:
                aux_1=(coste_f - ((box_f - 0.5)* eMOGA.epsilon + eMOGA.min_f))#/eMOGA.epsilon
                aux_2=(eMOGA.coste_A[j] - ((box_f - 0.5)* eMOGA.epsilon + eMOGA.min_f))#/eMOGA.epsilon
                dist1 = np.linalg.norm(aux_1)
                dist2 = np.linalg.norm(aux_2)
                if (dist1 < dist2):
                    eMOGA.ele_A[j]=x
                    eMOGA.coste_A[j]=coste_f
                return eMOGA
            elif b==1:
                eMOGA.ele_A[j]=x
                eMOGA.coste_A[j]=coste_f
                return eMOGA
            elif b==2 or b==3:
                return eMOGA
        else:
            if j < eMOGA.Nind_A-1:
                eMOGA.ele_A = np.delete(eMOGA.ele_A, j, axis=0)
                eMOGA.box_A = np.delete(eMOGA.box_A, j, axis=0)
                eMOGA.coste_A = np.delete(eMOGA.coste_A, j, axis=0)
                eMOGA.Nind_A = eMOGA.Nind_A - 1
            eMOGA.ele_A = np.delete(eMOGA.ele_A, eMOGA.Nind_A-1, axis=0)
            eMOGA.box_A = np.delete(eMOGA.box_A, eMOGA.Nind_A-1, axis=0)
            eMOGA.coste_A = np.delete(eMOGA.coste_A, eMOGA.Nind_A-1, axis=0)
            eMOGA.Nind_A = eMOGA.Nind_A - 1
            j = j - 1
        j = j + 1
    eMOGA.ele_A=np.append(eMOGA.ele_A,np.array([x]),axis=0)
    eMOGA.coste_A=np.append(eMOGA.coste_A, np.array([coste_f]), axis=0)
    eMOGA.box_A=np.append(eMOGA.box_A,np.array([box_f]), axis=0)
    eMOGA.Nind_A = eMOGA.Nind_A + 1
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------ITERACION MOEA------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Iteracion_MOEA(eMOGA, gen_counter):
    eMOGA.gen_counter = gen_counter #Actualiza el contador de generacion
    if gen_counter == 0: #Primera generacion
        for i in range(eMOGA.Nind_P - 1): #Para todos los elementos de P SALVO el ULTIMO
            if eMOGA.mod[i] is not 1: #Siempre que el individuo no este ya marcado como dominado se procede a su inspeccion
                for j in range((i + 1), eMOGA.Nind_P): #Se compara con todos los elementos que esten por encima del elegido anteriormente para compararlo
                    if eMOGA.mod[j] is not 1: #Este segundo individuo NO debe estar marcado como dominado tampoco
                        a = domina(eMOGA.coste_P[i], eMOGA.coste_P[j]) #Hace la comparacion entre individuos usando su vector de costes
                        if (a == 1) or (a == 3): #Si el individuo i domina al j o bien son el mismo se marca j como dominado por i
                            eMOGA.mod[j] = 1
                        elif a == 2: #Si j domina a i se marca i como dominado y se termina la comparacion
                            eMOGA.mod[i] = 1
                            break
                if eMOGA.mod[i] == 0: #Si tras comparar el elemento i con todos los individuos superiores no ha sido marcado como dominado (Mod=1) se determina que es NO dominado (Mod=2)
                    eMOGA.mod[i] = 2
        if (eMOGA.mod[eMOGA.Nind_P-1] == 0): #Tras analizar todos los individuos, si el ultimo individuo no ha sido marcado como dominado se deduce que es NO dominado y se marca
            eMOGA.mod[eMOGA.Nind_P-1] = 2
        # Se inicializan los limites de cada dimension del espacio objetivo de forma que se actualicen con los primeros valores que se tengan de los elementos NO dominado
        for j in range(eMOGA.Objfun_dim):
            eMOGA.max_f[j] = -100000
            eMOGA.min_f[j] = 10000
        # Se actualizan los limites con los individuos NO dominados (Mod=2)
        for i in range(eMOGA.Nind_P):
            if eMOGA.mod[i] == 2:
                for j in range(eMOGA.Objfun_dim):
                    if eMOGA.coste_P[i,j] > eMOGA.max_f[j]:
                        eMOGA.max_f[j] = eMOGA.coste_P[i,j]
                    if eMOGA.coste_P[i,j] < eMOGA.min_f[j]:
                        eMOGA.min_f[j] = eMOGA.coste_P[i,j]
        # Se calcula el ancho de caja (epsilon) para cada dimension del espacio objetivo
        for j in range(eMOGA.Objfun_dim):
            eMOGA.epsilon[j] = (eMOGA.max_f[j] - eMOGA.min_f[j]) / eMOGA.n_div[j]
        #Para cada individuo NO dominado se calcula su caja y se almacena en A
        for i in range(eMOGA.Nind_P):
            if eMOGA.mod[i]==2:
                box = Calcula_box(eMOGA, eMOGA.coste_P[i])
                eMOGA = Archivar(eMOGA, eMOGA.ele_P[i], eMOGA.coste_P[i], box[0])
    else: #Para generaciones distintas de la primera
        for i in range(eMOGA.Nind_GA): #Para cada individuo de GA se analiza si debe añadirse a A
            a = 0
            b = 0
            for j in range(eMOGA.Objfun_dim): #Se estudia en que zona estaria en el espacio objetivo
                if eMOGA.coste_GA[i,j] >= eMOGA.max_f[j]:
                    a = a + 1
                if eMOGA.coste_GA[i,j] <= eMOGA.min_f[j]:
                    b = b + 1
            # Caso Z1, se debe comprobar si se añade al set de pareto
            if (a == 0) and (b == 0):
                eMOGA.box_GA[i] = Calcula_box(eMOGA, eMOGA.coste_GA[i])
                eMOGA = Archivar(eMOGA, eMOGA.ele_GA[i], eMOGA.coste_GA[i], eMOGA.box_GA[i])
            # Caso Z4, todos los individuos de A desaparecen y unicamente se añade el individuo analizado
            elif b == eMOGA.Objfun_dim and a == 0:
                x = np.arange(1, eMOGA.Nind_A)
                eMOGA.ele_A = np.delete(eMOGA.ele_A, x, axis=0)
                eMOGA.coste_A = np.delete(eMOGA.coste_A, x, axis=0)
                eMOGA.box_A = np.delete(eMOGA.box_A, x, axis=0)
                eMOGA.Nind_A = 1 #El tamaño del set pasa a ser 1
                eMOGA.ele_A[0] = eMOGA.ele_GA[i]
                eMOGA.coste_A[0] = eMOGA.coste_GA[i]
                eMOGA.max_f = eMOGA.coste_GA[i]
                eMOGA.min_f =eMOGA.coste_GA[i]
            # Caso Z2 no se hace nada
            elif(a==eMOGA.Objfun_dim and b==0):
                continue
            # Caso Z3 se comprueba la dominancia para en la nueva poblacion A U GA(i)
            else:
                aux2 = 0
                for j in range(eMOGA.Nind_A):
                    c = domina(eMOGA.coste_A[j], eMOGA.coste_GA[i])
                    if c == 1:
                        aux2 = 1
                        break
                if aux2 == 0:
                    j = 0
                    while j < (eMOGA.Nind_A):
                        c = domina(eMOGA.coste_GA[i], eMOGA.coste_A[j])
                        if (c == 1):
                            eMOGA.ele_A = np.delete(eMOGA.ele_A, j, axis=0)
                            eMOGA.box_A = np.delete(eMOGA.box_A, j, axis=0)
                            eMOGA.coste_A = np.delete(eMOGA.coste_A, j, axis=0)
                            eMOGA.Nind_A = eMOGA.Nind_A - 1
                            j = j - 1
                        j = j + 1
                    for p in range(eMOGA.Objfun_dim):
                        eMOGA.max_f[p] = eMOGA.coste_GA[i,p]
                        eMOGA.min_f[p] = eMOGA.coste_GA[i,p]
                    for j in range(eMOGA.Nind_A):
                        for k in range(eMOGA.Objfun_dim):
                            if eMOGA.coste_A[j,k] >= eMOGA.max_f[k]:
                                eMOGA.max_f[k] = eMOGA.coste_A[j,k]
                            if eMOGA.coste_A[j,k] <= eMOGA.min_f[k]:
                                eMOGA.min_f[k] = eMOGA.coste_A[j,k]
                    for j in range(eMOGA.Objfun_dim):
                        eMOGA.epsilon[j] = (eMOGA.max_f[j] - eMOGA.min_f[j]) / eMOGA.n_div[j]
                    for j in range(eMOGA.Nind_A):
                        eMOGA.box_A[j] = Calcula_box(eMOGA, eMOGA.coste_A[j])
                    Nind_A_temp = eMOGA.Nind_A
                    copiaele = eMOGA.ele_A
                    copiacos = eMOGA.coste_A
                    copiabox = eMOGA.box_A
                    eMOGA.Nind_A = 1
                    x = np.arange(1,Nind_A_temp)
                    eMOGA.ele_A = np.delete(eMOGA.ele_A, x, axis=0)
                    eMOGA.coste_A= np.delete(eMOGA.coste_A, x, axis=0)
                    eMOGA.box_A = np.delete(eMOGA.box_A, x, axis=0)
                    for j in range(1, Nind_A_temp):
                        eMOGA = Archivar(eMOGA, copiaele[j], copiacos[j], copiabox[j])
                    eMOGA.box_GA[i]=Calcula_box(eMOGA, eMOGA.coste_GA[i])
                    eMOGA = Archivar(eMOGA, eMOGA.ele_GA[i],  eMOGA.coste_GA[i], eMOGA.box_GA[i])
                eMOGA = Actualizar_P(eMOGA, eMOGA.ele_GA[i], eMOGA.coste_GA[i])
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------RELLENA GA2---------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Rellena_GA2(eMOGA):
    for i in range(0,eMOGA.Nind_GA-1,2):
        a=uniform_int(eMOGA.Nind_P-1)
        eMOGA.ele_GA[i] = eMOGA.ele_P[a]
        b = uniform_int(eMOGA.Nind_A-1)
        eMOGA.ele_GA[i+1] = eMOGA.ele_A[b]
        pm=rd.random()
        if pm > eMOGA.Pm:
            eMOGA = Lxov(eMOGA, i, i + 1)
        else:
            eMOGA = MutRealDGausPond2(eMOGA, i)
            eMOGA = MutRealDGausPond2(eMOGA, i + 1)
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------evMOGA (FUNCION PRINCIPAL)------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def evMOGA(eMOGA): #Recibe una instancia del algoritmo evMOGA y devuelve el frente de pareto, los elementos que lo componen y el propio eMOGA

    if eMOGA.n_div[0]==0: #Longitud len()?¿?¿?¿?
        eMOGA.n_div = 50*np.ones((eMOGA.Objfun_dim),dtype=int)
    elif len(eMOGA.n_div)==1:
        eMOGA.n_div = eMOGA.n_div*np.ones(eMOGA.Objfun_dim)

    eMOGA.epsilon=np.ones((eMOGA.Objfun_dim),dtype=float) #Genera un vector con los tamaños de las cajas para cada dimension sinedo estos tamaños 1 inicialmente
    eMOGA.max_f = np.ones((eMOGA.Objfun_dim),dtype=int) #Genera un vector con los valores maximos para cada dimension sinedo estos tamaños 1 inicialmente
    eMOGA.min_f = np.ones((eMOGA.Objfun_dim),dtype=int)#Genera un vector con los valores minimos para cada dimension sinedo estos tamaños 1 inicialmente

    #Poblacion P
    eMOGA.ele_P=np.ones((eMOGA.Nind_P,eMOGA.searchSpace_dim),dtype=int)
    eMOGA.coste_P = np.ones((eMOGA.Nind_P, eMOGA.Objfun_dim),dtype=int)
    eMOGA.mod = np.zeros((eMOGA.Nind_P))

    # Polupation A
    eMOGA.ele_A = np.ones((1,eMOGA.searchSpace_dim),dtype=int)
    eMOGA.ele_A=np.delete(eMOGA.ele_A,0,axis=0)
    eMOGA.coste_A = np.ones((1,eMOGA.Objfun_dim),dtype=int)
    eMOGA.coste_A=np.delete(eMOGA.coste_A,0,axis=0)
    eMOGA.box_A = np.ones((1, eMOGA.Objfun_dim),dtype=int)
    eMOGA.box_A=np.delete(eMOGA.box_A,0,axis=0)
    eMOGA.Nind_A = 0

    # Polupation GA
    eMOGA.ele_GA = np.ones((eMOGA.Nind_GA,eMOGA.searchSpace_dim),dtype=int)
    eMOGA.coste_GA = np.ones((eMOGA.Nind_GA,eMOGA.Objfun_dim),dtype=int)
    eMOGA.box_GA = np.ones((eMOGA.Nind_GA, eMOGA.Objfun_dim),dtype=int)
    eMOGA.gen_counter = 0

    if eMOGA.Generations<1:
        eMOGA.Generations=1
    eMOGA.dd_fin_aux = (M.pow((eMOGA.dd_ini / eMOGA.dd_fin),2) - 1) / (eMOGA.Generations - 1)
    eMOGA.Sigma_Pm_fin_aux = (M.pow((eMOGA.Sigma_Pm_ini / eMOGA.Sigma_Pm_fin),2) - 1) / (eMOGA.Generations - 1)
    #Fin inicializacion

    eMOGA = CrtpReal(eMOGA)
    if np.size(eMOGA.subpobIni_obj,axis=0)==1:
        nind=1
    else:
        nind=np.size(eMOGA.subpobIni_obj,axis=0)+1
        eMOGA.coste_P=replace(eMOGA.coste_P, eMOGA.subpobIni_obj, (nind-1))
     #Funcion de coste!!!!
    for i in range(nind-1,eMOGA.Nind_P):
        eMOGA.coste_P[i]=eMOGA.objfun(eMOGA.ele_P[i]) #FUNCION DE COSTE RED NEURONAL
    #NO USO EL PARAMETRO (PARAM)
    #Generacion 0
    eMOGA=Iteracion_MOEA(eMOGA,0)
    #Generacion 1 hasta el final
    for i in range(1,eMOGA.Generations):
        eMOGA=Rellena_GA2(eMOGA)
        for j in range(eMOGA.Nind_GA):
            eMOGA.coste_GA[j]=eMOGA.objfun(eMOGA.ele_GA[j])
        eMOGA=Iteracion_MOEA(eMOGA,i)
    ParetoSet=eMOGA.ele_A
    ParetoFront=eMOGA.coste_A
    return [ParetoFront,ParetoSet,eMOGA]





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------GAUSS---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def gauss(m,s2): #Recibe una media y una desviacion estandar
    aux=np.random.normal(m,s2,1) #Devuelve un valor aleatorio con esa distribucion
    return aux





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------ACTUALIZAR P--------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Actualizar_P(eMOGA,x,coste_f):
    d=0
    a=rd.randint(1,eMOGA.Nind_P-1)
    for i in range(a,eMOGA.Nind_P):
        if domina(coste_f,eMOGA.coste_P[i])==1:
            d=i
            break
    if d==0:
        for i in range(a):
            if domina(coste_f, eMOGA.coste_P[i]) == 1:
                d = i
                break
    if d is not 0:
        eMOGA.ele_P[i]=x
        eMOGA.coste_P[i]=coste_f
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------CRUCE LVOX----------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Lxov(eMOGA,p1,p2):
    padre_1=eMOGA.ele_GA[p1]
    padre_2 = eMOGA.ele_GA[p2]
    dd=eMOGA.dd_ini/(M.pow((1+eMOGA.gen_counter*eMOGA.dd_fin_aux),2))
    beta=(1+2*dd)*rd.random()-dd
    hijo_1=beta*padre_1+(1-beta)*padre_2
    hijo_2=(1-beta)*padre_1+beta*padre_2
    for k in range(eMOGA.searchSpace_dim):
        if hijo_1[k]>eMOGA.searchspaceUB[k]:
            hijo_1[k]=eMOGA.searchspaceUB[k]
        elif hijo_1[k] < eMOGA.searchspaceLB[k]:
            hijo_1[k]=eMOGA.searchspaceLB[k]
        if hijo_2[k]>eMOGA.searchspaceUB[k]:
            hijo_2[k]=eMOGA.searchspaceUB[k]
        elif hijo_2[k]< eMOGA.searchspaceLB[k]:
            hijo_2[k]=eMOGA.searchspaceLB[k]
    eMOGA.ele_GA[p1]=hijo_1
    eMOGA.ele_GA[p2]=hijo_2
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------CRUCE POR UN PUNTO--------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Cruce_punto(eMOGA,p1,p2):
    padre_1=eMOGA.ele_GA[p1]
    padre_2 = eMOGA.ele_GA[p2]
    Punto_cruce=uniform_int(eMOGA.searchSpace_dim-1)
    hijo_1=np.ones((eMOGA.searchSpace_dim),dtype=int)
    hijo_2 = np.ones((eMOGA.searchSpace_dim), dtype=int)
    for i in range(Punto_cruce):
        hijo_1[i]=padre_1[i]
        hijo_2[i] = padre_2[i]
    for i in range(Punto_cruce,eMOGA.searchSpace_dim):
        hijo_1[i]=padre_2[i]
        hijo_2[i] = padre_1[i]
    eMOGA.ele_GA[p1]=hijo_1
    eMOGA.ele_GA[p2]=hijo_2
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------REPLACE-------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def replace (Matriz_1,Matriz_2,Posicion): #Recibe una matriz "Madre" y una matriz "Hija" que se debe indexar a ella eliminando el mismo espacio que ocupará esta
    x = np.arange(0, Posicion) #Se genera un vector con las filas que deben eliminarse de la matriz madre
    Matriz_1=np.delete(Matriz_1,x,axis=0) #Se eliminan esas filas
    Matriz_1=np.append(Matriz_2,Matriz_1,axis=0) #Se añade la matriz hija en esa posicion eliminada
    return Matriz_1





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------CRTPREAL------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def CrtpReal(eMOGA):
    nind= len(eMOGA.subpobIni)
    nsearchSpace_dim=len(eMOGA.subpobIni[0])
    k = 0
    if nind > 1:
        if nsearchSpace_dim==eMOGA.searchSpace_dim:
            eMOGA.ele_P=replace(eMOGA.ele_P,eMOGA.subpobIni,nind) #Sustituye las fias 1:nind por lo que haya en subplotIni
            k = nind + 1
    for j in range(eMOGA.searchSpace_dim):
        for i in range(k,eMOGA.Nind_P):
            eMOGA.ele_P[i,j] = (eMOGA.searchspaceUB[j] - eMOGA.searchspaceLB[j])*rd.random() + eMOGA.searchspaceLB[j]
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------MUTREALGAUSPOND2----------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def MutRealDGausPond2(eMOGA,p): #Funcion que muta un individuo dado
    padre = eMOGA.ele_GA[p] #Se copia el individuo a mutar
    sigma = eMOGA.Sigma_Pm_ini / M.pow((1 + eMOGA.gen_counter * eMOGA.Sigma_Pm_fin_aux),2) #Se calcula un % que desciende con el cuadrado de las generaciones aproximadamente
    for j in range(eMOGA.searchSpace_dim):
        padre[j] = padre[j]  + gauss(0, (eMOGA.searchspaceUB[j] - eMOGA.searchspaceLB[j]) * sigma / 100.0) #Se le añade a esa dimension el % anterior sobre la diferencia entre el valor maximo y el minimo que admite la dimension
        if (padre[j] > eMOGA.searchspaceUB[j]): #Si se ha excedido alguno de los limites superiores o inferiores se saturan estos valores poniendo los maximos o minimos
            padre[j]  = eMOGA.searchspaceUB[j]
        elif(padre[j] < eMOGA.searchspaceLB[j]):
            padre[j]  = eMOGA.searchspaceLB[j]
    eMOGA.ele_GA[p]=padre #Se reemplaza este individuo mutado por el original en el conjunto
    return eMOGA





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------UNIFORM INT---------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------


def uniform_int(x): #Devuelve un valor aleatorio entero entre 0 y el valor que recibe
    x=rd.randint(0,x)
    return x





#---------------------------------------------------------------------------------------------------------------------------
#-------------------------------------FUNCION COSTE-------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

def Funcion_analisis_Prueba(Vector):
	a1 = 0.5 * M.sin(1) - 2 * M.cos(1) + M.sin(2) - 1.5 * M.cos(2);
	a2 = 1.5 * M.sin(1) - M.cos(1) + 2 * M.sin(2) - 0.5 * M.cos(2);
	b1 = 0.5 * M.sin(Vector[0]) - 2 * M.cos(Vector[0]) + M.sin(Vector[1]) - 1.5 * M.cos(Vector[1]);
	b2 = 1.5 * M.sin(Vector[0]) - M.cos(Vector[0]) + 2 * M.sin(Vector[1]) - 0.5 * M.cos(Vector[1]);

	J1 = (1 + (a1 - b1) ** 2 + (a2 - b2) ** 2);
	J2 = ((Vector[0] + 3) ** 2 + (Vector[1] + 1) ** 2);
	J =np.array([J1,J2])
	return J


