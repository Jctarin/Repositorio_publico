from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
import numpy as np
import collections as c
import random as rd
import pygame as p


class Agente_DQN(p.sprite.Sprite):
    def __init__(self, Espacio_acciones, Espacio_estados):
        p.sprite.Sprite.__init__(self)  # Inicializa como una clase sprite para usar los metodos que ya existen
        #Parametros aprendizaje reforzado
        self.learning_rate = 0.001 #Tasa de aprendizaje
        self.model = 0 # Red del agente
        self.Espacio_estados = Espacio_estados #Cantidad de "sensores" que definen el estado
        self.Espacio_acciones = Espacio_acciones #Cantidad de acciones que se pueden hacer
        self.memoria = c.deque(maxlen=20000) #Revisar libreria
        self.gamma = 0.95    # tasa de descuento para la funcion de perdidas (Termino de futuras recompensas)
        self.epsilon = 1.0  # Como de probable es que la red tome una decision (1 imposible, 0 siempre) Va cayendo de 1 a epsilon min en pasos de epsilon decay
        self.epsilon_min = 0.01 #
        self.epsilon_decay = 0.995 #


        #Parametros del entorno
        self.image = p.image.load("Tanque.jpg")
        self.rect = self.image.get_rect()  # Genera una region para el agente
        self.rect.y = 550
        self.rect.x = rd.randint(50, 1100)  # Posicion en el eje X aleatoria


        #Propiedades a memorizar
        self.estado=[self.rect.x,0]
        self.accion=0
        self.recompensa=0
        self.Nuevo_estado=0
        self.muerto=0


        #Parametros del agente especifico en la simulacion
        # self.config_model=0 #Estructura de la red neuronal por si se reproduce poder clonar la red
        self.Estructura_red=[5,6,16]#[capas_ocultas Neuronas entrada Neuronas capas ocultas]
        # self.Pesos = 0  # Valor de los pesos de la red por si el individuo se reproduce poder clonarlos



        #Parametros del agente generico en la simulacion
        self.vida=100
        self.velocidad = [0, 0]  # Velocidad basica del agente en las dos coordenadas
        # self.comida = 0  # Valor de comida almacenada
        # self.Luz = 0  # Luz acumulada
        # self.energia = 10  # Valor de la energia del individuo
        # self.act_comido = 0  # Flag de haber realizado la accion de comer que se tendrá encuenta para descontar energia por el proceso
        # self.vmax = 10  # Velocidad maxima que puede alcanzar

    def Crear_red(self): #Funcion de crear red propia (Revisar la estructura que queremos)
        model=Sequential() #Modelo secuencial de capas (Una detras de otra)
        model.add(Dense(self.Estructura_red[1],activation='relu',input_shape=(2,))) #Se añade la capa incial con una entrada de 2 dimensiones (Revisar el input bien)
        for capas in range(self.Estructura_red[0]): #Añadir tantas capas ocultas como este en la estructura
            model.add(Dense(self.Estructura_red[2], activation='relu')) #Capa densa de tantas neuronas como este en su vector estructura
        model.add(Dense(self.Espacio_acciones, activation='linear')) #Capa de salida con tantas neuronas como acciones pueda hacer el agente
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate)) #Se compila para poder entrenar
        self.model=model #Almacena el modelo en el agente
        # self.config_model=model.get_config() #Almacen su estructura por si se reproduce clonarla
        # self.Pesos=self.model.get_weights() #Almacena los pesos por si se reproduce clonarlos


    def memorize(self): #Almacena el recuerdo en la memoria
        self.memoria.append((self.estado, self.accion, self.recompensa, self.Nuevo_estado, self.muerto))

    def act(self): #DEBE SER UNA MEZCLA CON LA FUNCION PREDECIR
        if np.random.rand() <= self.epsilon: #Posibilidad de tomar las decisiones de forma aleatoria o inteligente
            return rd.randrange(self.Espacio_acciones) #Elige una accion cualquiera
        estado=np.transpose(np.array([[self.estado[0]],[self.estado[1]]]))#Acondiciona la entrada
        act_values = self.model.predict(estado) #Predice las recompensas para cada accion en ese estado
        # print(self.estado,'Estado')
        # print(act_values,'Valores')
        self.accion=np.argmax(act_values[0])  # Devuelve la posicion del valor mas alto

    # def Predecir(self): #DEBE SER UNA MEZCLA CON LA FUNCION ACT
    #     Entrada=np.transpose(np.array([[self.comida],[self.Luz]])) #Vector estado
    #     Decision=self.model.predict([Entrada]) #Dado el estado actual que velocidad impongo en cada direccion
    #     Decision=Decision-0.5 # hasta 0.5 es el rango de velocidades negativas y hasta 1 es el rango de velocidades positivas
    #     self.velocidad=Decision*self.vmax #Valor final de la velocidad del agente

    def replay(self, batch_size):
        minibatch = rd.sample(self.memoria, batch_size) #Coje un numero de recuerdos de la memoria de forma aleatoria (NO secuenciales, estas redes no perciben temporalidad
        # eso lo podriamos hacer con redes recurrentes)
        for Estado_actual, Accion, Recompensa, Estado_siguiente, Muerto in minibatch: #Para cada recuerdo entrena la red
            if Muerto:
                target = Recompensa # La recompensa que deberia predecir la red si no hay mas estados futuros (Ha muerto en esa accion)
            else:
                Estado_siguiente = np.transpose(np.array([[Estado_siguiente[0]], [Estado_siguiente[1]]]))  # Acondiciona la entrada
                target = Recompensa + self.gamma * np.amax(self.model.predict(Estado_siguiente)[0]) #Lo que deberia predecir la red como recompensa de elegir la accion [Accion]
                # ese estado mas la recompensa futura de una accion mas.
            Estado_actual = np.transpose(np.array([[Estado_actual[0]], [Estado_actual[1]]]))  # Acondiciona la entrada
            target_f = self.model.predict(Estado_actual) #El vector de valores que la red predice para el estado en el que se encontraba
            target_f[0][Accion] = target #Se sustituye la recompensa que espera la red por la que se obtuvo al elegir la accion [Accion] dentro del vector

            self.model.fit(Estado_actual, target_f, epochs=1, verbose=0) #La red compara su prediccion para la posicion [Accion] con lo que sucedio realmente e intenta minimizar la diferencia cuadratica

        if self.epsilon > self.epsilon_min: #Si epsilon no es igual que el minimo se actualiza
            self.epsilon *= self.epsilon_decay #epsilon decar un porcentaje para darle mas peso a las decisiones de la red

    def update(self):  # Funcion propia de la clase stripe sobreescrita
        self.rect.move_ip(*self.velocidad)  # Funcion para actualizar la posicion en cada iteracion

    def moverse(self):
        if self.accion==0:
            self.velocidad[0]=-1
        elif self.accion==1:
            self.velocidad[0]=0
        else:
            self.velocidad[0]=1



#--------------------------------------------------------------------------------------------------------------
#----------------------------------CLASE SIMULACION------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------

class simulacion():
    def __init__(self):
        self.steps=15000 #Steps antes de parar la simulacion
        self.generations = 12000 #Partidas para aprender
        self.size = 1200, 600 #Tamaño de la pantalla (Podrian usarse las dos siguientes propiedades y eliminar esta)
        self.width=1200 #Ancho de la pantalla
        self.height =  600 #Alto de la pantalla
        self.Malos=80 #Numero de malos
        self.Agentes=1 #Numero de agentes
        self.Bloques_init=1




#--------------------------------------------------------------------------------------------------------------
#----------------------------------CLASE MALO----------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class Malo(p.sprite.Sprite):
    def __init__(self):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Platillo.jpg")
        self.rect=self.image.get_rect() #Genera una region para el agente
        self.velocidad=[0,0]
        self.rect.y =60
        self.rect.x =rd.randint(50,1100)
    def nueva_velocidad(self):
        self.velocidad[0]=rd.randint(0,2)
    def Disparar(self,Grupo):
        if rd.random()<0.002: #Posibilidad de disparar
           Grupo.add(Bomba(self.rect.x))#Genera una bomba y la añade a la lista de bombas
    def update(self):  # Funcion propia de la clase stripe sobreescrita
        self.rect.move_ip(*self.velocidad)  # Funcion para actualizar la posicion en cada iteracion

#--------------------------------------------------------------------------------------------------------------
#----------------------------------CLASE BOMBA----------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class Bomba(p.sprite.Sprite):
    def __init__(self,pos):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Bomba.jfif")
        self.rect=self.image.get_rect() #Genera una region para el agente
        self.velocidad=[0,2]
        self.rect.y =60
        self.rect.x =pos
        self.daño=4
    def update(self):  # Funcion propia de la clase stripe sobreescrita
        self.rect.move_ip(*self.velocidad)  # Funcion para actualizar la posicion en cada iteracion

#--------------------------------------------------------------------------------------------------------------
#----------------------------------CLASE EXPLOSION-------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class Explosion(p.sprite.Sprite):
    def __init__(self,posx,posy):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Explosion.jpg")
        self.rect=self.image.get_rect() #Genera una region para el agente
        self.velocidad=[0,0]
        self.rect.y = posy-10
        self.rect.x =posx
        self.vida=30


#--------------------------------------------------------------------------------------------------------------
#----------------------------------CLASE BLOQUE----------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class Bloque(p.sprite.Sprite):
    def __init__(self):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Bloque.jpg")
        self.rect=self.image.get_rect() #Genera una region para el agente
        self.velocidad=[0,0]
        self.rect.y = 400
        self.rect.x =rd.randint(10,1100)
        self.vida=300000