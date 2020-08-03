import pygame as p  # No deberiamos usarla aqui pero por ahora se usa para aprovechar los metodos de colisiones de la clase sprite
import numpy as np
import random as rd
from keras.models import Sequential
from keras.layers import Dense
import cv2 as cv2
import collections as c


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE ABSTRACTA PARA JUGADORES----------------------------------------------
# --------------------------------------------------------------------------------------------------------------

class Player_basico(p.sprite.Sprite):
    def __init__(self, Tipo_jugador):
        p.sprite.Sprite.__init__(self)  # Inicializa como una clase sprite para usar los metodos que ya existen
        self.velocidad = [0, 0]  # Velocidad basica del agente en las dos coordenadas
        self.comida = 0  # Valor de comida almacenada
        self.Luz = 0  # Luz acumulada
        self.energia = 10  # Valor de la energia del individuo
        self.vmax = 10  # Velocidad maxima que puede alcanzar
        self.act_comido = 0  # Flag de haber realizado la accion de comer que se tendrá encuenta para descontar energia por el proceso
        self.tipo_jugador = Tipo_jugador  # Con esto se puede tener todos los jugadores en un mismo grupo y distinguir entre los tipos de jugadores para ejecutar sus habilidades propias



    def update(self):  # Funcion propia de la clase stripe sobreescrita
        self.rect.move_ip(*self.velocidad)  # Funcion para actualizar la posicion en cada iteracion

    def Actualizar_luz(self):
        self.Luz = self.rect.y * 0.8 + rd.random()  # Calcula la luz en funcion de la posicion arriba

    def Digestion(
            self):  # 1.5 unidad de luz + 1 unidad de comida son 1.5 unidades de energia (Podrian hacerse digestiones mayores Ej:2 comida, 3 Luz --> 3 energia o multiplos asi si es posible)
        self.comida -= 1  # Coste de comida para generar energia
        self.Luz -= 1.5  # Coste de luz para generar energia
        self.energia += 1.5  # Energia conseguida en el proceso

    # Revisar funcion (Se puede mejorar o integrar en la funcion gasto de energia o similar)
    def Cagar(self,
              grupo):  # Parte de la comida no debe ser util para el individuo por lo que se generará un residuo con un % del valor alimenticio de la comida
        mierda = Mierda()
        mierda.Alimento = self.comida * 0.2  # Porcentaje del alimento que se pierde
        self.comida -= self.comida * 0.2  # El individuo pierde alimento
        # Misma posicion donde se produce la funcion
        mierda.rect.x = self.rect.x
        mierda.rect.y = self.rect.y
        grupo.add(mierda)
        return grupo

    def Gasto_energia(self):
        Gasto = (abs(self.velocidad[0, 0]) + abs(self.velocidad[
                                                     0, 1])) * 0.008  # Gasto de 0.3 de energia por pixel recorrido en cada direccion (¿Pitagoras para hacer la distancia?)
        # Funcion abs porque la velocidad puede ser negativa y generar un aumento de la energia con un gasto negativo
        Gasto += 2 * self.act_comido  # Si ha comido act_comido=1 si no sera 0 y no restara energia
        Gasto += 0.01  # Gasto por existir para penalizar agentes inmoviles
        self.energia -= Gasto  # Se resta al atributo energia
        self.act_comido = 0  # Se resetea el flaf de haber comido


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE PARA JUGADORES CON IA-------------------------------------------------
# --------------------------------------------------------------------------------------------------------------

class player_IA(Player_basico):  # Clase que a su vez instancia a la clase sprite de pygame
    def __init__(self,Espacio_acciones, Espacio_estados):
        Player_basico.__init__(self, 1)
        self.image = p.image.load("Cerebro.jfif")
        self.rect = self.image.get_rect()  # Genera una region para el agente
        self.rect.y = rd.randint(60, 600)  # Posicion en el eje Y aleatoria
        self.rect.x = rd.randint(0, 1200)  # Posicion en el eje X aleatoria

        #----------------------------------------------------------------------------------------
        #-------------------------------------------------RED------------------------------------
        # ---------------------------------------------------------------------------------------

        self.model = 0  # Red neuronal para hacer las predicciones
        self.config_model = 0  # Estructura de la red neuronal por si se reproduce poder clonar la red
        self.Estructura_red = [2, 12, 6]  # [capas_ocultas Neuronas entrada Neuronas capas ocultas]
        self.Pesos = 0  # Valor de los pesos de la red por si el individuo se reproduce poder clonarlos
        self.vision = 0

        # -------------------------------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------DQN----------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------------------------------------------------------------

        # Propiedades a memorizar
        self.estado = [self.rect.x, 0]
        self.accion = 0
        self.recompensa = 0
        self.Nuevo_estado = 0
        self.muerto = 0

        # Parametros aprendizaje reforzado
        self.learning_rate = 0.001  # Tasa de aprendizaje
        self.Espacio_estados = Espacio_estados  # Cantidad de "sensores" que definen el estado
        self.Espacio_acciones = Espacio_acciones  # Cantidad de acciones que se pueden hacer
        self.memoria = c.deque(maxlen=2000)  # Revisar libreria
        self.gamma = 0.95  # tasa de descuento para la funcion de perdidas (Termino de futuras recompensas)
        self.epsilon = 1.0  # Como de probable es que la red tome una decision (1 imposible, 0 siempre) Va cayendo de 1 a epsilon min en pasos de epsilon decay
        self.epsilon_min = 0.01  #
        self.epsilon_decay = 0.995  #

    def Crear_red(self):
        model = Sequential()  # Modelo secuencial de capas (Una detras de otra)
        model.add(Dense(self.Estructura_red[1], activation='relu', input_shape=(
        2,)))  # Se añade la capa incial con una entrada de 2 dimensiones (Revisar el input bien)
        for capas in range(self.Estructura_red[0]):  # Añadir tantas capas ocultas como este en la estructura
            model.add(Dense(self.Estructura_red[2],
                            activation='relu'))  # Capa densa de tantas neuronas como este en su vector estructura
        model.add(Dense(2, activation='sigmoid'))  # Capa de salida con funcion sigmoide y 2 neuronas
        self.model = model  # Almacena el modelo en el agente
        self.config_model = model.get_config()  # Almacen su estructura por si se reproduce clonarla
        self.Pesos = self.model.get_weights()  # Almacena los pesos por si se reproduce clonarlos

    def Predecir(self):
        Entrada = np.transpose(np.array([[self.comida], [self.Luz]]))  # Vector estado
        Decision = self.model.predict([Entrada])  # Dado el estado actual que velocidad impongo en cada direccion
        Decision = Decision - 0.5  # hasta 0.5 es el rango de velocidades negativas y hasta 1 es el rango de velocidades positivas
        self.velocidad = Decision * self.vmax  # Valor final de la velocidad del agente

    def Mutar_red(self):  # Modifica la estructura de la red
        self.Estructura_red[0] = rd.randint(1, 5)  # Capas ocultas
        self.Estructura_red[1] = rd.randint(2, 10)  # Numero de neuronas capa entrada
        self.Estructura_red[2] = rd.randint(2, 10)  # Numero de neuronas de la capa oculta

    def Ver(self):  # Extrae la imagen del entorno de cada agente
        image = cv2.imread('Camara.jpg')  # Cargamos el frame completo actual
        x = self.rect.x  # Ubicamos el centro de lo que queremos recortar
        y = self.rect.y  # "
        mascara_imagen = image[y - 100:y + 100,
                         x - 100:x + 100]  # Recortamos un rectangulo en la imagen con las cuatro esquinas como coordenadas
        # cv2.imshow('imagen',mascara_imagen) #Para debug de lo que recorta
        # cv2.waitKey(0) #Hay que pulsar 'q' para que pase a la imagen siguiente
        self.vision = mascara_imagen  # Almacenamos la nueva imagen como la vision en este bucle de ejecucion

    # ------------------------------------------------------------------------------------------------------
    #--------------------------------------------------DQN--------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
    def memorize(self): #Almacena el recuerdo en la memoria
        self.memoria.append((self.estado, self.accion, self.recompensa, self.Nuevo_estado, self.muerto))

    def act(self): #DEBE SER UNA MEZCLA CON LA FUNCION PREDECIR
        if np.random.rand() <= self.epsilon: #Posibilidad de tomar las decisiones de forma aleatoria o inteligente
            return rd.randrange(self.Espacio_acciones) #Elige una accion cualquiera
        estado=np.transpose(np.array([[self.estado[0]],[self.estado[1]]]))#Acondiciona la entrada
        act_values = self.model.predict(estado) #Predice las recompensas para cada accion en ese estado
        self.accion=np.argmax(act_values[0])  # Devuelve la posicion del valor mas alto

    def replay(self, batch_size):
        minibatch = rd.sample(self.memoria,batch_size)  # Coje un numero de recuerdos de la memoria de forma aleatoria (NO secuenciales, estas redes no perciben temporalidad
        # eso lo podriamos hacer con redes recurrentes)
        for Estado_actual, Accion, Recompensa, Estado_siguiente, Muerto in minibatch:  # Para cada recuerdo entrena la red
            if Muerto:
                target = Recompensa  # La recompensa que deberia predecir la red si no hay mas estados futuros (Ha muerto en esa accion)
            else:
                Estado_siguiente = np.transpose(np.array([[Estado_siguiente[0]], [Estado_siguiente[1]]]))  # Acondiciona la entrada
                target = Recompensa + self.gamma * np.amax(self.model.predict(Estado_siguiente)[0])  # Lo que deberia predecir la red como recompensa de elegir la accion [Accion]
                # ese estado mas la recompensa futura de una accion mas.
            Estado_actual = np.transpose(np.array([[Estado_actual[0]], [Estado_actual[1]]]))  # Acondiciona la entrada
            target_f = self.model.predict(Estado_actual)  # El vector de valores que la red predice para el estado en el que se encontraba
            target_f[0][Accion] = target  # Se sustituye la recompensa que espera la red por la que se obtuvo al elegir la accion [Accion] dentro del vector
            self.model.fit(Estado_actual, target_f, epochs=1,verbose=0)  # La red compara su prediccion para la posicion [Accion] con lo que sucedio realmente e intenta minimizar la diferencia cuadratica
        if self.epsilon > self.epsilon_min:  # Si epsilon no es igual que el minimo se actualiza
            self.epsilon *= self.epsilon_decay  # epsilon decar un porcentaje para darle mas peso a las decisiones de la red



# --------------------------------------------------------------------------------------------------------------
# ----------------------------------FUNCION MITOSIS PARA JUGADORES CON IA---------------------------------------
# --------------------------------------------------------------------------------------------------------------

def Mitosis_IA(Player,grupo):  # No se como hacer un metodo que replique otro individuo sin liarme con los atributos, por eso he hecho una funcion externa,
    # pero igual es mejor un metodo para que sea todo mas elegante
    jugador = player_IA()  # Nuevo agente
    new_model = Sequential.from_config(Player.config_model)  # Mismo red neuronal
    new_model.set_weights(Player.Pesos)  # Mismos pesos
    jugador.model = new_model  # Asignacion de la red clonada
    jugador.config_model = Player.config_model  # Almacena su nuevo modelo por si se reproduce
    jugador.Pesos = Player.Pesos  # Almacena sus nuevos pesos por si se reproduce
    jugador.energia = Player.energia / 10  # Se quedan un 10% de la energia que tenia el individuo original perdiendo un 80% en el proceso
    Player.energia = Player.energia / 10  # Se quedan un 10% de la energia que tenia el individuo original perdiendo un 80% en el proceso
    jugador.vmax = Player.vmax + Player.vmax * (rd.random() - rd.random())  # Puede aumentar o disminuir la velocidad del nuevo individuo
    grupo.add(jugador)  # Se añade a la lista de agentes
    return grupo


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE PARA JUGADORES RANDOM-------------------------------------------------
# --------------------------------------------------------------------------------------------------------------


class player_Random(Player_basico):  # Clase jugadores con la politica random
    def __init__(self):
        Player_basico.__init__(self, 2)
        self.image = p.image.load("Imagenes/Dados.jfif")
        self.rect = self.image.get_rect()  # Genera una region para el agente
        self.rect.y = rd.randint(60, 600)  # Posicion en el eje Y aleatoria
        self.rect.x = rd.randint(0, 1200)  # Posicion en el eje X aleatoria

    def Predecir(self):
        Decision = np.array([[rd.random(),rd.random()]])  # Valores random de 0 a 1 (Este formato es porque como la funcion gasto es comun a todos y accede a la velocidad
        # el vector decision tiene que tener la misma forma en todos los agentes para que la velocidad tenga el mismo formato y como las redes generan este formato lo replicamos )
        Decision = Decision - 0.5  # hasta 0.5 es el rango de velocidades negativas y hasta 1 es el rango de velocidades positivas
        self.velocidad = Decision * self.vmax  # Valor final de la velocidad del agente


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------FUNCION MITOSIS PARA JUGADORES RANDOM---------------------------------------
# --------------------------------------------------------------------------------------------------------------

def Mitosis_Random(Player,grupo):  # No se como hacer un metodo que replique otro individuo sin liarme con los atributos, por eso he hecho una funcion externa,
    # pero igual es mejor un metodo para que sea todo mas elegante
    jugador = player_Random()  # Nuevo agente
    jugador.Predecir()  # Inicializa la velocidad con el formato adecuado
    jugador.vmax = Player.vmax + Player.vmax * (rd.random() - rd.random())  # Puede aumentar o disminuir la velocidad
    jugador.energia = Player.energia / 10  # Se quedan un 10% de la energia que tenia el individuo original perdiendo un 80% en el proceso
    Player.energia = Player.energia / 10  # Se quedan un 10% de la energia que tenia el individuo original perdiendo un 80% en el proceso
    grupo.add(jugador)  # Se añade a la lista de agentes
    return grupo


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE COMIDA ---------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------

class Comida(p.sprite.Sprite):
    def __init__(self):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Comida.jfif")
        self.rect = self.image.get_rect()  # Genera una region para el agente
        self.velocidad = [0, 0]  # Esta parado siempre
        self.Alimento = 3  # Cuanto alimento aporta al individuo que lo consume
        self.rect.y = rd.randint(60, 600)  # Posicion en el eje Y aleatoria
        self.rect.x = rd.randint(0, 1200)  # Posicion en el eje X aleatoria


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE MIERDA----------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------
class Mierda(p.sprite.Sprite):
    def __init__(self):
        p.sprite.Sprite.__init__(self)
        self.image = p.image.load("Imagenes/Mierda.jfif")
        self.rect = self.image.get_rect()  # Genera una region para el agente
        self.velocidad = [0, 0]  # Esta parado siempre
        self.Alimento = 0
        self.rect.y = 0
        self.rect.x = 0
        self.vida = 10  # Ciclos en los que desaparecera la mierda si no se hace nada con ella


# --------------------------------------------------------------------------------------------------------------
# ----------------------------------CLASE SIMULACION------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------

class simulacion():
    def __init__(self):
        self.steps=1000 #Steps antes de parar la simulacion
        self.generations = 5000  #Partidas para aprender
        self.size = 1200, 600  # Tamaño de la pantalla (Podrian usarse las dos siguientes propiedades y eliminar esta)
        self.width = 1200  # Ancho de la pantalla
        self.height = 600  # Alto de la pantalla
        self.players_IA = 5  # Numero de jugadores con IA
        self.players_Random = 5  # Numero de jugadores random
        self.cantidad_comida = 90  # Numero de objetos comida que se instanciarán
        self.pm = 0.00001  # Probabilidad de mutacion
        self.umbral_energia = 100  # Energia minima necesaria para duplicarse



