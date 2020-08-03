from tkinter import *
from tkinter import filedialog
import threading
import GUI.Libreria_Control_5_GUI as LC
import GUI.Libreria_vision_GUI_2 as LV
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')
from tensorflow.keras.models import load_model



class Pagina_principal():
    def __init__(self,raiz):
        self.Qgc=LC.QGC()
        self.raiz=raiz
        self.Verbose_options=Verbose_options()
        self.miframe = Frame(raiz)
        self.miframe.pack()
        self.Vision=0
        # ------------------------------------------------
        # -----------------Cajas texto--------------------
        # ------------------------------------------------
        self.metros = Entry(self.miframe)
        self.metros.grid(row=1, column=7)
        self.Latitud = Entry(self.miframe)
        self.Latitud.grid(row=2, column=5)
        self.Longitud = Entry(self.miframe)
        self.Longitud.grid(row=2, column=7)
        self.Pitch = Entry(self.miframe)
        self.Pitch.grid(row=7, column=5)
        self.Roll = Entry(self.miframe)
        self.Roll.grid(row=7, column=7)
        # ------------------------------------------------
        # -----------------Labels-------------------------
        # ------------------------------------------------
        Label(self.miframe, text="Latitud:").grid(row=2, column=4)
        Label(self.miframe, text="Metros:").grid(row=1, column=6)
        Label(self.miframe, text="Longitud:").grid(row=2, column=6)
        Label(self.miframe, text="Pitch:").grid(row=7, column=4)
        Label(self.miframe, text="Roll:").grid(row=7, column=6)
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.GoTo = Button(self.miframe, text=" GoTo  ",command=self.Actuar_GoTo,bg='white',width=10)
        self.GoTo.grid(row=2, column=8)
        self.GoTo_activo=0
        self.Waypoint=LC.Waypoint(21,-157,500,100,1)
        self.Mission = Button(self.miframe, text="Mission",command=self.Actuar_Mision,bg='white',width=10)
        self.Mission.grid(row=3, column=8,padx=5)
        self.Mission_activo = 0
        self.Altitud = Button(self.miframe, text="Altitud",command=self.Actuar_Altitud,bg='white',width=10)
        self.Altitud.grid(row=1, column=8)
        self.Altitud_activo=0
        self.Altitud_vuelo=500
        self.Takeoff = Button(self.miframe, text="Takeoff",command=self.Actuar_Takeoff,bg='white',width=10)
        self.Takeoff.grid(row=4, column=8)
        self.Takeoff_activo=0
        self.Land = Button(self.miframe, text="  Land  ",command=self.Actuar_Land,bg='white',width=10)
        self.Land.grid(row=5, column=8)
        self.Land_activo = 0
        self.AutoLand = Button(self.miframe, text="  Auto-Land  ",command=self.Actuar_Auto_Land,bg='white',width=10)
        self.AutoLand.grid(row=6, column=8)
        self.AutoLand_activo = 0
        self.Calibracion = Button(self.miframe, text="  Calibracion  ",command=self.Actuar_Calibracion,bg='white',width=10)
        self.Calibracion.grid(row=7, column=8)
        self.Calibracion_activo = 0
        # ------------------------------------------------
        # -----------------Menu---------------------------
        # ------------------------------------------------
        menu = Menu(raiz)
        raiz.config(menu=menu)
        # Mission
        Mission = Menu(menu, tearoff=0)
        menu.add_cascade(label="Mission", menu=Mission)
        Mission.add_command(label="Create Mission",command=lambda:Pagina_Mission(self.miframe,self.Qgc,self))
        Mission.add_command(label="Load Mission", command=self.Cargar_mission)
        # Control
        Control = Menu(menu, tearoff=0)
        menu.add_cascade(label="Control", menu=Control)
        Control.add_command(label="Tunning PID",command=lambda:Pagina_PIDs(self.miframe,self.Qgc,self))
        Control.add_command(label="Load PID", command=self.Cargar_PIDs)
        # Verbose
        Verbose = Menu(menu, tearoff=0)
        menu.add_cascade(label="Verbose", menu=Verbose)
        Verbose.add_command(label="Options",command=lambda:Pagina_Verbose(self.miframe,self))
        # Comm
        Comunications = Menu(menu, tearoff=0)
        menu.add_cascade(label="Comunications", menu=Comunications)
        Comunications.add_command(label="Config",command=lambda:Pagina_Comm(self.miframe,self))
        # IA
        IA = Menu(menu, tearoff=0)
        menu.add_cascade(label="IA", menu=IA)
        IA.add_command(label="IA config",command=lambda:Pagina_IA(self.miframe,self))

        if self.Qgc.Modelo is None:
            self.AutoLand.configure(state=DISABLED)
        if self.Qgc.Mission is None:
            self.Mission.configure(state=DISABLED)


    # ------------------------------------------------
    # -----------------Funciones Menu-----------------
    # ------------------------------------------------
    def Cargar_mission(self):
        Fichero = filedialog.askopenfilename(title="Abrir", filetypes=(("Fichero txt", "*.txt"),))
        Mission = []
        try:
            Fichero = open(Fichero, "r")
            for lines in Fichero.readlines():
                line = lines.split(',')
                Mission.append(LC.Waypoint(float(line[0]), float(line[1]), float(line[2]), int(line[3]), int(line[4])))
            self.Qgc.Mission = Mission
            print('Cargada')
            self.Mission.configure(state=NORMAL)
        except:  # Si no hay mision se define una por defecto
            print('No hay mision')

    def Cargar_PIDs(self):
        Control=LC.PIDs()
        i=0
        Fichero = filedialog.askopenfilename(title="Abrir", filetypes=(("Fichero txt", "*.txt"),))
        try:
            Fichero = open(Fichero, "r")
            for lines in Fichero.readlines():
                line = lines.split(',')
                if i==0:
                    Control.PID_Heading.tunings=(float(line[0]), float(line[1]), float(line[2]))
                elif i==1:
                    Control.PID_Altitud.tunings=(float(line[0]), float(line[1]), float(line[2]))
                elif i==2:
                    Control.PID_Roll.tunings=(float(line[0]), float(line[1]), float(line[2]))
                elif i==3:
                    Control.PID_Pitch.tunings=(float(line[0]), float(line[1]), float(line[2]))
                elif i==4:
                    Control.PID_AirSpeed.tunings=(float(line[0]), float(line[1]), float(line[2]))
                i+=1
            self.Qgc.Control = Control
            print('Cargados')
        except:  # Si no hay mision se define una por defecto
            print('No hay PIDs o no estan completos')

    # ------------------------------------------------
    # -----------------FUNCIONES BOTONES--------------
    # ------------------------------------------------

    def Actuar_Mision(self):
        if self.Mission_activo==0:
            self.hilo = Boton(self,LC.Mission)
            self.hilo.start()
            self.Mission.config(bg="green")
            self.Mission_activo=1
            # Deshabilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Takeoff.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.Mission.config(bg="white")
            self.Mission_activo=0
            self.hilo.Parar()
            #Habilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            self.Takeoff.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_Altitud(self):
        if self.Altitud_activo == 0:
            if self.metros.get()!="":
                self.Altitud_vuelo=float(self.metros.get())
            else:
                self.Altitud_vuelo=600
                print('No hay altura')
            self.hilo = Boton(self, LC.Altitud)
            self.hilo.start()
            self.Altitud.config(bg="green")
            self.Altitud_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Takeoff.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.Altitud.config(bg="white")
            self.Altitud_activo = 0
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Takeoff.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_Land(self):
        if self.Land_activo == 0:
            self.hilo = Boton(self,LC.Land_2)
            self.hilo.start()
            self.Land.config(bg="green")
            self.Land_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Takeoff.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.Land.config(bg="white")
            self.Land_activo = 0
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Takeoff.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_Takeoff(self):
        if self.Takeoff_activo == 0:
            self.hilo = Boton(self, LC.Takeoff)
            self.hilo.start()
            self.Takeoff.config(bg="green")
            self.Takeoff_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.Takeoff.config(bg="white")
            self.Takeoff_activo = 0
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.GoTo.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_GoTo(self):
        if self.GoTo_activo == 0:
            if self.Latitud.get()!="" and self.Longitud.get()!="":
                self.Waypoint.lat=float(self.Latitud.get())
                self.Waypoint.lon = float(self.Longitud.get())
            self.hilo = Boton(self, LC.Nav)
            self.hilo.start()
            self.GoTo.config(bg="green")
            self.GoTo_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.GoTo.config(bg="white")
            self.GoTo_activo = 0
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_Auto_Land(self):
        if self.AutoLand_activo == 0:
            if not self.Vision.is_alive():
                self.Vision=LV.Vision(self.Qgc.Cola,self.Qgc.Modelo)
            self.hilo = Boton(self, LC.Aterrizaje_autonomo)
            self.Vision.start()
            self.hilo.start()
            self.AutoLand.config(bg="green")
            self.AutoLand_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.GoTo.configure(state=DISABLED)
            self.Calibracion.configure(state=DISABLED)
        else:
            self.AutoLand.config(bg="white")
            self.AutoLand_activo = 0
            self.Vision.Matar()
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            self.GoTo.configure(state=NORMAL)
            self.Calibracion.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Actuar_Calibracion(self):
        if self.Calibracion_activo == 0:
            Roll=0
            Pitch=0
            if self.Roll.get() != "":
                Roll=float(self.Roll.get())
            if self.Pitch.get() != "":
                Pitch=float(self.Pitch.get())
            self.hilo = Boton(self, LC.Bajo_nivel_2,Roll=Roll,Pitch=Pitch)
            self.hilo.start()
            self.Calibracion.config(bg="green")
            self.Calibracion_activo = 1
            # Deshabilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=DISABLED)
            self.Altitud.configure(state=DISABLED)
            self.Mission.configure(state=DISABLED)
            self.Land.configure(state=DISABLED)
            self.GoTo.configure(state=DISABLED)
            self.AutoLand.configure(state=DISABLED)
        else:
            self.Calibracion.config(bg="white")
            self.Calibracion_activo = 0
            self.hilo.Parar()
            # Habilitar los botones de otros modos de vuelo
            self.Takeoff.configure(state=NORMAL)
            self.Altitud.configure(state=NORMAL)
            if self.Qgc.Mission is not None:
                self.Mission.configure(state=NORMAL)
            self.Land.configure(state=NORMAL)
            self.GoTo.configure(state=NORMAL)
            if self.Qgc.Modelo is not None:
                self.AutoLand.configure(state=NORMAL)
            self.Plotear()
            if self.Verbose_options.Clean==1:
                self.Clean()

    def Plotear(self):
        if self.Verbose_options.Heading:
            Pagina_Plots(self.miframe,self.Qgc.Verbose.Plot_Heading(self))
        if self.Verbose_options.Altitud:
            Pagina_Plots(self.miframe, self.Qgc.Verbose.Plot_altitud(self))
        if self.Verbose_options.pitch:
            Pagina_Plots(self.miframe, self.Qgc.Verbose.Plot_Pitch(self))
        if self.Verbose_options.Roll:
            Pagina_Plots(self.miframe, self.Qgc.Verbose.Plot_Roll(self))
        if self.Verbose_options.Vel:
            Pagina_Plots(self.miframe, self.Qgc.Verbose.Plot_Vel(self))
        if self.Verbose_options.Posicion:
            Pagina_Plots(self.miframe, self.Qgc.Verbose.Plot_Posicion(self))


    def Clean(self):
        self.Qgc.Verbose=LC.Verbose_controls()


# ------------------------------------------------
# -----------------CLASES AUXILIARES--------------
# ------------------------------------------------

class Boton(threading.Thread):
    def __init__(self,Main,Funcion,Roll=0,Pitch=0):
        threading.Thread.__init__(self)
        self.Vivo=1
        self.Qgc=Main.Qgc
        self.Funcion=Funcion
        self.Altitud_vuelo=Main.Altitud_vuelo
        self.waypoint=Main.Waypoint
        self.Vision=Main.Vision
        self.pitch=Pitch
        self.Roll=Roll
    def run(self):
        while (1):
            if self.Vivo:
                self.Funcion(self)
            else:
                break
        print('Hilo muerto')

    def Get_vivo(self):
        return self.Vivo

    def Parar(self):
        self.Vivo=0


class Verbose_options():
    def __init__(self):
        self.Heading=1
        self.Altitud=0
        self.Roll=0
        self.pitch=0
        self.Vel=0
        self.Posicion=0
        self.Heading_save=0
        self.Altitud_save=0
        self.Roll_save=0
        self.pitch_save=0
        self.Vel_save=0
        self.Posicion_save=0
        self.Clean=1



# ------------------------------------------------
# -----------------VENTANA PIDs-------------------
# ------------------------------------------------

class Pagina_PIDs():
    def __init__(self,raiz,Qgc,Frame_principal):
        self.Qgc=Qgc
        self.Principal=Frame_principal
        miframe = Toplevel(raiz)
        miframe.title("PIDs Editor")
        # ------------------------------------------------
        # -----------------Cajas texto--------------------
        # ------------------------------------------------
        self.kp = Entry(miframe)
        self.kp.grid(row=1, column=7)
        self.ki = Entry(miframe)
        self.ki.grid(row=2, column=7)
        self.kd = Entry(miframe)
        self.kd.grid(row=3, column=7)
        # ------------------------------------------------
        # -----------------Labels-------------------------
        # ------------------------------------------------
        Label(miframe, text="ki:").grid(row=2, column=6)
        Label(miframe, text="kp:").grid(row=1, column=6)
        Label(miframe, text="kd:").grid(row=3, column=6)
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.Export = Button(miframe, text=" Export ",command=self.Exportar_PIDs)
        self.Export.grid(row=4, column=6)
        self.Save = Button(miframe, text=" Save ",command=self.save)
        self.Save.grid(row=4, column=7)
        Button(miframe, text=" + ",command=lambda:self.Sumar(0)).grid(row=1, column=8)
        Button(miframe, text=" + ",command=lambda:self.Sumar(1)).grid(row=2, column=8)
        Button(miframe, text=" + ",command=lambda:self.Sumar(2)).grid(row=3, column=8)
        Button(miframe, text=" - ",command=lambda:self.Restar(0)).grid(row=1, column=5)
        Button(miframe, text=" - ",command=lambda:self.Restar(1)).grid(row=2, column=5)
        Button(miframe, text=" - ",command=lambda:self.Restar(2)).grid(row=3, column=5)
        # ------------------------------------------------
        # -----------------Combobox-----------------------
        # ------------------------------------------------
        OptionList=["Heading","Rumbo", "Altitud", "Roll", "Pitch", "Velocidad"]
        self.variable = StringVar(miframe)
        self.variable.set(OptionList[0])
        self.menu=OptionMenu(miframe, self.variable, *OptionList)
        self.menu.grid(row=0,column=0)
        self.set()
        self.variable.trace("w", self.set)

    def Exportar_PIDs(self):
        Fichero = filedialog.askopenfilename(title="Abrir", filetypes=(("Fichero txt", "*.txt"),))
        # try:
        Fichero = open(Fichero, "w")
        Fichero.write(str(self.Qgc.Control.PID_Heading.Kp)+","+str(self.Qgc.Control.PID_Heading.Ki)+","+str(self.Qgc.Control.PID_Heading.Kd)+"\n")
        Fichero.write(str(self.Qgc.Control.PID_Altitud.Kp) + "," + str(self.Qgc.Control.PID_Altitud.Ki) + "," + str(self.Qgc.Control.PID_Altitud.Kd) + "\n")
        Fichero.write(str(self.Qgc.Control.PID_Roll.Kp) + "," + str(self.Qgc.Control.PID_Roll.Ki) + "," + str(self.Qgc.Control.PID_Roll.Kd) + "\n")
        Fichero.write(str(self.Qgc.Control.PID_Pitch.Kp) + "," + str(self.Qgc.Control.PID_Pitch.Ki) + "," + str(self.Qgc.Control.PID_Pitch.Kd) + "\n")
        Fichero.write(str(self.Qgc.Control.PID_AirSpeed.Kp) + "," + str(self.Qgc.Control.PID_AirSpeed.Ki) + "," + str(self.Qgc.Control.PID_AirSpeed.Kd) + "\n")
        print('Cargados')
        # except:  # Si no hay mision se define una por defecto
        #     print('No hay PIDs o no estan completos')

    def save(self):
        if self.variable.get()=="Heading":
            self.Principal.Qgc.Control.PID_Heading.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_Heading.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_Heading.Kd = float(self.kd.get())

        elif self.variable.get()=="Rumbo":
            self.Principal.Qgc.Control.PID_Heading_Rumbo.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_Heading_Rumbo.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_Heading_Rumbo.Kd = float(self.kd.get())

        elif self.variable.get()=="Altitud":
            self.Principal.Qgc.Control.PID_Altitud.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_Altitud.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_Altitud.Kd = float(self.kd.get())

        elif self.variable.get()=="Roll":
            self.Principal.Qgc.Control.PID_Roll.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_Roll.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_Roll.Kd = float(self.kd.get())

        elif self.variable.get()=="Pitch":
            self.Principal.Qgc.Control.PID_Pitch.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_Pitch.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_Pitch.Kd = float(self.kd.get())

        else:
            self.Principal.Qgc.Control.PID_AirSpeed.Kp = float(self.kp.get())
            self.Principal.Qgc.Control.PID_AirSpeed.Ki = float(self.ki.get())
            self.Principal.Qgc.Control.PID_AirSpeed.Kd = float(self.kd.get())

    def set(self,*args):
        self.kp.delete(0, 50)
        self.ki.delete(0, 50)
        self.kd.delete(0, 50)
        if self.variable.get()=="Heading":
            self.kp.insert(0,str(self.Principal.Qgc.Control.PID_Heading.Kp))
            self.ki.insert(0,str(self.Principal.Qgc.Control.PID_Heading.Ki))
            self.kd.insert(0,str(self.Principal.Qgc.Control.PID_Heading.Kd))

        elif self.variable.get()=="Rumbo":
            self.kp.insert(0,str(self.Principal.Qgc.Control.PID_Heading_Rumbo.Kp))
            self.ki.insert(0,str(self.Principal.Qgc.Control.PID_Heading_Rumbo.Ki))
            self.kd.insert(0,str(self.Principal.Qgc.Control.PID_Heading_Rumbo.Kd))

        elif self.variable.get()=="Altitud":
            self.kp.insert(0,str(self.Principal.Qgc.Control.PID_Altitud.Kp))
            self.ki.insert(0,str(self.Principal.Qgc.Control.PID_Altitud.Ki))
            self.kd.insert(0,str(self.Principal.Qgc.Control.PID_Altitud.Kd))

        elif self.variable.get()=="Roll":
            self.kp.insert(0,str(self.Principal.Qgc.Control.PID_Roll.Kp))
            self.ki.insert(0,str(self.Principal.Qgc.Control.PID_Roll.Ki))
            self.kd.insert(0,str(self.Principal.Qgc.Control.PID_Roll.Kd))

        elif self.variable.get()=="Pitch":
            self.kp.insert (0,str(self.Principal.Qgc.Control.PID_Pitch.Kp))
            self.ki.insert (0,str(self.Principal.Qgc.Control.PID_Pitch.Ki))
            self.kd.insert (0,str(self.Principal.Qgc.Control.PID_Pitch.Kd))

        else:
            self.kp.insert (0,str(self.Principal.Qgc.Control.PID_AirSpeed.Kp))
            self.ki.insert (0,str(self.Principal.Qgc.Control.PID_AirSpeed.Ki))
            self.kd.insert (0,str(self.Principal.Qgc.Control.PID_AirSpeed.Kd))

    def Sumar(self,opcion):
        paso=0.5
        if opcion==0:
            Valor_kp=float(self.kp.get())+paso
            self.kp.delete(0, 50)
            self.kp.insert (0,str(Valor_kp))
        elif opcion==1:
            Valor_ki = float(self.ki.get()) + paso
            self.ki.delete(0, 50)
            self.ki.insert (0,str(Valor_ki))
        else:
            Valor_kd = float(self.kd.get()) + paso
            self.kd.delete(0, 50)
            self.kd.insert (0,str(Valor_kd))

    def Restar(self,opcion):
        paso=0.5
        if opcion==0:
            Valor_kp=float(self.kp.get())-paso
            self.kp.delete(0, 50)
            self.kp.insert (0,str(Valor_kp))
        elif opcion==1:
            Valor_ki = float(self.ki.get()) - paso
            self.ki.delete(0, 50)
            self.ki.insert (0,str(Valor_ki))
        else:
            Valor_kd = float(self.kd.get()) - paso
            self.kd.delete(0, 50)
            self.kd.insert (0,str(Valor_kd))



class Pagina_Mission():
    def __init__(self,raiz,Qgc,Frame_principal):
        self.Qgc=Qgc
        self.Principal=Frame_principal
        miframe = Toplevel(raiz)
        miframe.title("Mission Creator")

        # ------------------------------------------------
        # -----------------Cajas texto--------------------
        # ------------------------------------------------
        self.Metros = Entry(miframe)
        self.Metros.grid(row=1, column=7)
        self.Latitud = Entry(miframe)
        self.Latitud.grid(row=2, column=7)
        self.Longitud = Entry(miframe)
        self.Longitud.grid(row=3, column=7)
        self.Velocidad = Entry(miframe)
        self.Velocidad.grid(row=4, column=7)
        self.FM = Entry(miframe)
        self.FM.grid(row=5, column=7)
        # ------------------------------------------------
        # -----------------Labels-------------------------
        # ------------------------------------------------
        Label(miframe, text="Metros:").grid(row=2, column=6)
        Label(miframe, text="Latitud:").grid(row=1, column=6)
        Label(miframe, text="Longitud:").grid(row=3, column=6)
        Label(miframe, text="Velocidad:").grid(row=4, column=6)
        Label(miframe, text="FM:").grid(row=5, column=6)
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.Save = Button(miframe, text=" Save ",command=self.save,bg='white')
        self.Save.grid(row=6, column=6)
        self.Add = Button(miframe, text=" Add ",command=self.add,bg='white')
        self.Add.grid(row=6, column=7)
        self.Delete = Button(miframe, text=" Delete ",command=self.delete,bg='white')
        self.Delete.grid(row=6, column=8)
        # ------------------------------------------------
        # -----------------Texto--------------------------
        # ------------------------------------------------
        self.Texto=Text(miframe)
        self.Texto.config(width=20, height=10)
        self.Texto.grid(row=7,column=7)
    def save(self):
        self.Principal.Qgc=self.Qgc
        self.Principal.Mission.configure(state=NORMAL)

    def add(self):
        if self.Metros.get()!="" and self.Latitud.get()!="" and self.Longitud.get()!=""and self.Velocidad.get()!=""and self.FM.get()!="":
            self.Qgc.Mission.append(LC.Waypoint(self.Latitud.get(),self.Longitud.get(),self.Metros.get(),self.Velocidad.get(),self.FM.get()))
            self.Texto.insert("insert", str(self.Latitud.get())+str(',')+str(self.Longitud.get())+str(',')+str(self.Metros.get())+str(',')+str(self.Velocidad.get())+str(',')+str(self.FM.get())+'\n')
    def delete(self):
        self.Qgc.Mission=[]
        self.Texto.delete(1.0,END)


class Pagina_Verbose():
    def __init__(self,raiz,Frame_principal):
        self.Principal=Frame_principal
        miframe = Toplevel(raiz)
        miframe.title("Verbose options")


        # ------------------------------------------------
        # -----------------Variables-------------------------
        # ------------------------------------------------
        self.Heading=IntVar()
        self.Altitud=IntVar()
        self.Roll=IntVar()
        self.pitch=IntVar()
        self.Vel=IntVar()
        self.Posicion = IntVar()
        self.Heading_save=IntVar()
        self.Altitud_save=IntVar()
        self.Roll_save=IntVar()
        self.pitch_save=IntVar()
        self.Vel_save=IntVar()
        self.Posicion_save = IntVar()
        self.Clean=IntVar()

        # ------------------------------------------------
        # -----------------ChecButtons--------------------
        # ------------------------------------------------
        self.Check_Heading=Checkbutton(miframe, text="Heading", variable=self.Heading, onvalue=1,offvalue=0)
        self.Check_Heading.pack()
        self.Check_Altitud=Checkbutton(miframe, text="Altitud", variable=self.Altitud, onvalue=1,offvalue=0)
        self.Check_Altitud.pack()
        self.Check_Roll=Checkbutton(miframe, text="Roll", variable=self.Roll, onvalue=1,offvalue=0)
        self.Check_Roll.pack()
        self.Check_Pitch=Checkbutton(miframe, text="Pitch", variable=self.pitch, onvalue=1,offvalue=0)
        self.Check_Pitch.pack()
        self.Check_Vel=Checkbutton(miframe, text="Vel", variable=self.Vel, onvalue=1,offvalue=0)
        self.Check_Vel.pack()
        self.Check_Posicion=Checkbutton(miframe, text="Posicion", variable=self.Posicion, onvalue=1,offvalue=0)
        self.Check_Posicion.pack()
        self.Check_Heading_save=Checkbutton(miframe, text="Heading save", variable=self.Heading_save, onvalue=1,offvalue=0)
        self.Check_Heading_save.pack()
        self.Check_Altitud_save=Checkbutton(miframe, text="Altitud save", variable=self.Altitud_save, onvalue=1,offvalue=0)
        self.Check_Altitud_save.pack()
        self.Check_Roll_save=Checkbutton(miframe, text="Roll save", variable=self.Roll_save, onvalue=1,offvalue=0)
        self.Check_Roll_save.pack()
        self.Check_Pitch_save=Checkbutton(miframe, text="Pitch save", variable=self.pitch_save, onvalue=1,offvalue=0)
        self.Check_Pitch_save.pack()
        self.Check_Vel_save=Checkbutton(miframe, text="Vel save", variable=self.Vel_save, onvalue=1,offvalue=0)
        self.Check_Vel_save.pack()
        self.Check_Posicion_save=Checkbutton(miframe, text="Posicion save", variable=self.Posicion_save, onvalue=1,offvalue=0)
        self.Check_Posicion_save.pack()
        self.Check_Clean=Checkbutton(miframe, text="Clean", variable=self.Clean, onvalue=1,offvalue=0)
        self.Check_Clean.pack()
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.Save = Button(miframe, text=" Save ",command=self.save,bg='white')
        self.Save.pack()
        self.set()

    def save(self):
        self.Principal.Verbose_options.Heading = self.Heading.get()
        self.Principal.Verbose_options.Altitud = self.Altitud.get()
        self.Principal.Verbose_options.Roll = self.Roll.get()
        self.Principal.Verbose_options.pitch = self.pitch.get()
        self.Principal.Verbose_options.Vel = self.Vel.get()
        self.Principal.Verbose_options.Posicion = self.Posicion.get()
        self.Principal.Verbose_options.Heading_save = self.Heading_save.get()
        self.Principal.Verbose_options.Altitud_save = self.Altitud_save.get()
        self.Principal.Verbose_options.Roll_save = self.Roll_save.get()
        self.Principal.Verbose_options.pitch_save = self.pitch_save.get()
        self.Principal.Verbose_options.Vel_save = self.Vel_save.get()
        self.Principal.Verbose_options.Posicion_save = self.Posicion_save.get()
        self.Principal.Verbose_options.Clean = self.Clean.get()

    def set(self):
        self.Heading.set(self.Principal.Verbose_options.Heading)
        self.Altitud.set(self.Principal.Verbose_options.Altitud)
        self.Roll.set(self.Principal.Verbose_options.Roll)
        self.pitch.set(self.Principal.Verbose_options.pitch)
        self.Vel.set(self.Principal.Verbose_options.Vel)
        self.Posicion.set(self.Principal.Verbose_options.Posicion)
        self.Heading_save.set(self.Principal.Verbose_options.Heading_save)
        self.Altitud_save.set(self.Principal.Verbose_options.Altitud_save)
        self.Roll_save.set(self.Principal.Verbose_options.Roll_save)
        self.pitch_save.set(self.Principal.Verbose_options.pitch_save)
        self.Vel_save.set(self.Principal.Verbose_options.Vel_save)
        self.Posicion_save.set(self.Principal.Verbose_options.Posicion_save)
        self.Clean.set(self.Principal.Verbose_options.Clean)

class Pagina_Plots():
    def __init__(self,raiz,fig):
        miframe = Toplevel(raiz)
        miframe.title("Plots")
        if fig is not None:
            canvas = FigureCanvasTkAgg(fig, master=miframe)
            plot_widget = canvas.get_tk_widget()
            plot_widget.pack(side=TOP, fill=BOTH, expand=1)
        else:
            miframe.destroy()


class Pagina_Comm():
    def __init__(self,raiz,main):
        miframe = Toplevel(raiz)
        miframe.title("Config")
        self.main=main
        # ------------------------------------------------
        # -----------------Variables-------------------------
        # ------------------------------------------------
        self.Port_send=StringVar()
        self.Port_recv=StringVar()
        self.IP=StringVar()
        # ------------------------------------------------
        # -----------------Labels-------------------------
        # ------------------------------------------------
        Label(miframe,text="Port_send: ").grid(row=1, column=1)
        Label(miframe,text="Port_recv: ").grid(row=2, column=1)
        Label(miframe,text="IP: ").grid(row=3, column=1)
        # ------------------------------------------------
        # -----------------Entry-------------------------
        # ------------------------------------------------
        self.Port_send_entry = Entry(miframe,textvariable=self.Port_send)
        self.Port_send_entry.grid(row=1, column=2)
        self.Port_recv_entry = Entry(miframe,textvariable=self.Port_recv)
        self.Port_recv_entry.grid(row=2, column=2)
        self.IP_entry = Entry(miframe,textvariable=self.IP)
        self.IP_entry.grid(row=3, column=2)
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.Save = Button(miframe, text=" Save ", command=self.save, bg='white')
        self.Save.grid(row=4, column=1)
        self.set()

    def save(self):
        self.main.Qgc.PortAdress_send = (self.IP.get(),int(self.Port_send.get()))
        self.main.Qgc.PortAdress_recv = (self.IP.get(),int(self.Port_recv.get()))
        print(self.main.Qgc.PortAdress_recv)
        self.main.Qgc.sock.bind(self.main.Qgc.PortAdress_recv)

    def set(self):
        recv = str(self.main.Qgc.PortAdress_recv).split(",")
        send = str(self.main.Qgc.PortAdress_send).split(",")
        Port_send=send[1].rstrip(')')
        Port_recv=recv[1].rstrip(')')
        Ip=recv[0].lstrip('(')
        self.Port_send.set(Port_send)
        self.Port_recv.set(Port_recv)
        self.IP.set(Ip)

class Pagina_IA():
    def __init__(self,raiz,main):
        miframe = Toplevel(raiz)
        miframe.title("Config")
        self.main=main
        # ------------------------------------------------
        # -----------------Botones------------------------
        # ------------------------------------------------
        self.Load_IA = Button(miframe, text=" Load IA ", command=self.Load, bg='white')
        self.Load_IA.grid(row=1, column=1)
        self.Load_IA_default = Button(miframe, text=" Load IA Default ", command=self.Load_default, bg='white')
        self.Load_IA_default.grid(row=2, column=1)


    def Load(self):
        Modelo = filedialog.askopenfilename(title="Abrir modelo")
        try:
            cnn = LC.load_model(Modelo)
            self.main.Qgc.Modelo=cnn
            self.main.Vision=LV.Vision(self.Qgc.Cola,self.Qgc.Modelo)
            self.main.AutoLand.configure(state=NORMAL)
            print('Cargado')
        except:
            print('Fallo al cargar el modelo')
            self.main.AutoLand.configure(state=DISABLED)

    def Load_default(self):
        Modelo = r'C:\Users\Juatarto\Desktop\TFM\Arquitecturas\Test\Epoca_10\Modelo_Capas_6_RGB_Epocas_10_Neuronas_256_Filtros_32_relu.h5'
        try:
            cnn = load_model(Modelo)
            self.main.Qgc.Modelo=cnn
            self.main.Vision=LV.Vision(self.main.Qgc.Cola,self.main.Qgc.Modelo)
            self.main.AutoLand.configure(state=NORMAL)
            print('Cargado')
        except:
            print('Fallo al cargar el modelo')
            self.main.AutoLand.configure(state=DISABLED)