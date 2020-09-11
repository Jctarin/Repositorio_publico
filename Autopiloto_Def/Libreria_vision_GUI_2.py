import numpy as np
import math
import requests
from PIL import Image
import Autopiloto_Def.Modulo_vision_GUI as mv
import threading


#----------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------ZONA VISION E IA------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------


class Vision (threading.Thread): #Hilo de vision e inteligencia artificial
    def __init__(self,Cola,Modelo,Text):
        threading.Thread.__init__(self)
        self.Activo=0
        self.modelo=Modelo
        self.Pos_GPS=[0,0]
        self.lane_image=0
        self.Cola=Cola
        self.mission=0
        self.Giro=0
        self.Direccion=0
        self.Nuevo_Giro=0
        self.Pinteresantes=0
        self.Vivo=1
        self.Limite=60
        self.Text=Text
    def run(self):
        while (1):
            if self.Vivo:
                if self.Activo :
                    try:
                        self.lane_image=self.Captura_imagen() #Captura la imagen
                    except:
                        self.lane_image=None
                    if self.lane_image is not None and self.Activo==1:
                        self.Capturar_Datos() #Capturo la ultima posicion GPS almacenada que corresponde con la imagen
                        try:
                            Flag,result=IA(self) #Proceso de segmentacion con Inteligencia artificial
                        except:
                            Flag=False
                        if Flag==True and self.Activo==1:

                            VA(self,result) #Proceso de vision artificial para reconocer la pista
            else:
                break

    def Matar(self):
        self.Vivo=0
        if self.Activo==1:
            self.Activo=0

    def Girar(self,Giro): #Proteger la variable si el vuelo no es estable
        if self.Activo: #Si esta autorizado el hilo a cambiar el valor de giro
            self.Nuevo_Giro=1
            self.Giro=Giro*math.pi/180

    def Reset_mission(self):
        self.mission=0

    def Reset_giro(self):
        self.Nuevo_Giro=0

    def Cambio_Giro(self):
        if self.Nuevo_Giro==1 or self.Nuevo_Giro==2:
            return 0
        else:
            return 1

    def Desplazar(self,Direccion):
        if self.Activo:
            self.Nuevo_Giro=2
            self.Direccion=Direccion

    def Parar(self): #Parar el Hilo
        if self.Activo==1:
            self.Activo=0


    def Activar(self): #Activar el Hilo
        if self.Activo==0:
            self.Activo=1

    def IsActivo(self):
        if self.Activo == 0:
            return 0
        else:
            return 1

    def Capturar_Datos(self):
        self.Pos_GPS=self.Cola.get()
        return 0

    def Mission(self):
        try:
            return len(self.mission)
        except:
            return 0

    def Nueva_mission(self):
        if self.Mission()>0:
            return 1
        else:
            return 0

    def Get_Mission(self):
        return self.mission

    def Captura_imagen(self):
        m = Image.open(requests.get('http://localhost:1111/screenshot.jpg', stream=True).raw)
        frame = np.asarray(m)
        lane_image = np.copy(frame)  # Pasa el frame a matriz numpy
        return lane_image

    def Nuevo_Pinteresante(self):
        if self.Pinteresantes_len()>0:
            return 1
        else:
            return 0

    def Pinteresantes_len(self):
        try:
            return len(self.Pinteresantes)
        except:
            return 0

    def Reset_Pinteresantes(self):
        self.Pinteresantes=0

    def Get_Pinteresantes(self):
        return self.Pinteresantes

def IA(self):
    resolucion = 30  # Tamaño de las celdas en las que se divide la imagen
    Pasos_max_X = (math.trunc(self.lane_image.shape[1] / resolucion) - 1)
    Pasos_max_Y = (math.trunc(self.lane_image.shape[0] / resolucion) - 1)
    Flag = False
    for y in range(Pasos_max_Y, 0,-1):  # Comienzo por las filas inferiores ya que son las zonas más próximas espacialmente al avión
        if Flag:
            break
        else:
            for x in range(Pasos_max_X):
                Flag = False
                result = mv.recorte(self.lane_image, x, y, 256, 256, resolucion)
                if result.shape[0]==256 and result.shape[1]==256:
                    result = np.expand_dims(result, axis=0)
                    Prediccion = self.modelo.predict(result)
                    Prediccion = np.argmax(Prediccion)
                    if (Prediccion == 1):
                        result = mv.region_de_interes(self.lane_image, x, y, resolucion, 0, 0, False)
                        Flag = True
                        return Flag,result
    return Flag , None



def VA(self,result):
    # MEDIDA DE LINEAS DE PISTA
    Linea_Central, Lineas_medias, canny_image = mv.Vision_Artificial_2(result, self.lane_image,180)
    if Linea_Central.any() > 0:  # Si detecto lineas me quedo con la pendiente de las lineas para orientar la imagen
        Deteccion = True
        self.Pinteresantes=self.Pos_GPS#Punto de retorno para identificar la pista
    else:
        Deteccion = False

    # CALCULO DE DISTANCIA AL CENTRO
    if Deteccion == True and self.Activo==1:
        Linea_Central_parametros = mv.Crear_parametros_2(Linea_Central)  # Caracteriza la recta central
        if Linea_Central_parametros[0][0] is not None:
            if Linea_Central_parametros[0][0] > 0.0001 and Linea_Central_parametros[0][0] < -0.0001:  # Si el rumbo es perpendicular a la pista girar
                Distancia_superior = 100
                Distancia_inferior = 100
                Coordenada_linea_Central_inf = 0
                Coordenada_linea_Central_sup = 900
            else:  # Si el rumbo no forma 90º con la pista
                Coordenada_linea_Central_sup = int((int((self.lane_image.shape[0] / 3)) - Linea_Central_parametros[0][1]) / Linea_Central_parametros[0][0])  # Coordenada x de la linea de referencia de pista a la altura del punto medio de la camara
                Coordenada_linea_Central_inf = int((int((self.lane_image.shape[0] / 1.5)) - Linea_Central_parametros[0][1]) / Linea_Central_parametros[0][0])  # Coordenada x de la linea
                Distancia_superior = mv.Distancia_entre_puntos([int((self.lane_image.shape[1] / 2)), int((self.lane_image.shape[0] / 3))],[Coordenada_linea_Central_sup, int((self.lane_image.shape[0] / 3))])
                Distancia_inferior = mv.Distancia_entre_puntos([int((self.lane_image.shape[1] / 2)), int((self.lane_image.shape[0] / 1.5))],[Coordenada_linea_Central_inf, int((self.lane_image.shape[0] / 1.5))])

        else:  # Si la pista es paralela al rumbo
            Coordenada_linea_Central_sup = Linea_Central_parametros[0][1]
            Coordenada_linea_Central_inf = Linea_Central_parametros[0][1]
            Distancia_superior = mv.Distancia_entre_puntos([int((self.lane_image.shape[1] / 2)), int((self.lane_image.shape[0] / 3))],[Coordenada_linea_Central_sup, int((self.lane_image.shape[0] / 3))])
            Distancia_inferior = mv.Distancia_entre_puntos([int((self.lane_image.shape[1] / 2)), int((self.lane_image.shape[0] / 1.5))],[Coordenada_linea_Central_inf, int((self.lane_image.shape[0] / 1.5))])
        # self.Text.insert("insert", "Inferior"+str(Distancia_inferior)+"Superior"+str(Distancia_superior)+"\n")
        print([Distancia_inferior,Distancia_superior,'Inf y sup'])
        if Distancia_superior<self.Limite and Distancia_inferior<self.Limite: #Si la distancia es muy pequeña vale como referencia
            print('Cazado punto')
            self.Text.insert("insert", "Cazado punto\n")
            self.mission=self.Pos_GPS
        else:
            if self.lane_image.shape[1] / 2 > Coordenada_linea_Central_sup * 1.05 and self.lane_image.shape[1] / 2 < Coordenada_linea_Central_inf * 0.95:
                self.Girar(0.05)
            elif self.lane_image.shape[1] / 2 < Coordenada_linea_Central_sup * 0.95 and self.lane_image.shape[1] / 2 > Coordenada_linea_Central_inf * 1.05:
                self.Girar(-0.05)
            elif self.lane_image.shape[1] / 2 < Coordenada_linea_Central_sup * 0.95 and self.lane_image.shape[1] / 2 < Coordenada_linea_Central_inf * 0.95:
                self.Desplazar(1)
            elif self.lane_image.shape[1] / 2 > Coordenada_linea_Central_sup * 1.05 and self.lane_image.shape[1] / 2 > Coordenada_linea_Central_inf * 1.05:
                self.Desplazar(-1)











