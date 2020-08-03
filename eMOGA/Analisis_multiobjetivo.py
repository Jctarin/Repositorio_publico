import tensorflow as tf
from tensorflow.python.keras.preprocessing.image import ImageDataGenerator
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dropout, Flatten, Dense,LeakyReLU
from tensorflow.python.keras.layers import Convolution2D, MaxPooling2D
from tensorflow.python.keras import backend as K
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.preprocessing.image import  img_to_array
import cv2
from tensorflow.keras.models import load_model
import numpy as np
import os
import glob
import math as M
import time




def Capa_Inicial(Color,Filtros,Fila_pooling,Columna_pooling,Fila_filtros,Columna_filtros,Valor_LeakyReLu):
	cnn2 = Sequential()
	if Valor_LeakyReLu==0:
		cnn2.add(Convolution2D(Filtros, (Fila_filtros,Columna_filtros), padding='same', input_shape=(256, 256, Color),activation='relu', kernel_initializer=tf.random_normal_initializer(0, 0.02)))
	else:
		cnn2.add(Convolution2D(Filtros, (Fila_filtros,Columna_filtros), padding='same', input_shape=(256, 256, Color), kernel_initializer=tf.random_normal_initializer(0, 0.02)))
		cnn2.add(LeakyReLU(alpha=Valor_LeakyReLu))
	cnn2.add(MaxPooling2D(pool_size=(Fila_pooling,Columna_pooling)))
	return cnn2


def Capas_Ocultas(Fila_filtros,Columna_filtros,Filtros,Fila_pooling,Columna_pooling,Valor_LeakyReLu,x):
	Filtros=int((Filtros*M.pow(2,(x+1))))
	if Filtros>512:
		Filtros=512
	cnn2 = Sequential()
	if Valor_LeakyReLu==0:
		cnn2.add(Convolution2D(Filtros, (Fila_filtros,Columna_filtros), padding='same', activation='relu',kernel_initializer=tf.random_normal_initializer(0, 0.02)))
	else:
		cnn2.add(Convolution2D(Filtros, (Fila_filtros,Columna_filtros), padding='same',kernel_initializer=tf.random_normal_initializer(0, 0.02)))
		cnn2.add(LeakyReLU(alpha=Valor_LeakyReLu))
	cnn2.add(MaxPooling2D(pool_size=(Fila_pooling,Columna_pooling)))
	return cnn2

##Red convolucional

def Red_Neuronal(Neuronas,Capas,Color,Filtros,Fila_pooling,Columna_pooling,Fila_filtros,Columna_filtros,Valor_LeakyReLu):
	cnn = Sequential()  ## Define la red como una consecucion de capas
	Capas=Capas-1
	cnn.add(Capa_Inicial(Color,Filtros,Fila_pooling,Columna_pooling,Fila_filtros,Columna_filtros,Valor_LeakyReLu))
	for x in range(Capas):
		cnn.add(Capas_Ocultas(Fila_filtros,Columna_filtros,Filtros,Fila_pooling,Columna_pooling,Valor_LeakyReLu,x))
	cnn.add(Flatten())  ## Hace plana la imagen final comprimiendo toda la profundidad que tenia
	cnn.add(Dense(Neuronas, activation='relu'))  ##Capa densa de 256 neuronas
	cnn.add(Dropout(0.5))  ## Durante el entrenamiento "apaga" la mitad de las neuronas de la capa densa para evitar overfitting
	cnn.add(Dense(2, activation='softmax'))  ## softmax saca las probabilidades de que pertenezca a cada clase
	cnn.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.0005), metrics=['accuracy'])
	cnn.summary()
	return cnn

##Entrenamiento
def Entrenar(cnn,Color,Epocas):
	if Color==2:
		data_entrenamiento = r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_RGB_256x256_Filtradas\Entrenamiento'  ##Directotio de imagenes para entrenar
		data_validacion = r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_RGB_256x256_Filtradas\Validacion'  ##Directotio de imagenes para validacion
	else:
		data_entrenamiento = r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_GRAY_256x256_Filtradas\Entrenamiento'  ##Directotio de imagenes para entrenar
		data_validacion = r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_GRAY_256x256_Filtradas\Validacion'  ##Directotio de imagenes para validacion
	altura, longitud = 256, 256  ## tamaño de entrenamiento
	batch_size = 32  ## Imagenes a procesar en cada una de las iteraciones
	## Preprocesamiento

	##1. Coge las imagenes antes del entremaniento y les aplica cambios para enriquecer el entrenamiento
	entrenamiento_datagen = ImageDataGenerator(
		rescale=1. / 255,  ## cambia los posibles valores de cada pixel (0-255) a (0-1) para ser mas eficientes
		shear_range=0.3,
		## Inclina las imagenes para que el algoritmo identifique las imagenes independientmente de su inclinacion
		zoom_range=0.3,
		## Aplica un zoom a las imagenes de forma aleatoria para que el algoritmo identifique la forma anq no aparezca igual de grande
		horizontal_flip=True  ## Invierte imagenes
	)

	validacion_datagen = ImageDataGenerator(
		rescale=1. / 255,  ## cambia los posibles valores de cada pixel (0-255) a (0-1) para ser mas eficientes
	)
	if Color == 1:
		imagen_entrenamiento = entrenamiento_datagen.flow_from_directory(
			data_entrenamiento,  ##Accede al directorio que hemos definido donde estan las imagenes
			color_mode='grayscale',
			target_size=(altura, longitud),  ## Las trata con las dimensiones definidas anteriormente
			batch_size=batch_size,
			class_mode='categorical'  ## El objetivo es decidir si son de una Categoria u otra
		)

		imagen_validacion = validacion_datagen.flow_from_directory(
			data_validacion,  ##Accede al directorio que hemos definido donde estan las imagenes
			target_size=(altura, longitud),  ## Las trata con las dimensiones definidas anteriormente
			batch_size=batch_size,
			color_mode='grayscale',
			class_mode='categorical'  ## El objetivo es decidir si son de una Categoria u otra
		)
	else:
		imagen_entrenamiento = entrenamiento_datagen.flow_from_directory(
			data_entrenamiento,  ##Accede al directorio que hemos definido donde estan las imagenes
			target_size=(altura, longitud),  ## Las trata con las dimensiones definidas anteriormente
			batch_size=batch_size,
			class_mode='categorical'  ## El objetivo es decidir si son de una Categoria u otra
		)

		imagen_validacion = validacion_datagen.flow_from_directory(
			data_validacion,  ##Accede al directorio que hemos definido donde estan las imagenes
			target_size=(altura, longitud),  ## Las trata con las dimensiones definidas anteriormente
			batch_size=batch_size,
			class_mode='categorical'  ## El objetivo es decidir si son de una Categoria u otra
		)
	print(imagen_entrenamiento.class_indices)
	cnn.fit(imagen_entrenamiento, epochs=Epocas, validation_data=imagen_validacion)
	dir = r'C:\Users\Juatarto\Desktop\TFM'

	Direccion_modelo=r'C:\Users\Juatarto\Desktop\TFM\Modelo_Capas_Experimental4.h5'
	Direccion_pesos=r'C:\Users\Juatarto\Desktop\TFM\Pesos_Capas_Experimental4.h5'

	##Guardar modelo
	if not os.path.exists(dir):
		os.mkdir(dir)
	cnn.save(Direccion_modelo)  ##Estructura del modelo
	cnn.save_weights(Direccion_pesos)  ## Pesos de cada cosa
	return [Direccion_modelo,Direccion_pesos]


def Ensayo_2(Vector_imagenes,Color):#CAMBIAR EL SISTEMA DE CARGAR LAS IMAGENES
	modelo = r'C:\Users\Juatarto\Desktop\TFM\Arquitecturas\Test\Epoca_10\Modelo_Capas_6_RGB_Epocas_10_Neuronas_256_Filtros_32_relu.h5'
	pesos = r'C:\Users\Juatarto\Desktop\TFM\Arquitecturas\Test\Epoca_10\Pesos_Capas_6_RGB_Epocas_10_Neuronas_256_Filtros_32_relu.h5'
	# modelo = r'C:\Users\Juatarto\Desktop\TFM\Modelo_Capas_Experimental4.h5'
	# pesos = r'C:\Users\Juatarto\Desktop\TFM\Pesos_Capas_Experimental4.h5'
	cnn = load_model(modelo)
	cnn.load_weights(pesos)
	contador=0
	Vector_pista = np.array([])
	Vector_No_pista = np.array([])
	Tiempo_inicial=time.time()
	for imagen in Vector_imagenes:
		if Color==3:
			imagen_leida=cv2.imread(imagen)
		else:
			imagen_leida = cv2.imread(imagen)
			gray = cv2.cvtColor(imagen_leida, cv2.COLOR_RGB2GRAY)
			imagen_leida = img_to_array(gray)
		result = np.expand_dims(imagen_leida, axis=0)
		Prediccion = cnn.predict(result)
		if contador%2==0: #Si la posicion es par DEBE haber una pista en la imagen
			Vector_pista=np.append(Vector_pista,Prediccion[0,1]) # Prediccion menos el valor esperado que habiendo pista es 1
		else:
			Vector_No_pista=np.append(Vector_No_pista,Prediccion[0,0])  #Prediccion menos el valor esperado que siendo NO pista es 0
		contador=contador+1 #Controla si hay una pista o no
	Tiempo_final = time.time()
	Tiempo_ejecucion = Tiempo_final-Tiempo_inicial
	Resultado_No_Pista=np.mean(Vector_No_pista)
	Resultado_Pista = np.mean(Vector_pista)
	return [(1-Resultado_Pista),Resultado_No_Pista,Tiempo_ejecucion] #% de error y acierto


def Ensayo(Vector_imagenes,Color):#CAMBIAR EL SISTEMA DE CARGAR LAS IMAGENES
	modelo = r'C:\Users\Juatarto\Desktop\TFM\Modelo_Capas_Experimental4.h5'
	pesos = r'C:\Users\Juatarto\Desktop\TFM\Pesos_Capas_Experimental4.h5'
	cnn = load_model(modelo)
	cnn.load_weights(pesos)
	contador=0
	Vector_Errores = []
	for imagen in Vector_imagenes:
		if Color==3:
			imagen_leida=cv2.imread(imagen)
		else:
			imagen_leida = cv2.imread(imagen)
			gray = cv2.cvtColor(imagen_leida, cv2.COLOR_RGB2GRAY)
			imagen_leida = img_to_array(gray)
		result = np.expand_dims(imagen_leida, axis=0)
		Prediccion = cnn.predict(result)
		Prediccion = np.argmax(Prediccion)
		if contador%2==0: #Si la posicion es par DEBE haber una pista en la imagen
			Vector_Errores.append(Prediccion-1) # Prediccion menos el valor esperado que habiendo pista es 1
		else:
			Vector_Errores.append(Prediccion)  #Prediccion menos el valor esperado que siendo NO pista es 0
		contador=contador+1 #Controla si hay una pista o no
	Aciertos=Vector_Errores.count(0) #Los valores 0 significan que se restaron los mismo valores, coincide lo que habia con la pediccion
	Error_tipo1 = Vector_Errores.count(1) # Error de NO ver una pista cuando SI la hay
	Error_tipo2 = Vector_Errores.count(-1) #Error de ver pista cuando NO la hay
	Imagenes_Totales=Aciertos+Error_tipo1+Error_tipo2 #Imagenes totales
	Error_tipo1=round((Error_tipo1)/Imagenes_Totales,3)
	Error_tipo2=round((Error_tipo2)/Imagenes_Totales,3)
	return [Error_tipo1,Error_tipo2] #% de error y acierto

def Funcion_analisis(Vector):
	Vector_ensayo=r'C:\Users\Juatarto\Desktop\TFM\Imagenes\Test\TRAIN_RGB_256x256_Filtradas\Entrenamiento\Pista\*.jpg'
	Neuronas=int(Vector[0])
	Capas=int(Vector[1])
	Color=int(Vector[2])
	Filtros=int(Vector[3])
	Fila_pooling=int(Vector[4])
	Columna_pooling=int(Vector[5])
	Fila_filtros=int(Vector[6])
	Columna_filtros = int(Vector[7])
	Valor_LeakyReLu=Vector[8]/100
	Epocas=int(Vector[9])
	K.clear_session()
	try:
		Direccion_modelo,Direccion_pesos=Entrenar(Red_Neuronal(Neuronas,Capas,Color,Filtros,Fila_pooling,Columna_pooling,Fila_filtros,Columna_filtros,Valor_LeakyReLu),Color,Epocas)
		if Color==3:
			Imagenes = glob.glob(Vector_ensayo)
		else:
			Imagenes = glob.glob(Vector_ensayo)
		Vector=Ensayo_2(Imagenes,Color)
		Peso_modelo=os.path.getsize(Direccion_modelo) #Obtener el valor del peso del modelo en bytes
		Peso_pesos=os.path.getsize(Direccion_pesos) #Obtener el valor del peso del modelo en bytes
		Peso_total=Peso_modelo+Peso_pesos
		os.remove(Direccion_modelo) # Eliminar el modelo una vez medido
		os.remove(Direccion_pesos)  # Eliminar el modelo una vez medido
		Vector.append(Peso_total)
	except:
		Vector=np.array([1000,1000,1000,1000000])
	return Vector

def Funcion_analisis_Prueba(Vector):
	a1 = 0.5 * M.sin(1) - 2 * M.cos(1) + M.sin(2) - 1.5 * M.cos(2);
	a2 = 1.5 * M.sin(1) - M.cos(1) + 2 * M.sin(2) - 0.5 * M.cos(2);
	b1 = 0.5 * M.sin(Vector[0]) - 2 * M.cos(Vector[0]) + M.sin(Vector[1]) - 1.5 * M.cos(Vector[1]);
	b2 = 1.5 * M.sin(Vector[0]) - M.cos(Vector[0]) + 2 * M.sin(Vector[1]) - 0.5 * M.cos(Vector[1]);

	J1 = (1 + (a1 - b1) ** 2 + (a2 - b2) ** 2);
	J2 = ((Vector[0] + 3) ** 2 + (Vector[1] + 1) ** 2);
	J =np.array([J1,J2])
	return J
