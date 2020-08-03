import pygame
import random as rd
import Libreria_Sopa as pc
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

simulacion=pc.simulacion() #Instancia el objeto simulacion con los parametros necesarios

#Listas de jugadores y comida
list_players_all=pygame.sprite.Group() #Lista de todos los agenestes para acciones comunes
list_comida=pygame.sprite.Group()
list_mierdas=pygame.sprite.Group()


#Inicializa el juego
pygame.init()
fuente = pygame.font.SysFont('Arial', 40) #Instancia la fuente a utilizar en el texto (Esto debe ir despues del init siempre)
screen=pygame.display.set_mode(simulacion.size) #Crea la pantalla
pygame.display.set_caption("Simulación") #Le da nombre creo

#Instanciacion de jugadores, redes de jugadores y comida
for x in range(simulacion.players_Random):
    list_players_all.add(pc.player_Random())#Intanciacion de los jugadores random

for x in range(simulacion.players_IA):
    list_players_all.add(pc.player_IA()) #Intanciacion de los jugadores con IA

for player in list_players_all:
    if player.tipo_jugador==1:
        player.Crear_red() #Instancia la red de cada individuo con IA
    else:
        player.Predecir()  # Inicializan una velocidad en el formato correcto para los players random

for i in range(simulacion.cantidad_comida):
    list_comida.add(pc.Comida()) #Instancia la comida inicial


ciclo=50 #Ciclos para los agentes random sin modificar su velocidad, de lo contrario se quedarian en el sitio practicamente
#Bucle principal
while simulacion.generations>0:
    #Choques entre los grupos(Grupo1, Grupo2,Debe desaparecer en la colision grupo1,Debe desaparecer en la colision grupo2)
    colisiones=pygame.sprite.groupcollide(list_players_all, list_comida, False, True)
    #colisiones es un diccionario donde aparece que player ha chocado con cuantas comidas
    for player,list_comida_ in colisiones.items():
        player.comida+=sum(Comida.Alimento for Comida in list_comida_) #Se suma la propiedad alimento de todas las comidas colisionadas a la comida del player
        player.act_comido=1 #Flag de comer para descontar la energia por haber comido


    for player in list_players_all:
        # Hacia donde moverse y actualizar cuanta luz tienen
        player.Actualizar_luz() #Calcula la luz que recibe el agente segun la altura
        if player.tipo_jugador==1:
            player.Predecir() #Predice el movimiento del agente
        else:
            if ciclo == 0:
                player.Predecir()  # Predice el movimiento del agente

        #Digestion
        if player.comida>1 and player.Luz>1.5:
            player.Digestion() #Convierte la luz y la comida en energia

        #Cagar
        if player.act_comido==1:
            player.Cagar(list_mierdas)

        #Gasto energetico
        player.Gasto_energia() #Calcula el coste energetido de la iteracion segun las acciones y la resta de la energia almacenada

        # Duplicarse
        if player.energia > simulacion.umbral_energia: #Si tiene energia suficiente se reproduce
            if player.tipo_jugador==1:
                list_players_all=pc.Mitosis_IA(player,list_players_all) #Duplica el agente en otro exactamente igual
            else:
                list_players_all = pc.Mitosis_Random(player,list_players_all)  # Duplica el agente en otro exactamente igual

        #Mutacion de la red
        if player.tipo_jugador==1:
            if rd.random() < simulacion.pm:
                player.Mutar_red() #Modifica su estructura
                player.Crear_red() #Crea una nueva red

        #Muerte de los que no tienen energia
        if player.energia<0:
            player.kill() #Mueren los agentes que terminan la iteracion sin energia

    #Desaparicion de la mierda
    for mierda in list_mierdas:
        mierda.vida-=1
        if mierda.vida<0:
            mierda.kill()

    #Reponer parte de la comida consumida
    comida_presente=list_comida.__len__() #Comida presente
    Nueva_comida=rd.randint(0,(simulacion.cantidad_comida-comida_presente)) #Aleatorio entre 0 y lo que falta por reponer
    for i in range(Nueva_comida):
        list_comida.add(pc.Comida()) #Instancia nueva comida atendiendo a la que se ha consumido

    # Para que no se salga de los limites (Hay que echarle un ojo a esto pq no me convence)
    for player in list_players_all:
        if player.rect.x < 0:
            player.rect.x=simulacion.width
        if player.rect.x > simulacion.width:
            player.rect.x = 0
        if player.rect.y < 60:
            player.rect.y=simulacion.height
        if player.rect.y > simulacion.height:
            player.rect.y =60
        player.update()

    Agentes_IA=0
    Agentes_random=0
    for player in list_players_all:
        if player.tipo_jugador==1:
            Agentes_IA+=1
        else:
            Agentes_random+=1


    text="Agentes IA %s" % str(Agentes_IA)
    mensaje_IA=fuente.render(text, True, (0, 0, 0)) # Muestran el texto en la pantalla

    text="Agentes Random %s" % str(Agentes_random)
    mensaje_Random=fuente.render(text, True, (0, 0, 0)) # Muestran el texto en la pantalla


    screen.fill((255,255,255)) #Pone la pantalla en blanco

    #Resetea las imagenes para que aparezcan en cada iteracion o algo parecido
    for player in list_players_all:
        screen.blit(player.image, player.rect)
    for comida in list_comida:
        screen.blit(comida.image,comida.rect)
    for mierda in list_mierdas:
        screen.blit(mierda.image,mierda.rect)

    screen.blit(mensaje_IA,(100,0))
    screen.blit(mensaje_Random, (400, 0))

    pygame.display.flip() #Actualiza la simulacion

    # Zona de vision para los agentes con IA
    pygame.image.save(screen,'Camara.jpg')
    for agente in list_players_all:
        if agente.tipo_jugador==1:
            agente.Ver()


    simulacion.generations-=1
    if ciclo==0:
        ciclo=51
    ciclo-=1
pygame.quit() #Acaba la simulacion

