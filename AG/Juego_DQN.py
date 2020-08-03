import pygame
from matplotlib import pyplot as plt
import Libreria_DQN as ag
import numpy as np


simulacion=ag.simulacion() #Instancia el objeto simulacion con los parametros necesarios

#Listas de bombas
list_bombas=pygame.sprite.Group()
list_malos=pygame.sprite.Group()
list_agentes=pygame.sprite.Group()
list_explosiones=pygame.sprite.Group()

vida=np.zeros(shape=[simulacion.generations])
Steps=np.zeros(shape=[simulacion.generations])

#Instanciacion de jugadores, redes de jugadores y comida
for agente in range(simulacion.Agentes):
    list_agentes.add(ag.Agente_DQN(3,2))
for agente in list_agentes:
    agente.Crear_red()

for malo in range(simulacion.Malos):#Se instancian tantos malos como este en la simulacion
    list_malos.add(ag.Malo())#Se añaden a la lista de malos


for i in range(simulacion.generations):
    #Inicializa la partida
    pygame.init()
    screen=pygame.display.set_mode(simulacion.size) #Crea la pantalla

    ciclo=51 #Ciclos para los agentes random sin modificar su velocidad, de lo contrario se quedarian en el sitio practicamente
    Flag_Reinicio=0 #Para saber cuando terminar la partida si el agente muere
    steps = 0
    #Bucle principal
    for p in range(simulacion.steps):

        for agente in list_agentes:
            agente.act() #Decide la nueva accion
            agente.moverse() #Aplica la nueva accion a la velocidad que va a tomar
            #Actualiza su posicion
            if agente.rect.x < 0:
                agente.rect.x = simulacion.width
            if agente.rect.x > simulacion.width:
                agente.rect.x = 0
            agente.update()

        #Actuan los malos
        for malo in list_malos:
            if ciclo==0:
                malo.nueva_velocidad()
            # Para que no se salga de los limites (Hay que echarle un ojo a esto pq no me convence)
            if malo.rect.x < 0:
                malo.rect.x = simulacion.width
            if malo.rect.x > simulacion.width:
                malo.rect.x = 0
            malo.update()
            malo.Disparar(list_bombas)

        #Actuan las bombas
        for bomba in list_bombas:
            bomba.update()
            if bomba.rect.y > 550:
                bomba.kill()

        #Choques entre los grupos(Grupo1, Grupo2,Debe desaparecer en la colision grupo1,Debe desaparecer en la colision grupo2)
        colisiones=pygame.sprite.groupcollide(list_agentes, list_bombas, False, True)
        #colisiones es un diccionario donde aparece que player ha chocado con cuantas comidas
        for Agente,list_bombas_ in colisiones.items():
            Agente.vida-=sum(Bomba.daño for Bomba in list_bombas_) #Resta el daño de la bomba a su vida
            if sum(Bomba.daño for Bomba in list_bombas_)>0: #Le dan o no las bombas
                list_explosiones.add(ag.Explosion(Agente.rect.x,Agente.rect.y))
                Agente.recompensa=-5
            else:
                Agente.recompensa=+1
        for agente in list_agentes:
            #Muerto o vivo
            if agente.vida<=0:
                agente.muerto=1
                agente.recompensa=-10
            # Nuevo estado del agente
            agente.Nuevo_estado=[agente.rect.x,0]

        #Busca la altura de la bomba mas cercana en su misma linea de caida
        for Agente in list_agentes:
            for bomba in list_bombas:
                altura=400
                if bomba.rect.x<Agente.rect.x+50 and bomba.rect.x>Agente.rect.x-50: #Si hay una bomba encima de su linea
                    if bomba.rect.y>altura and bomba.rect.y<550: #Esa bomba es la mas cercana a el sin haberle dado ya
                        Agente.Nuevo_estado[1]=bomba.rect.y #Actualiza el sensor
                        altura=bomba.rect.y

        for agente in list_agentes:
            # Memoriza el nuevo estado
            agente.memorize()
            # Actualiza el estado inicial de la siguiente iteracion
            agente.estado=agente.Nuevo_estado
            #Si muere para la simulacion despues de memorizar el suceso
            if agente.muerto==1:
                Flag_Reinicio=1
                break
        if Flag_Reinicio==1:
            Flag_Reinicio=0
            break

        # Desaparicion de las explosiones
        for Explosion in list_explosiones:
            Explosion.vida -= 1
            if Explosion.vida < 0:
                Explosion.kill()

        screen.fill((255,255,255)) #Pone la pantalla en blanco

        #Resetea las imagenes para que aparezcan en cada iteracion o algo parecido
        for malo in list_malos:
            screen.blit(malo.image, malo.rect)
        for bomba in list_bombas:
            screen.blit(bomba.image,bomba.rect)
        for Agente in list_agentes:
            screen.blit(Agente.image,Agente.rect)
        for Explosion in list_explosiones:
            screen.blit(Explosion.image, Explosion.rect)

        pygame.display.flip() #Actualiza la simulacion
        if ciclo==0:
            ciclo=51
        ciclo-=1
        steps+=1
    pygame.quit()
    media=0
    for agente in list_agentes:
        agente.replay(32)
        agente.muerto=0
        media +=agente.vida
        agente.vida=100
    media=media/simulacion.Agentes
    vida[i]=media
    Steps[i]=steps
pygame.quit()
x=np.arange(0,simulacion.generations,1)
y=vida
y_2=Steps
plot1,plot2=plt.plot(x,y,x,y_2)
plt.show()
