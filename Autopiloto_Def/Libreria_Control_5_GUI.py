from Autopiloto_Def.PID import *
import math
import socket as s
from matplotlib import pyplot as plt
import numpy as np
import queue as q
import Autopiloto_Def.Libreria_vision_GUI_2 as LV
import Autopiloto_Def.Libreria_GUI as LG

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------CLASE QGROUNCONTROL--------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
class QGC(): #Clase principal que reune todos los objetos necesarios para el vuelo autonomo
    def __init__(self,Modelo=None):
        self.Control = PIDs() #Estructura de PIDs
        self.Vector_estado = Vector_Estado() #Estructura para tratar los sensores y actuadores
        self.Mission = None #Mision cargada
        self.Verbose=Verbose_controls() #Estructura que recaba datos de vuelo
        self.PortAdress_send=("localhost",9900) #Direccion de envio de los actuadores
        self.PortAdress_recv = ("localhost", 9999)  # Puerto de recepcion de datos
        self.Cola=q.LifoQueue() #Pila de trabajo para compartir informacion con el hilo de VA
        self.sock=sock=s.socket(s.AF_INET,s.SOCK_DGRAM) #Socket para la comunicacions
        self.Modelo=Modelo #Red neuronal
        self.waypoint=Waypoint(0,0,0,0,0) #Waypoint objetivo
        sock.bind(self.PortAdress_recv) #Comienza la escucha del puerto de recepcion de datos

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------FUNCIONES DE CONTROL-------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Acciones_Control_Bajo_nivel(Ref,Qgc,Takeoff=None,Signal_heading=None,Ref_heading=None): #Bucles de control de bajo nivel (Velocidad,Pitch,Roll)
    #Bucle Acelerador
    Qgc.Verbose.Ref_velocidad.append(Ref[0])#Almacena valores
    Qgc.Control.PID_AirSpeed.setpoint=Ref[0]
    Qgc.Verbose.Signal_velocidad.append(Qgc.Vector_estado.groundspeed)#Almacena valores
    Acelerador=Qgc.Control.PID_AirSpeed(Qgc.Vector_estado.groundspeed)
    Qgc.Verbose.Control_acelerador.append(Acelerador)#Almacena valores

    #Bucle elevador
    Qgc.Verbose.Ref_pitch.append(Ref[1])#Almacena valores
    Ref[1] = Filtro(Qgc.Verbose.Ref_pitch, 4)
    Qgc.Control.PID_Pitch.setpoint=Ref[1]
    Qgc.Verbose.Signal_pitch.append(Qgc.Vector_estado.pitch)#Almacena valores
    Elevador=Qgc.Control.PID_Pitch(Qgc.Vector_estado.pitch)
    Qgc.Verbose.Control_elevador.append(Elevador)#Almacena valores

    #Bucle Aleron
    Qgc.Verbose.Ref_roll.append(Ref[2])#Almacena valores
    Ref[2] = Filtro(Qgc.Verbose.Ref_roll, 10)
    Qgc.Control.PID_Roll.setpoint=Ref[2]
    Qgc.Verbose.Signal_roll.append(Qgc.Vector_estado.roll)#Almacena valores
    Aleron=Qgc.Control.PID_Roll(Qgc.Vector_estado.roll)
    Qgc.Verbose.Control_aileron.append(Aleron) #Almacena valores
    Qgc.Verbose.Update(Qgc.Verbose.Control_aileron.__len__()) #Actualiza eje temporal

    #Actualizar posicion
    Qgc.Verbose.Lat_actual.append(Qgc.Vector_estado.lat)
    Qgc.Verbose.Lon_actual.append(Qgc.Vector_estado.lon)
    Qgc.Verbose.Lat_objetivo.append(Qgc.waypoint.lat)
    Qgc.Verbose.Lat_objetivo.append(Qgc.waypoint.lon)

    #Bucle Timon
    if Takeoff is None:
        Timon=Aleron*Qgc.Control.Rudder_Const
    else:
        if Ref_heading==None:
            Qgc.Verbose.Ref_Rudder.append(0)
            Qgc.Control.PID_Rudder.setpoint = 0
            Qgc.Verbose.Signal_Rudder.append(Signal_heading)  # Almacena valores
            Timon = Qgc.Control.PID_Rudder(Signal_heading)
        else:
            Qgc.Verbose.Ref_Rudder.append(Ref_heading)#Almacena valores
            Qgc.Control.PID_Rudder_Rumbo.setpoint = Ref_heading
            Qgc.Verbose.Signal_Rudder.append(Signal_heading)  # Almacena valores
            Timon = Qgc.Control.PID_Rudder_Rumbo(Signal_heading)

        Qgc.Verbose.Control_Timon.append(Timon)  # Almacena valores

    return [Aleron, Elevador, Timon, Acelerador]

def Acciones_Control_Alto_nivel(Ref_altitud,Signal_heading,Qgc,Ref_heading,Planeo): #Bucles de control de alto nivel
    #Bucle Elevador
    Qgc.Verbose.Ref_altitud.append(Ref_altitud)#Almacena valores
    Qgc.Control.PID_Altitud.setpoint=Ref_altitud
    Qgc.Verbose.Signal_altitud.append(Qgc.Vector_estado.alt)#Almacena valores
    Ref_pitch=Qgc.Control.PID_Altitud(Qgc.Vector_estado.alt)

    #Bucle Aleron
    if Planeo==None:
        if Ref_heading==None: #Modo navegacion
            Qgc.Verbose.Ref_heading.append(0)#Almacena valores
            Qgc.Control.PID_Heading.setpoint = 0
        else: #Modo vuelo alineado a un rumbo
            Qgc.Verbose.Ref_heading.append(Ref_heading)#Almacena valores
            Qgc.Control.PID_Heading_Rumbo.setpoint = Ref_heading
        Qgc.Verbose.Signal_heading.append(Signal_heading)#Almacena valores
        if Ref_heading==None:
            Ref_Roll=Qgc.Control.PID_Heading(Signal_heading)#heading
        else:
            Ref_Roll = Qgc.Control.PID_Heading_Rumbo(Signal_heading)  # heading
    else:
        Qgc.Verbose.Signal_heading.append(0)  # Almacena valores
        Qgc.Verbose.Ref_heading.append(0)  # Almacena valores
        Ref_Roll=Planeo
    return [Ref_pitch,Ref_Roll]

def Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Qgc,Ref_heading=None,Planeo=None,Takeoff=None):#Funcion general que enlaza los bucles de alto y bajo nivel (Heading,Vel,Altitud)
    Ref_alto_nivel=Acciones_Control_Alto_nivel(Ref_altitud,Signal_heading,Qgc,Ref_heading,Planeo)
    Acciones=Acciones_Control_Bajo_nivel([Ref_vel,Ref_alto_nivel[0],Ref_alto_nivel[1]],Qgc,Takeoff,Signal_heading,Ref_heading)
    return Acciones



#------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------CONDICIONES DE PASO POR WAYPOINT SEGUN EL MODO DE VUELO-------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Waypoint_takeoff(waypoint,vector_Estado):
    if abs(waypoint.alt-vector_Estado.alt)<2:
        return 0
    else:
        return 1
def Waypoint_nav(waypoint,vector_Estado):
    if(abs(waypoint.lat-vector_Estado.lat)<0.00015 and abs(waypoint.lon-vector_Estado.lon)<0.0001 and abs(waypoint.alt-vector_Estado.alt)<4):
        return 0
    else:
        return 1
def Waypoint_land(vector_Estado):
    if (vector_Estado.alt<10 and vector_Estado.vx<35):
        return 0
    else:
        return 1

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------MODOS DE VUELO BASICOS-----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

#---------------------------------------MODOS DE VUELO BASICOS-----------------------------------------------------------------------
def Takeoff(Hilo):
    Aux=[0,0,0,0]
    Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)  # Recepcion de datos del simulador
    while(Waypoint_takeoff(Hilo.Qgc.Vector_estado,Hilo.waypoint) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock) #Recepcion de datos del simulador
        Ref_altitud,Signal_heading,Ref_vel,Takeoff,planeo,Aux=Takeoff_acciones(Hilo.Qgc.Vector_estado,Hilo.waypoint,Aux) #Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Takeoff=Takeoff,Planeo=planeo) #Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG




def Nav(Hilo,Aux=[0,0,0,0]):
    Hilo.Qgc.waypoint=Hilo.waypoint
    while(Waypoint_nav(Hilo.Qgc.Vector_estado,Hilo.waypoint) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref_altitud,Signal_heading,Ref_vel,Aux,Planeo=nav_acciones(Hilo.Qgc.Vector_estado,Hilo.waypoint,Aux)#Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Planeo=Planeo)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Aux


def Land(Hilo,Aux=[0,0,0,0]):
    Hilo.Qgc.waypoint = Hilo.waypoint
    Rumbo_def=None
    while(Waypoint_land(Hilo.Qgc.Vector_estado) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref_altitud,Signal_heading,Ref_vel,Takeoff,planeo,Rumbo,Aux=Land_acciones(Hilo.Qgc.Vector_estado,Hilo.waypoint,Aux)#Calculo de las referencias para el control
        if Rumbo is not None and Rumbo_def is None:
            Rumbo_def=Rumbo
            print((Rumbo*180/math.pi),'Rumbo')
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Planeo=planeo,Takeoff=Takeoff,Ref_heading=Rumbo_def)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG

def Altitud(Hilo):
    while(Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock,Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref_altitud,Signal_heading,Ref_vel=[Hilo.Altitud_vuelo,0,100]
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Planeo=0)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG


#---------------------------------------MODOS DE VUELO BAJO NIVEL---------------------------------------------------------------

def Bajo_nivel(Hilo):
    while(Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref=[100,Hilo.pitch*math.pi/180,Hilo.Roll*math.pi/180]#Calculo de las referencias para el control
        Acciones=Acciones_Control_Bajo_nivel(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Hilo.Qgc.Verbose

def Bajo_nivel_2(Hilo):
    Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock, Hilo.Qgc.Cola)  # Recepcion de datos del simulador
    Rumbo=Hilo.Qgc.Vector_estado.yaw
    print(Rumbo,'Rumbo')
    while(Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock,Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref_altitud, Signal_heading, Ref_vel=[1200,Hilo.Qgc.Vector_estado.yaw,100]
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Ref_heading=Rumbo)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Hilo.Qgc.Verbose
#---------------------------------------MODOS DE VUELO ATERRIZAJE AUTONOMO--------------------------------------------------------------

def Cambio_Rumbo(Hilo):
    Rumbo=Hilo.Vision.Giro
    Contador=0
    print('Entrnado giro')
    while( Hilo.Get_vivo() and Contador<60):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock, Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref_altitud, Signal_heading, Ref_vel=[1200,Hilo.Qgc.Vector_estado.yaw,100]
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Ref_heading=Rumbo)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones), Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Contador+=1
    Hilo.Vision.Reset_giro()

def Desplazamiento_lateral(Hilo):
    Direccion=Hilo.Vision.Direccion
    Contador=0
    print('Entrnado Desplazamiento')
    while(Hilo.Get_vivo() and Contador<150):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock, Hilo.Qgc.Cola) #Recepcion de datos del simulador
        Ref_altitud, Signal_heading, Ref_vel=[1200, 0, 100]
        Planeo = Direccion*5*math.pi/180
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Planeo=Planeo)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones), Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Contador+=1
    Hilo.Vision.Reset_giro()

def Vuelo_estable(Hilo,Mission,Pinteresantes):
    Contador=0
    while(Hilo.Get_vivo() and Hilo.Vision.Cambio_Giro() and Contador<3000 and len(Mission)<2):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock,Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref_altitud, Signal_heading, Ref_vel = [1200, 0, 100]
        Acciones=Acciones_Control(Ref_altitud,Signal_heading,Ref_vel,Hilo.Qgc,Planeo=0)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Contador+=1

        if Hilo.Vision.Nueva_mission() == 1:
            Mission.append(Hilo.Vision.Get_Mission())
            Hilo.Vision.Reset_mission()

        if Hilo.Vision.Nuevo_Pinteresante() == 1 and len(Pinteresantes)<2:
            Pinteresantes.append(Hilo.Vision.Get_Pinteresantes())
            Hilo.Vision.Reset_Pinteresantes()

        if Contador>200 and not Hilo.Vision.IsActivo():
            if not Hilo.Vision.is_alive():
                Hilo.Vision = LV.Vision(Hilo.Qgc.Cola, Hilo.Qgc.Modelo,Hilo.Main.Texto)
                Hilo.Vision.start()
            Hilo.Vision.Activar()  # Se lanza la vision con vuelo estable
    Hilo.Vision.Matar()  # Al realiar un giro se detiene la parte de vision para evitar errores

    if Contador==3000:
        Reconocimiento=True
    else:
        Reconocimiento = False

    if len(Mission)>1:
        print('Mission completa')
        Aterrizaje=True
    else:
        Aterrizaje = False
    return Reconocimiento,Aterrizaje,Mission,Pinteresantes

def Fase_Reconocimiento(Hilo):
    Mission=[]
    Pinteresantes=[]
    while(Hilo.Get_vivo()):
        print('Vuelo estable')
        Flag_Reconocimiento,Flag_aterrizaje,Mission,Pinteresantes = Vuelo_estable(Hilo,Mission,Pinteresantes)  # Vuelo para captura de imagenes
        if Flag_aterrizaje:
            break
        if Hilo.Vision.Nuevo_Giro==1: #Cambio de rumbo
            print('Cambio rumbo')
            Cambio_Rumbo(Hilo)
            Hilo.Vision.Reset_giro()
        elif Hilo.Vision.Nuevo_Giro==2: #Desplazamiento lateral
            print('Desplazamiento')
            Desplazamiento_lateral(Hilo)
            Hilo.Vision.Reset_giro()
        if Flag_Reconocimiento:
            Hilo.Vision.Parar() #Se pausa el hilo de vision para realizar el reposicionamiento
            Mision_reconocimineto(Hilo,Pinteresantes)
    if Hilo.Get_vivo():
        Hilo.Vision.Matar()
        Hilo.Qgc.Mission=Crear_mision_aterrizaje(Mission,Hilo.Qgc)

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------MODOS DE VUELO COMPLEJOS---------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Aterrizaje_autonomo(Hilo): #Modo de vuelo para la identificacion de pistas y aterrizaje en ellas
    Fase_Reconocimiento(Hilo) #Vuelo para encontrar waypoints en pista
    try:
        Hilo.Hoja_Ruta.salir()
    except:
        None
    if Hilo.Get_vivo():
        Mission(Hilo)


def Mission(Hilo, Aux=[0, 0, 0, 0]): #Modo de vuelo mision en el que se combinan todos los posibles tipos de vuelo
    Hilo.Hoja_Ruta=LG.Hoja_ruta(Hilo.Main.raiz, Hilo.Qgc.Mission)
    for i in range(Hilo.Qgc.Mission.__len__()):
        Hilo.waypoint=Hilo.Qgc.Mission[i]
        if Hilo.Get_vivo():
            Hilo.Hoja_Ruta.Actualizar_waypoint(i)
            if Hilo.Qgc.Mission[i].Flight_mode == 0: #Modo depegue
                Takeoff(Hilo)
            elif Hilo.Qgc.Mission[i].Flight_mode == 1:#Modo Navegacion
                Aux = Nav(Hilo, Aux)
            elif Hilo.Qgc.Mission[i].Flight_mode == 2:#Modo Aterrizaje autonomo
                Aterrizaje_autonomo(Hilo)
            else:
                Land(Hilo)#Modo Aterrizaje simple
    Hilo.Hoja_Ruta.Actualizar_waypoint(i+1,True)
    Hilo.Main.Texto.insert("insert", "Fin mision\n")
    Hilo.Hoja_Ruta.salir()


#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------REFERENCIAS DE CONTROL SEGUN MODO DE VUELO---------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Takeoff_acciones(vector_Estado,waypoint,Aux):
    Signal_Heading,Aux,_=Heading(waypoint,vector_Estado,Aux)
    Ref_vel=150
    Takeoff=None
    planeo=0
    if vector_Estado.groundspeed<60:
        Ref_vel=150
        Ref_Altitud = vector_Estado.alt+5
        Takeoff = True
    elif vector_Estado.groundspeed>60 and vector_Estado.groundspeed<100:
        Ref_Altitud = vector_Estado.alt+10
        Takeoff = True
    else:
        Ref_Altitud = vector_Estado.alt*1.25
    return Ref_Altitud,Signal_Heading,Ref_vel,Takeoff,planeo,Aux

def nav_acciones(vector_Estado,waypoint,Aux):
    Ref_vel=waypoint.vel
    Ref_Altitud=waypoint.alt
    Signal_Heading,Aux,Planeo=Heading(waypoint,vector_Estado,Aux)
    return Ref_Altitud,Signal_Heading,Ref_vel,Aux,Planeo

def Land_acciones(vector_Estado,waypoint,Aux):
    Rumbo = vector_Estado.yaw
    Signal_Heading = vector_Estado.yaw
    planeo=None
    Takeoff=None
    if vector_Estado.groundspeed>75:
        Signal_Heading, Aux, _ = Heading(waypoint, vector_Estado, Aux)
        Ref_vel = vector_Estado.groundspeed*0.98
        Ref_Altitud = 200
        Rumbo=None
    elif vector_Estado.groundspeed>50 and vector_Estado.groundspeed<75:
        Takeoff=True
        planeo=0
        Ref_vel =  vector_Estado.groundspeed*0.9
        Ref_Altitud = vector_Estado.alt*1.2
    elif vector_Estado.groundspeed>35 and vector_Estado.groundspeed<50:
        Signal_Heading, Aux, _ = Heading(waypoint, vector_Estado, Aux)
        Rumbo = None
        Takeoff = True
        planeo=0
        Ref_vel =  vector_Estado.groundspeed*0.65
        Ref_Altitud = vector_Estado.alt*1.8
    else:
        planeo=0
        Ref_vel =0
        Ref_Altitud = vector_Estado.alt*1.9
    return Ref_Altitud,Signal_Heading,Ref_vel,Takeoff,planeo,Rumbo,Aux


#---------------------------------------CALCULO DE LA REFERENCIA DE BEARING---------------------------------------------------

def Heading(waypoint,vector_Estado,Aux):
    Planeo=None
    Heading_1=Aux[0]
    contH=Aux[1]
    Bearing_1=Aux[2]
    contB=Aux[3]
    # Calculo bearing
    dlon = (waypoint.lon - vector_Estado.lon) * (math.pi / 180)
    y = math.sin(dlon) * math.cos((waypoint.lat * math.pi) / 180)
    x = math.cos(vector_Estado.lat * math.pi / 180) * math.sin(waypoint.lat * math.pi / 180) - math.sin(vector_Estado.lat * math.pi / 180) * math.cos(waypoint.lat * math.pi / 180) * math.cos(dlon)
    bearing = math.atan2(y, x)
    if bearing < 0:
        bearing = bearing + 2 * math.pi
    Heading = vector_Estado.yaw
    if Heading < 0:
        Heading = Heading + 2 * math.pi
    cambioH = Heading - Heading_1
    Heading_1 = Heading

    if (cambioH > math.pi):
        contH = contH - 1
    else:
        if (cambioH < -math.pi):
            contH = contH + 1

    cambioB = bearing - Bearing_1
    Bearing_1 = bearing
    if (cambioB > math.pi):
        contB = contB - 1
    else:
        if (cambioB < -math.pi):
            contB = contB + 1

    total_HEADING = contH * 2 * math.pi + Heading
    total_BEARING = contB * 2 * math.pi + bearing
    Heading_ERROR = total_BEARING - total_HEADING
    Heading_ERROR = Heading_ERROR % (2 * math.pi)

    if Heading_ERROR > math.pi:
        Heading_ERROR = Heading_ERROR - 2 * math.pi
    if Heading_ERROR < -math.pi:
        Heading_ERROR = Heading_ERROR + 2 * math.pi

    N_max = 1 / math.cos(math.pi*35/180)
    V = math.sqrt(pow((vector_Estado.groundspeed*0.3048),2) + pow((vector_Estado.vz*0.3048),2))
    R_min = math.pow(V,2) / (9.81 * math.sqrt(math.pow(N_max,2) - 1))

    Lat1 = (vector_Estado.lat * math.pi ) / 180
    Lat2 = waypoint.lat * math.pi / 180

    Long1 = (vector_Estado.lon * math.pi) / 180
    Long2 = waypoint.lon * math.pi / 180
    dist2Waypoint = abs(6371e3 * math.acos(math.cos(Lat1) * math.cos(Lat2) * math.cos(Long2 - Long1) + math.sin(Lat1) * math.sin(Lat2)))

    if (dist2Waypoint < R_min):
        Heading_ERROR = 0
        Planeo=0
    return Heading_ERROR,[Heading_1,contH,Bearing_1,contB],Planeo

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------FUNCIONES AUXILIARES-------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Filtro(Lista,Numero):
    Ultimo_indice = len(Lista)
    if Ultimo_indice>Numero:
        Diferencia=Lista[Ultimo_indice-1]-Lista[Ultimo_indice-2]
        if Diferencia >0.00000001 or Diferencia <-0.00000001:
            Signo=Diferencia/abs(Diferencia)
        else:
            Signo=1
        if abs(Diferencia)<0.0001:
            Primer_indice = Ultimo_indice - Numero
            sublista = Lista[Primer_indice:Ultimo_indice]
            Valor = np.mean(sublista)
        else:
            Valor=Lista[Ultimo_indice-2]+0.0001*Signo
    else:
        Valor=Lista[Ultimo_indice-1]
    return Valor

def Crear_mision_aterrizaje(Puntos_GPS,Qgc,Reconocimiento=False):
    print(Puntos_GPS,'GPS detectados')
    #Calculo de las alturas
    alt_1 = Qgc.Vector_estado.alt
    #Calculo de la recta que forma la pista
    x1 = Puntos_GPS[0][0]
    y1 = Puntos_GPS[0][1]
    x2 = Puntos_GPS[1][0]
    y2 = Puntos_GPS[1][1]
    Dif_lat = (x2 - x1)
    if abs(Dif_lat)>0.0005: #No es vertical completamente
        print('Metodo 1')
        print(abs(Dif_lat))
        Dif_lon=(y2-y1)
        Pendiente=Dif_lon/Dif_lat
        Interseccion=y2-Pendiente*x2
        #Calculo de las posiciones GPS
        x3=2*x2-x1
        y3=Pendiente*x3+Interseccion+3*(y2-y1)
        x4=x1-3*(x2-x1)
        y4=Pendiente*x4+Interseccion-4*(y2-y1)
        x5=x1-1.5*(x2-x1)
        y5=Pendiente*x4+Interseccion-2*(y2-y1)
        x6=x1+((x2-x1)/2)
        y6=Pendiente*x6+Interseccion
        x7=x3
        y7=y3
    else:
        print('Metodo 2')
        signo=(y2-y1)/abs((y2-y1))
        #Calculo de las posiciones GPS
        x3=x1
        y3=y2+signo*1.5/60
        x4=x1
        y4=y1-signo*3/60
        x5=x1
        y5=y1-signo*1.2/60
        x6=x1
        y6=y1-signo*0.2/60
        x7=x1
        y7=y1+signo*0.8/60
    # Creacion de la mision
    Mision = []
    if Reconocimiento==False: #Mission de aterrizaje
        print([x3, y3], 'Punto 1')
        Mision.append(Waypoint(x3,y3,alt_1,125,1))
        print([x4, y4], 'Punto 2')
        Mision.append(Waypoint(x4,y4,700,125,1))
        print([x5, y5], 'Punto 3')
        Mision.append(Waypoint(x5,y5,450,125,1))
        print([x6, y6], 'Punto 4')
        Mision.append(Waypoint(x6,y6,350,100,1))
        print([x7, y7], 'Punto 5')
        Mision.append(Waypoint(x7,y7,100,150,3))
    elif Reconocimiento==True:
        print([x3, y3], 'Punto 1')
        Mision.append(Waypoint(x3,y3,alt_1,150,1))
        print([x4, y4], 'Punto 2')
        Mision.append(Waypoint(x4,y4,900,150,1))
        print([x5, y5], 'Punto 3')
        Mision.append(Waypoint(x5,y5,1000,150,1))
        print([x6, y6], 'Punto 4')
        Mision.append(Waypoint(x6,y6,1100,150,1))
        print([x7, y7], 'Punto 5')
        Mision.append(Waypoint(x7,y7,1200,150,2))
    return Mision


def Mision_reconocimineto(Hilo,Pinteresante):
    print('Mision de reconocimiento')
    Lista=Pinteresante
    Numero_puntos=len(Lista)
    if Numero_puntos>1:
        Hilo.Qgc.Mission=Crear_mision_aterrizaje(Pinteresante,Hilo.Qgc,Reconocimiento=True)
        print('Mision activa reconocimiento')
        Mission(Hilo)
    else:
        print('No hay mision')





#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------CLASES AUXILIARES-------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

class Verbose_controls():
    def __init__(self):
    #Eje tiempo
        self.Eje_x= []
    #Posicion Espacial
        self.Lat_actual=[]
        self.Lon_actual=[]
        self.Lat_objetivo=[]
        self.Lon_objetivo=[]
    #Control_aleron
        self.Signal_heading=[]
        self.Ref_heading=[]

        self.Ref_roll=[]
        self.Signal_roll=[]
        self.Control_aileron=[]
    #Control_Elevador
        self.Ref_altitud=[]
        self.Signal_altitud=[]
        self.Ref_pitch=[]
        self.Signal_pitch=[]
        self.Control_elevador=[]
    #Control_Acelerador
        self.Ref_velocidad=[]
        self.Signal_velocidad=[]
        self.Control_acelerador=[]
    # Control_Timon
        self.Ref_Rudder = []
        self.Signal_Rudder = []
        self.Control_Timon = []
    def Update(self,n):
        self.Eje_x.append(int(n))

    def Plot_Posicion(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Lat_actual, self.Lon_actual)#,self.Lat_objetivo, self.Lon_objetivo)
            ax.legend(( 'Posicion'))#,'Waypoint'))
            if Hilo.Verbose_options.Posicion_save:
                fig.savefig('Posicion.png')
            return fig
        except:
            print('No se puede plotear la Posicion')
            return None

    def Plot_altitud(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_altitud[400:],self.Eje_x[400:], self.Signal_altitud[400:],self.Eje_x[400:], self.Control_elevador[400:])
            ax.legend(( 'Ref_altitud','Signal_altitud','Control_elevador'))
            if Hilo.Verbose_options.Altitud_save:
                fig.savefig('altitud.png')
            return fig
        except:
            print('No se puede plotear la altura')
            return None

    def Plot_Pitch(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_pitch[400:],self.Eje_x[400:], self.Signal_pitch[400:],self.Eje_x[400:], self.Control_elevador[400:])
            ax.legend(( 'Ref_pitch','Signal_pitch','Control_elevador'))
            if Hilo.Verbose_options.pitch_save:
                fig.savefig('Pitch.png')
            return fig
        except:
            print('No se puede plotear el pitch')
            return None

    def Plot_Roll(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_roll[400:],self.Eje_x[400:], self.Signal_roll[400:],self.Eje_x[400:], self.Control_aileron[400:])
            ax.legend(( 'Ref_roll','Signal_roll','Control_aleron'))
            if Hilo.Verbose_options.Roll_save:
                fig.savefig('Roll.png')
            return fig
        except:
            print('No se puede plotear el roll')
            return None

    def Plot_Heading(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_heading[400:],self.Eje_x[400:], self.Signal_heading[400:],self.Eje_x[400:], self.Ref_roll[400:])
            ax.legend(( 'Ref_Heading','Signal_Heading','Ref_Roll'))
            if Hilo.Verbose_options.Heading_save:
                fig.savefig('Heading.png')
            return fig
        except:
            print('No se puede plotear el Heading')
            return None

    def Plot_Vel(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_velocidad[400:],self.Eje_x[400:], self.Signal_velocidad[400:],self.Eje_x[400:], self.Control_acelerador[400:])
            ax.legend(( 'Ref_velocidad','Signal_velocidad','Control_acelerador'))
            if Hilo.Verbose_options.Vel_save:
                fig.savefig('Vel.png')
            return fig
        except:
            print('No se puede plotear la velocidad')
            return None

    def Plot_Rudder(self,Hilo):
        try:
            fig, ax = plt.subplots()
            ax.plot( self.Eje_x[400:], self.Ref_Rudder[400:],self.Eje_x[400:], self.Signal_Rudder[400:],self.Eje_x[400:], self.Control_Timon[400:])
            ax.legend(( 'Ref_Rudder','Signal_Rudder','Control_Vel'))
            if Hilo.Verbose_options.Vel_save:
                fig.savefig('Rudder.png')
            return fig
        except:
            print('No se puede plotear el Rudder')
            return None

class Waypoint():
    def __init__(self,lat,lon,alt,vel,FM):
        self.lat=lat
        self.lon=lon
        self.alt=alt
        self.vel=vel
        self.Flight_mode=FM # 0-->Takeoff, 1-->Nav, 2-->AutoLand, 3-->Land

#Clase vector de estados
class Vector_Estado():
    def __init__(self):
        #Inputs
        self.elevator=0
        self.flaps=0
        self.Throttle=0
        self.ailerons=0
        self.rudder=0
        #Eurler angles
        self.roll=0
        self.pitch=0
        self.yaw=0
        #Position
        self.lat=0
        self.lon=0
        self.alt=0
        #Relative velocities
        self.vx=0
        self.vy=0
        self.vz=0
        self.groundspeed=0

    def update_sensor (self,socket,Cola=None):
        data,addr=socket.recvfrom(1024)
        data = data.decode("utf-8")
        data = data.split(',')
        self.roll=float(data[0])*(math.pi/180)
        self.pitch=float(data[1])*(math.pi/180)
        self.yaw=float(data[2])*(math.pi/180)
        self.lat = float(data[3])
        self.lon = float(data[4])
        self.alt = float(data[5])
        self.vx = float(data[6])
        self.vy = float(data[7])
        self.vz = float(data[8])
        self.ailerons = float(data[9])
        self.elevator = float(data[10])
        self.rudder = float(data[11])
        self.Throttle = float(data[12])
        self.groundspeed=float(data[13])
        if Cola is not None:
            Cola.put([self.lat,self.lon])

    def pack_controls(self,Acciones):
        Acciones_Control = [Acciones[0], ',', Acciones[1], ',', Acciones[2], ',', Acciones[3], '\n'] #[Alerones,elevador,rudder,accelerador]
        mensaje = ''.join(str(e) for e in Acciones_Control)
        Enviar = str.encode(mensaje)
        return Enviar



#Clase con los PIDs del modelo
class PIDs():
    def __init__(self):
        self.sample_time=1/50
        self.PID_Roll=PID(1.8,1.5,0,output_limits=(-0.9,0.9),sample_time=self.sample_time)
        self.PID_Rudder = PID(-2.8, -0.175, 0, output_limits=(-0.19, 0.19), sample_time=self.sample_time)
        self.PID_Rudder_Rumbo = PID(3.2, 0.35, 0, output_limits=(-0.19, 0.19), sample_time=self.sample_time)
        self.PID_Heading=PID(-1.45,-0.35,-0.15,output_limits=(-(35*math.pi/180),(35*math.pi/180)),sample_time=self.sample_time)
        self.PID_Heading_Rumbo = PID(0.25, 0.2, 0.15, output_limits=(-(35 * math.pi / 180), (35 * math.pi / 180)),sample_time=self.sample_time)
        self.PID_Pitch=PID(-2.3,-1.7,0,output_limits=(-0.9,0.9),sample_time=self.sample_time)
        self.PID_AirSpeed=PID(0.06,0.03,0.01,output_limits=(0,1),sample_time=self.sample_time)
        self.PID_Altitud=PID(0.0018,0.00085,0,output_limits=(-(10*math.pi/180),(5*math.pi/180)),sample_time=self.sample_time)
        self.Rudder_Const=0.15
