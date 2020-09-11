import cv2
import numpy as np
import math as mt

# --------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------
# --------------------------------------CALCULO GEOMETRICO------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------

#Recibe dos puntos de cada recta y calcula el punto de interseccion (Problemas cuando son paralelas)
def Punto_de_interseccion(Recta_1,Recta_2):
    Punto=[0,0]
    Recta_1=np.array([Recta_1])
    Recta_2=np.array([Recta_2])
    Recta_1=Crear_parametros(Recta_1)
    Recta_2=Crear_parametros(Recta_2)
    Recta_1=Recta_1[0]
    Recta_2=Recta_2[0]
    M_1=Recta_1[0]
    M_2=Recta_2[0]
    C_1=Recta_1[1]
    C_2=Recta_2[1]
    Punto[0]=round((C_2-C_1)/(M_1-M_2),2)
    Punto[1]=round(M_1*Punto[0]+C_1,2)
    return Punto

def Angulo_entre_rectas(Recta_1,Recta_2):
    Vector_1=[(Recta_1[0]-Recta_1[2]),(Recta_1[1]-Recta_1[3])]
    Vector_2=[(Recta_2[0]-Recta_2[2]),(Recta_2[1]-Recta_2[3])]
    Angulo=mt.acos(abs(Vector_1[0]*Vector_2[0]+Vector_1[1]*Vector_2[1])/(mt.sqrt(mt.pow(Vector_1[0],2)+mt.pow(Vector_1[1],2))*mt.sqrt(mt.pow(Vector_2[0],2)+mt.pow(Vector_2[1],2))))
    Angulo = Angulo * (360 / (2 * mt.pi))
    if Angulo<0.00001 and Angulo>-0.00001:
        Angulo=0
    return Angulo

def Distancia_entre_rectas(Recta_1,Recta_2):
    Linea_1=Recta_1
    Linea_2=Recta_2
    Punto_1=Linea_1[0]
    Punto_2=Linea_2[0]
    Distancia=int(mt.sqrt(mt.pow((Punto_2[0]-Punto_1[0]),2)+mt.pow((Punto_2[1]-Punto_1[1]),2)))
    return Distancia

def Distancia_entre_puntos(Punto_1,Punto_2):
    Distancia=int(mt.sqrt(mt.pow((Punto_2[0]-Punto_1[0]),2)+mt.pow((Punto_2[1]-Punto_1[1]),2)))
    return Distancia

#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------TRATAMINETO DE DATOS (LINEAS)-------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------

def Comparar(Pendiente,Pendientes_totales):
    _,Pendiente_media=Percentiles(Pendientes_totales)
    Limite_sup_Pendiente=0.8*Pendiente_media
    Limite_inf_Pendiente = -0.8 * Pendiente_media
    if Pendiente>Limite_sup_Pendiente and Pendiente>Limite_inf_Pendiente:
        Flag=True
    else:
        Flag=False
    return Flag


def Percentiles(lista):
    sublista=[]
    superior = np.percentile(lista, 75, axis=0)
    inferior = np.percentile(lista, 25, axis=0)
    for parametro in lista:
        if parametro<superior and parametro>inferior:
            sublista.append(parametro)
    if len(sublista)>0:
        media=np.average(sublista, axis=0)
    else:
        media=np.percentile(lista, 50, axis=0)
    return media

def Tamizado_datos(lines):
    lines_nueva=[]
    lines_nueva_1=[]
    Intersecciones=[]
    Pendientes=[]
    Porcentaje_sup=1.10
    Porcentaje_inf=0.90
    if len(lines)>2:
        for line in lines:
            Pendiente,Interseccion=line
            Intersecciones.append(Interseccion)
            Pendientes.append(Pendiente)

        Media_Pend=Percentiles(Pendientes)
        Media_Int=Percentiles(Intersecciones)


        if Media_Pend>0:
            for line in lines:
                if Media_Pend*Porcentaje_inf<=line[0]<=Media_Pend*Porcentaje_sup:
                    lines_nueva_1.append(line)
        else:
            for line in lines:
                if Media_Pend * Porcentaje_inf >= line[0] >= Media_Pend * Porcentaje_sup:
                    lines_nueva_1.append(line)

        if Media_Int>0:
            for line in lines_nueva_1:
                if Media_Int*Porcentaje_inf<=line[1]<=Media_Int*Porcentaje_sup:
                    lines_nueva.append(line)
        else:
            for line in lines_nueva_1:
                if Media_Int*Porcentaje_inf>=line[1]>=Media_Int*Porcentaje_sup:
                    lines_nueva.append(line)
    else:
        lines_nueva=lines
    return lines_nueva

#Recibe una imagen y un vector con la pendiente y el punto de corte en X y devuelve las coordenadas de dos puntos de la recta
def Crear_coordenadas(image,parametros_linea):
    Pendiente,Interseccion =parametros_linea
    if Pendiente>150:
        y1 = image.shape[0]
        y2 = int(y1 * (3 / 7))
        x1=int(Interseccion)
        x2=int(Interseccion)
    elif Pendiente>0.001 or Pendiente<-0.001:
        y1 = image.shape[0]
        y2 = int(y1 * (3 / 7))
        x1=int((y1-Interseccion)/Pendiente)
        x2=int((y2-Interseccion)/Pendiente)
    else:
        y1=int(image.shape[0]/2)
        y2=int(image.shape[0]/2)
        x1=int(image.shape[1])
        x2=int(image.shape[1]/2)
    return np.array([x1,y1,x2,y2])

#Recibe un conjunto de lineas en forma de puntos extremos y devuelve las lineas en forma punto de corte y pendiente
def Crear_parametros(lines):
    Rectas =[]
    if lines is not None:
        for line in lines:
            x1,y1,x2,y2 =line.reshape(4)#IMPORTANTISIMO LINES TIENE QUE TENER EL FORMATO [[[5,6,5,4]] [[8,9,8,7]] [[7,8,9,6]]]
            if abs(x2-x1)<2:
                parametros=[200,x1]
            else:
                parametros = np.polyfit((x1,x2),(y1,y2),1)
            Pendiente = parametros[0]
            interseccion= parametros[1]
            Rectas.append([Pendiente,interseccion])
    return Rectas

#Recibe un conjunto de lineas en forma de puntos extremos y devuelve las lineas en forma punto de corte y pendiente
def Crear_parametros_2(lines):
    Rectas =[]
    if lines is not None:
        for line in lines:
            x1,y1,x2,y2 =line.reshape(4)#IMPORTANTISIMO LINES TIENE QUE TENER EL FORMATO [[[5,6,5,4]] [[8,9,8,7]] [[7,8,9,6]]]
            if (x2-x1)<0.0001 and (x2-x1)>-0.0001:
                Rectas.append([None, x1])
            else:
                parametros = np.polyfit((x1,x2),(y1,y2),1)
                Pendiente = parametros[0]
                interseccion= parametros[1]
                Rectas.append([Pendiente,interseccion])

    return Rectas

def Recta_central(linea_1,linea_2):
    media=[0,0,0,0]
    if linea_1.any() is not 0 and linea_2.any() is not 0:
        l1_x1,l1_y1,l1_x2,l1_y2=linea_1
        l2_x1, l2_y1, l2_x2, l2_y2 = linea_2
        media=int((l1_x1+l2_x1)/2),l1_y1,int((l1_x2+l2_x2)/2),l1_y2
    return media

#Recibe una imagen y un conjunto de rectas en forma de coordenadas de los puntos extremos de las mismas
# y devuelve las rectas laterales y central de la pista
def media_lineas(image,lines):
    Linea_derecha=[0,0,0,0]
    Linea_izquierda=[0,0,0,0]
    Linea_central=[0,0,0,0]
    Recta_Camara_1 = [int((image.shape[1] / 2)), int((image.shape[0] / 3)+5), int((image.shape[1]/2)), int((image.shape[0]/3)-5)]
    Recta_Camara_2 = [int((image.shape[1] / 2)), int((image.shape[0] / 1.5) + 5), int((image.shape[1] / 2)),int((image.shape[0] / 1.5) - 5)]
    Grupo_derecha= [] #Conjunto de lineas a la derecha
    Grupo_izquierda= [] #Conjunto de lineas a la Izquierda
    Grupo_total= Crear_parametros (lines) #Conjunto de lineas total
    if len(Grupo_total)>0:
        Pendiente_total,Interseccion_total=np.average(Grupo_total,axis=0)
        for Grupo in Grupo_total:
            Pendiente,interseccion=Grupo
            if Interseccion_total > interseccion:
                Grupo_izquierda.append([Pendiente,interseccion])
            else:
                Grupo_derecha.append([Pendiente,interseccion])
        Grupo_derecha = Tamizado_datos(Grupo_derecha)
        if len(Grupo_derecha)>0:
            media_derecha = np.average(Grupo_derecha, axis=0)
            Linea_derecha = Crear_coordenadas(image, media_derecha)
        Grupo_izquierda = Tamizado_datos(Grupo_izquierda)
        if len(Grupo_izquierda)>0:
            media_izquierda= np.average(Grupo_izquierda,axis=0)
            Linea_izquierda = Crear_coordenadas(image, media_izquierda)
        if len(Grupo_derecha)>0 and len(Grupo_izquierda)>0:
            Linea_central= Recta_central(Linea_derecha,Linea_izquierda)
    return np.array([Linea_izquierda,Linea_derecha,Linea_central]),np.array([Recta_Camara_1,Recta_Camara_2]),np.array([Linea_central])


#Recibe una imagen y un array de rectas y devuelve una imagen de las rectas sobre un fonde negro
def lines_detect(image, lines,Lines_camara):
    lines_imagen = np.zeros_like(image)
    if lines is not None:
        for line in lines:
            x1,y1,x2,y2 = line.reshape(4)
            cv2.line(lines_imagen,(x1,y1),(x2,y2),(255,0,0),5)
        for line in Lines_camara:
            x1, y1, x2, y2 = line.reshape(4)
            cv2.line(lines_imagen, (x1, y1), (x2, y2), (0, 255, 0), 7)
    return lines_imagen

#Recibe una imgen y devuelve una imagen de contornos
def canny(image,threshold):
    gray = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY) #Se pasa de 3 canales de color a 1
    _, Umbral = cv2.threshold(gray, threshold, 240, cv2.THRESH_TOZERO) #Binarizacion de la imagen
    canny = cv2.Canny(Umbral,255,255)  # Se detectan gradientes importantes de color siendo el limite inferior 255 y el superior 255
    return canny


#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------TAMANO DE IMAGENES DE INTERES-------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------



#Recibe una imagen y devuelve una region intacta de la imagen original y el resto negro
def recorte(image,x,y,Altura,Anchura,resolucion):
    x=x*resolucion
    y=y*resolucion
    mascara_imagen = image[y:y+Altura,x:x+Anchura] #vector con 4 coordenadas (Rectangulo)
    #mascara = np.zeros_like(image)#Plantilla del tamano de la imagen
    #cv2.fillPoly(mascara,Poligono,255)#Funde ambas imagenes y marca la interseccion en blanco (255)
    #mascara_imagen = cv2.bitwise_and(image,mascara)  #And bit a bit de la imagen
    return mascara_imagen

#Recibe una imagen y devuelve una region intacta de la imagen original y el resto negro
def region_de_interes(image,x,y,resolucion,pendiente,Interseccion,Flag):
    tamano=400
    #Poligono de interes
    if pendiente == 0: # Caso para NO detecciones
        x=x*resolucion
        y=y*resolucion
        Poligono=np.array([[(x,y),(int(x+tamano),y),(int(x+tamano),int(y+tamano)),(x,int(y+tamano))]])
    elif Flag==False and pendiente is not 0:#Caso importante, deteccion de pista y seguimiento
        y1=y*resolucion-200
        y2=y*resolucion+550
        Poligono=np.array([[(int((y1-Interseccion)/pendiente)-100,y1),(int((y2-Interseccion)/pendiente)-200,y2),(int((y2-Interseccion)/pendiente)+200,y2),(int((y1-Interseccion)/pendiente)+100,y1)]])

    elif Flag==True and pendiente is not 0: #Inclinacion de la zona de interes (Para compatibilidad con versiones antiguas)
        x = x * resolucion
        y = y * resolucion
        x_prima=int(x-y*mt.tan(90-pendiente))
        Poligono = np.array([[(x,y),(x+500,y),(x_prima+500,y+500),(x_prima,y+500)]])

    mascara = np.zeros_like(image)  # Plantilla del tamano de la imagen
    cv2.fillPoly(mascara, [Poligono], (255, 255, 255))  # Funde ambas imagenes y marca la interseccion en blanco (255)
    # cv2.rectangle(mascara,(x,y),(x-100,y-100),(255,255,255),1)# Funde ambas imagenes y marca la interseccion en blanco (255)
    mascara_imagen = cv2.bitwise_and(image, mascara)  # And bit a bit de la imagen
    return mascara_imagen


#Funcion de vision artificial
def Vision_artificial(result,lane_image):
    canny_imagen = canny(result, 210)
    lineas = cv2.HoughLinesP(canny_imagen, 2, np.pi / 180, 80, np.array([]), minLineLength=70, maxLineGap=3)
    Lineas_medias,Lineas_camara, Linea_Central = media_lineas(lane_image, lineas)
    imagen_lines = lines_detect(lane_image, Lineas_medias,Lineas_camara)
    combo_imagen = cv2.addWeighted(imagen_lines, 0.8, lane_image, 1, 1)
    Final = cv2.addWeighted(combo_imagen, 1, result, 1.5, 1)
    return Final,Linea_Central,Lineas_medias,canny_imagen


#Funcion de vision artificial
def Vision_artificial_3(result):
    canny_imagen = canny(result, 180)
    lineas = cv2.HoughLinesP(canny_imagen, 2, np.pi / 180, 80, np.array([]), minLineLength=70, maxLineGap=6)
    Lineas_medias,Lineas_camara, Linea_Central = media_lineas(canny_imagen, lineas)
    imagen_lines = lines_detect(canny_imagen, Lineas_medias,Lineas_camara)
    combo_imagen = cv2.addWeighted(imagen_lines, 0.8, canny_imagen, 1, 1)
    return combo_imagen

#Funcion para definir los umbrales de las acciones de control
def Umbral(input,umbral_sup,umbral_inf):
    if input>=umbral_sup:
        output=umbral_sup
    elif input<=umbral_inf:
        output=umbral_inf
    else:
        output=input
    return output

def Vision_Artificial_2(result,lane_image,Threshold):
    canny_imagen = canny(result, Threshold)
    lineas = cv2.HoughLinesP(canny_imagen, 2, np.pi / 180, 80, np.array([]), minLineLength=60, maxLineGap=2)
    Lineas_medias,Lineas_camara, Linea_Central = media_lineas(lane_image, lineas)
    return Linea_Central,Lineas_medias,canny_imagen

def Vision_Artificial_4(result, lane_image, Threshold):
    canny_imagen = canny(result, Threshold)
    lineas = cv2.HoughLinesP(canny_imagen, 2, np.pi / 180, 80, np.array([]), minLineLength=60, maxLineGap=2)
    Lineas_medias,Lineas_camara, Linea_Central = media_lineas(lane_image, lineas)
    imagen_lines = lines_detect(lane_image, Lineas_medias,Lineas_camara)
    combo_imagen = cv2.addWeighted(imagen_lines, 0.5, lane_image, 0.5, 0)
    Final = cv2.addWeighted(combo_imagen, 1, result, 1.5, 1)
    return Final,Linea_Central,Lineas_medias,canny_imagen
