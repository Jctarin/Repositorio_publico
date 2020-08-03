from GUI.PID import *
import math
import socket as s
from matplotlib import pyplot as plt
import numpy as np
import queue as q
from tensorflow.keras.models import load_model


#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------CLASE QGROUNCONTROL--------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
class QGC(): #Clase principal que reune todos los objetos necesarios para el vuelo autonomo
    def __init__(self):
        self.Control = PIDs() #Estructura de PIDs
        self.Vector_estado = Vector_Estado() #Estructura para tratar los sensores y actuadores
        self.Mission = self.Default_mission() #Mision de vuelo
        self.Verbose=Verbose_controls() #Estructura que recaba datos de vuelo
        self.PortAdress_send=("localhost",9900) #Direccion de envio de los actuadores
        self.Cola=q.LifoQueue() #Pila de trabajo para compartir informacion con el hilo de VA
        self.sock=sock=s.socket(s.AF_INET,s.SOCK_DGRAM) #Socket para la comunicacion
        self.PortAdress_recv=("localhost",9999)
        self.Modelo=0
        self.Cargar_modelo()
        self.waypoint=Waypoint(0,0,0,0,0)
        sock.bind(self.PortAdress_recv) #Comienza la escucha del puerto de recepcion de datos

    def Cargar_modelo(self):
        try:
            modelo = r'C:\Users\Juatarto\Desktop\TFM\Arquitecturas\Test\Epoca_10\Modelo_Capas_6_RGB_Epocas_10_Neuronas_256_Filtros_32_relu.h5'
            cnn = load_model(modelo)
            self.Modelo=cnn
        except:
            print('No hay modelo')
            self.Modelo=None


    def Default_mission(self): #Metodo de carga de mision
        Mission=[]
        Mission.append(Waypoint(0, 0, 500, 150, 1))
        Mission.append(Waypoint(0, 0, 500, 150, 1))
        return Mission
#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------FUNCIONES DE CONTROL-------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Acciones_Control_Bajo_nivel(Ref,Qgc): #Bucles de control de bajo nivel (Velocidad,Pitch,Roll)
    #Bucle Acelerador
    Qgc.Verbose.Ref_velocidad.append(Ref[0])#Almacena valores
    Qgc.Control.PID_AirSpeed.setpoint=Ref[0]
    Qgc.Verbose.Signal_velocidad.append(Qgc.Vector_estado.groundspeed)#Almacena valores
    Acelerador=Qgc.Control.PID_AirSpeed(Qgc.Vector_estado.groundspeed)
    Qgc.Verbose.Control_acelerador.append(Acelerador)#Almacena valores

    #Bucle elevador
    Qgc.Verbose.Ref_pitch.append(Ref[1])#Almacena valores
    Ref[1] = Filtro(Qgc.Verbose.Ref_pitch, 1)
    Qgc.Control.PID_Pitch.setpoint=Ref[1]
    Qgc.Verbose.Signal_pitch.append(Qgc.Vector_estado.pitch)#Almacena valores
    Elevador=Qgc.Control.PID_Pitch(Qgc.Vector_estado.pitch)
    Qgc.Verbose.Control_elevador.append(Elevador)#Almacena valores

    #Bucle Aleron
    Qgc.Verbose.Ref_roll.append(Ref[2])#Almacena valores
    Ref[2] = Filtro(Qgc.Verbose.Ref_roll, 1)
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
    Timon=Aleron*Qgc.Control.Rudder_Const

    return [Aleron, Elevador, Timon, Acelerador]

def Acciones_Control_Alto_nivel(Ref,Qgc): #Bucles de control de alto nivel

    #Bucle Elevador
    Qgc.Verbose.Ref_altitud.append(Ref[1])#Almacena valores
    Qgc.Control.PID_Altitud.setpoint=Ref[1]
    Qgc.Verbose.Signal_altitud.append(Qgc.Vector_estado.alt)#Almacena valores
    Ref_pitch=Qgc.Control.PID_Altitud(Qgc.Vector_estado.alt)


    #Bucle Aleron
    Qgc.Verbose.Ref_heading.append(0)#Almacena valores
    Qgc.Control.PID_Heading.setpoint = 0
    Qgc.Verbose.Signal_heading.append(Ref[0])#Almacena valores
    Ref[0] = Filtro(Qgc.Verbose.Signal_heading, 4)
    Ref_Roll=Qgc.Control.PID_Heading(Ref[0])#heading


    return [Ref_pitch,Ref_Roll]

def Acciones_Control(Ref,Qgc):#Funcion general que enlaza los bucles de alto y bajo nivel (Heading,Vel,Altitud)
    Ref_alto_nivel=Acciones_Control_Alto_nivel([Ref[0],Ref[2]],Qgc)
    Acciones=Acciones_Control_Bajo_nivel([Ref[1],Ref_alto_nivel[0],Ref_alto_nivel[1]],Qgc)
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
    if  vector_Estado.alt<0 and vector_Estado.vx<5:
        return 0
    else:
        return 1

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------MODOS DE VUELO BASICOS-----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

#---------------------------------------MODOS DE VUELO BASICOS-----------------------------------------------------------------------
def Takeoff(Hilo,Aux=[0,0,0,0]):
    while(Waypoint_takeoff(Hilo.Qgc.Vector_estado,Hilo.waypoint) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock) #Recepcion de datos del simulador
        Ref,Aux=Takeoff_acciones(Hilo.Qgc.Vector_estado,Hilo.waypoint,Aux) #Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref,Hilo.Qgc) #Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Aux


def Nav(Hilo,Aux=[0,0,0,0]):
    Hilo.Qgc.waypoint=Hilo.waypoint
    while(Waypoint_nav(Hilo.Qgc.Vector_estado,Hilo.waypoint) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref,Aux=nav_acciones(Hilo.Qgc.Vector_estado,Hilo.waypoint,Aux)#Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Aux

def Land(Hilo):
    while(Waypoint_land(Hilo.Qgc.Vector_estado) and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref=Land_acciones(Hilo.Qgc)#Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG

def Altitud(Hilo):
    while(Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock,Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref=[0,100,Hilo.Altitud_vuelo]
        Acciones=Acciones_Control(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG


#---------------------------------------MODOS DE VUELO TEST-----------------------------------------------------------------------

def Prueba(Qgc):
    Contador=0
    Aux=[0,0,0,0]
    while(Contador<4000):
        Contador+=1
        Qgc.Vector_estado.update_sensor(Qgc.sock)#Recepcion de datos del simulador
        Ref,Aux=nav_acciones(Qgc.Vector_estado,Qgc.Mission[0],Aux)#Calculo de las referencias para el control
        Acciones=Acciones_Control(Ref,Qgc)#Calculo de las acciones de control
        Qgc.sock.sendto(Qgc.Vector_estado.pack_controls(Acciones),Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Qgc.Verbose

#---------------------------------------MODOS DE VUELO BAJO NIVEL---------------------------------------------------------------

def Bajo_nivel(Hilo):
    while(Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock)#Recepcion de datos del simulador
        Ref=[100,Hilo.pitch*math.pi/180,Hilo.Roll*math.pi/180]#Calculo de las referencias para el control
        Acciones=Acciones_Control_Bajo_nivel(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
    return Hilo.Qgc.Verbose
#---------------------------------------MODOS DE VUELO ATERRIZAJE AUTONOMO--------------------------------------------------------------

def Giro_izquierda(Hilo,Limite):
    while(Limite>1and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock, Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref=[90,0,(1*math.pi/180)]#Calculo de las referencias para el control
        Acciones=Acciones_Control_Bajo_nivel(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones), Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Limite -= 1
def Giro_derecha(Hilo,Limite):
    while(Limite>1and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock, Hilo.Qgc.Cola) #Recepcion de datos del simulador
        Ref=[90,0,(-1*math.pi/180)]#Calculo de las referencias para el control
        Acciones=Acciones_Control_Bajo_nivel(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones), Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Limite -= 1

def Fase_Reconocimiento(Hilo):
    Contador_ciclos=0 #Evalua si se ha alejado mucho de una zona susceptible de contener pistas
    Hilo.Vision.start() #Inicia el hilo de vision pero permanece a la espera
    while(Hilo.Get_vivo()):
        Contador_ciclos+=1
        Giro=Hilo.Vision.Get_Giro() #Evalua si existe un Giro que realizar
        if Giro==1:
            print('Empieza giro izquierda')
            Hilo.Vision.Parar() #Al realiar un giro se detiene la parte de vision para evitar errores
            Giro_izquierda(Hilo,100) #Se realiza una maniobra de giro
            Hilo.Vision.Giro=0
            print('Termina giro derecha')
            Contador_ciclos = 0
        elif Giro==2:
            print('Empieza giro derecha')
            Hilo.Vision.Parar() #Al realiar un giro se detiene la parte de vision para evitar errores
            Giro_derecha(Hilo,100) #Se realiza una maniobra de giro
            Hilo.Vision.Giro=0
            print('Termina giro izquierda')
            Contador_ciclos=0
        print('Planeo')
        Planeo(Hilo,100) #Tras girar se debe estabilizar la nave o continuar volando estable si no ha habido giro
        Hilo.Vision.Activar() #Se lanza la vision con vuelo estable
        if Hilo.Vision.Mission()>1:
            break
        if Contador_ciclos>20:
            Hilo.Vision.Parar() #Se pausa el hilo de vision para realizar el reposicionamiento
            Mision_reconocimineto(Hilo)
            Contador_ciclos=0
    if Hilo.Get_vivo():
        Hilo.Qgc.Mission=Crear_mision_aterrizaje(Hilo.Vision.Get_Mission(),Hilo.Qgc)


def Planeo(Hilo,Limite):
    while(Limite>1 and Hilo.Get_vivo()):
        Hilo.Qgc.Vector_estado.update_sensor(Hilo.Qgc.sock,Hilo.Qgc.Cola)#Recepcion de datos del simulador
        Ref=[90,0,0]#Calculo de las referencias para el control
        Acciones=Acciones_Control_Bajo_nivel(Ref,Hilo.Qgc)#Calculo de las acciones de control
        Hilo.Qgc.sock.sendto(Hilo.Qgc.Vector_estado.pack_controls(Acciones),Hilo.Qgc.PortAdress_send)  # Envio de las acciones de control a FG
        Limite-=1



#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------MODOS DE VUELO COMPLEJOS---------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Aterrizaje_autonomo(Hilo): #Modo de vuelo para la identificacion de pistas y aterrizaje en ellas
    Fase_Reconocimiento(Hilo) #Vuelo para encontrar waypoints en pista
    if Hilo.Get_vivo():
        Mission(Hilo)


def Mission(Hilo, Aux=[0, 0, 0, 0], Vision=0): #Modo de vuelo mision en el que se combinan todos los posibles tipos de vuelo
    for i in range(Hilo.Qgc.Mission.__len__()):
        print(i, 'Nuevo waypoint')
        Hilo.waypoint=Hilo.Qgc.Mission[i]
        if Hilo.Get_vivo():
            if Hilo.Qgc.Mission[i].Flight_mode == 0: #Modo depegue
                Aux = Takeoff(Hilo, Aux)
            elif Hilo.Qgc.Mission[i].Flight_mode == 1:#Modo Navegacion
                Aux = Nav(Hilo, Aux)
            elif Hilo.Qgc.Mission[i].Flight_mode == 2:#Modo Aterrizaje autonomo
                Aterrizaje_autonomo(Hilo)
            else:
                Land(Hilo)#Modo Aterrizaje simple
    print('Fin mision')
    return Hilo.Qgc.Verbose

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------REFERENCIAS DE CONTROL SEGUN MODO DE VUELO---------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Takeoff_acciones(vector_estado,waypoint,Aux):
    Ref_vel=150
    Ref_Heading,Aux=Heading(waypoint,vector_estado,Aux)
    if vector_estado.groundspeed>70:
        Ref_Altitud=vector_estado.alt*1.2
    else:
        Ref_Altitud=vector_estado.alt*1.2
    return [0,Ref_vel,Ref_Altitud],Aux

def nav_acciones(vector_Estado,waypoint,Aux):
    Ref_vel=waypoint.vel
    Ref_alt=waypoint.alt
    Heading_ERROR,Aux=Heading(waypoint,vector_Estado,Aux)
    return [Heading_ERROR,Ref_vel,Ref_alt],Aux

def Land_acciones(Qgc):
    Ref_Heading=0
    Ref_vel=0
    Ref_Altitud=0
    if Qgc.Vector_estado.alt>150:
        Ref_vel=55
        Ref_Altitud = Qgc.Vector_estado.alt-150
    elif Qgc.Vector_estado.alt>80 and Qgc.Vector_estado.alt<150:
        Ref_vel=48
        Ref_Altitud = Qgc.Vector_estado.alt*1.1
    elif Qgc.Vector_estado.alt>20 and Qgc.Vector_estado.alt<80:
        Ref_vel=35
        Ref_Altitud = Qgc.Vector_estado.alt*1.24
    elif Qgc.Vector_estado.alt<5:
        Ref_vel=0
        Ref_Altitud=0
    return [Ref_Heading,Ref_vel,Ref_Altitud]

def nav_acciones_IA(Qgc,Aux):
    Ref_vel=Qgc.waypoint.vel
    Ref_alt=Qgc.waypoint.alt
    Heading_ERROR,Aux=Heading(Qgc.waypoint,Qgc.vector_Estado,Aux)
    return [Heading_ERROR,Ref_vel,Ref_alt],Aux


#---------------------------------------CALCULO DE LA REFERENCIA DE BEARING---------------------------------------------------

def Heading(waypoint,vector_Estado,Aux):
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

    if (dist2Waypoint <2* R_min):
        Heading_ERROR = 0
    return Heading_ERROR,[Heading_1,contH,Bearing_1,contB]

#------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------FUNCIONES AUXILIARES-------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

def Filtro(Lista,Numero):
    Ultimo_indice = len(Lista)
    if Ultimo_indice>Numero:
        Primer_indice = Ultimo_indice - Numero
        sublista = Lista[Primer_indice:Ultimo_indice]
        Valor = np.mean(sublista)
    else:
        Valor=Lista[Ultimo_indice-1]
    return Valor

def Crear_mision_aterrizaje(Puntos_GPS,Qgc):
    print(Puntos_GPS,'GPS detectados')
    #Calculo de la recta que forma la pista
    x1 = Puntos_GPS[0][0]
    y1 = Puntos_GPS[0][1]
    x2 = Puntos_GPS[1][0]
    y2 = Puntos_GPS[1][1]
    Dif_lat = (x2 - x1)
    if Dif_lat>0.0000005: #No es vertical completamente
        Dif_lon=(y2-y1)
        Pendiente=Dif_lon/Dif_lat
        Interseccion=y2-Pendiente*x2
        #Calculo de las posiciones GPS
        x3=2*x2-x1
        y3=Pendiente*x3+Interseccion+3*(y2-y1)
        x4=x1-1.5*(x2-x1)
        y4=Pendiente*x4+Interseccion-2*(y2-y1)
        x5=x1-3*(x2-x1)
        y5=Pendiente*x5+Interseccion-4*(y2-y1)
        x6=x1+((x2-x1)/2)
        y6=Pendiente*x6+Interseccion
        #Calculo de las alturas
        alt_1 = Qgc.Vector_estado.alt
    else:
        #Calculo de las posiciones GPS
        x3=x1
        y3=y2+4*(y2-y1)
        x4=x1
        y4=y1-5*(y2-y1)
        x5=x1
        y5=y1-2*(y2-y1)
        x6=x1
        y6=y5
        #Calculo de las alturas
        alt_1 = Qgc.Vector_estado.alt
    #Creacion de la mision
    Mision=[]
    print([x3,y3],'Punto 1')
    Mision.append(Waypoint(x3,y3,alt_1,150,1))
    print([x4, y4], 'Punto 2')
    Mision.append(Waypoint(x4,y4,800,150,1))
    print([x5, y5], 'Punto 3')
    Mision.append(Waypoint(x5,y5,600,150,1))
    print([x6, y6], 'Punto 4')
    Mision.append(Waypoint(x6,y6,500,80,1))
    print(Mision,'Mision')
    Mision.append(Waypoint(x6,y6,200,150,3))
    print(Mision,'Mision')
    return Mision


def Mision_reconocimineto(Hilo):
    print('Mision de reconocimiento')
    Lista=Hilo.Vision.Get_Pinteresantes()
    Numero_puntos=len(Lista)
    x=0
    if Numero_puntos>1:
        Mision=[]
        for Punto in Lista:
            x+=1
            if x>2 or x==Numero_puntos-1: #Solo se necesitan dos puntos para que el avion coja el rumbo en el que detectó pista
                break
            Mision.append(Waypoint(Punto[0],Punto[1],500,100,1)) #Vuelo por zonas de pista en modo navegacion para llegar orientado
        Hilo.Pinteresantes=[] #Borramos los antiguos puntos reconocidos para no dar vueltas en circulo si nunca se consigue alinear
        Hilo.Qgc.Mission=Mision
        Mission(Hilo)
    else:
        Numero=np.random.rand()
        if Numero>0.5:
            Giro_derecha(Hilo,200)
        else:
            Giro_izquierda(Hilo,200)

#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------CLASES AUXILIARES-------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------

class Verbose_controls():
    def __init__(self):
    #Eje tiempo
        self.Eje_x=[]
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
        self.Cola=q.Queue()

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
            ax.plot( self.Eje_x, self.Ref_altitud,self.Eje_x, self.Signal_altitud,self.Eje_x, self.Control_elevador)
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
            ax.plot( self.Eje_x, self.Ref_pitch,self.Eje_x, self.Signal_pitch,self.Eje_x, self.Control_elevador)
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
            ax.plot( self.Eje_x, self.Ref_roll,self.Eje_x, self.Signal_roll,self.Eje_x, self.Control_aileron)
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
            ax.plot( self.Eje_x, self.Ref_heading,self.Eje_x, self.Signal_heading,self.Eje_x, self.Ref_roll)
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
            ax.plot( self.Eje_x, self.Ref_velocidad,self.Eje_x, self.Signal_velocidad,self.Eje_x, self.Control_acelerador)
            ax.legend(( 'Ref_velocidad','Signal_velocidad','Control_acelerador'))
            if Hilo.Verbose_options.Vel_save:
                fig.savefig('Vel.png')
            return fig
        except:
            print('No se puede plotear la velocidad')
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
    #     print(Acciones,'Acciones')
        Acciones_Control = [Acciones[0], ',', Acciones[1], ',', Acciones[2], ',', Acciones[3], '\n'] #[Alerones,elevador,rudder,accelerador]
        mensaje = ''.join(str(e) for e in Acciones_Control)
        Enviar = str.encode(mensaje)
        return Enviar



#Clase con los PIDs del modelo
class PIDs():
    def __init__(self):
        self.sample_time=1/20
        self.PID_Roll=PID(1.8,1.5,0,output_limits=(-0.9,0.9),sample_time=self.sample_time)
        self.PID_Heading=PID(-1.6,-0.08,-0.7,output_limits=(-(35*math.pi/180),(35*math.pi/180)),sample_time=self.sample_time,setpoint=0)
        self.PID_Pitch=PID(-2.3,-1.7,0,output_limits=(-0.9,0.9),sample_time=self.sample_time)
        self.PID_AirSpeed=PID(1.1,0.8,0,output_limits=(0,0.9),sample_time=self.sample_time)
        self.PID_Altitud=PID(0.0018,0.00085,0,output_limits=(-(10*math.pi/180),(10*math.pi/180)),sample_time=self.sample_time)
        self.Rudder_Const=0.15
