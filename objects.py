
# ----------- /// -----------
# Importações!

# Importa as funções auxiliares
from aux import *
import numpy as np
import math as mt

# ----------- /// -----------

class Object:

    qtd_texturas = 0

    __idTextureAvailable=0
    __vIniAvailable=0
    vertices_list = []
    textures_coord_list = []

    def __init__(self,model_file,texture_file,escala=0.5,d_x=0,d_y=0,d_z=0,t_x=0,t_y=0,t_z=0):

        self.model_file = model_file
        self.texture_file = texture_file
        self.ID = self.setId()

        self.vIni = -1
        self.vCount = -1
        
        self.qtd_texturas+=1

        self.dx=d_x
        self.dy=d_y
        self.dz=d_z
        self.tx=t_x
        self.ty=t_y
        self.tz=t_z
        self.escala=escala

        self.eXMin = float('inf')
        self.eXMax = float('-inf')
        self.eYMin = float('inf')
        self.eYMax = float('-inf')
        self.eZMin = float('inf')
        self.eZMax = float('-inf')

        # Matrizes de transformação do objeto:
        cos_dx = mt.cos(d_x)
        sin_dx = mt.sin(d_x)
        cos_dy = mt.cos(d_y)
        sin_dy = mt.sin(d_y)
        cos_dz = mt.cos(d_z)
        sin_dz = mt.sin(d_z)
        
        self.__mat_rotation_x = np.array([1.0,   0.0,    0.0, 0.0, 
                                        0.0, cos_dx, -sin_dx, 0.0, 
                                        0.0, sin_dx,  cos_dx, 0.0, 
                                        0.0,   0.0,    0.0, 1.0], np.float32)
        
        self.__mat_rotation_y = np.array([cos_dy,  0.0, sin_dy, 0.0, 
                                        0.0,    1.0,   0.0, 0.0, 
                                        -sin_dy, 0.0, cos_dy, 0.0, 
                                        0.0,    0.0,   0.0, 1.0], np.float32)
        
        self.__mat_rotation_z = np.array([cos_dz, -sin_dz, 0.0, 0.0, 
                                        sin_dz,  cos_dz, 0.0, 0.0, 
                                        0.0,      0.0, 1.0, 0.0, 
                                        0.0,      0.0, 0.0, 1.0], np.float32)
        
        self.__mat_translation = np.array([1.0,  0.0, 0.0, t_x, 
                                          0.0,  1.0, 0.0, t_y, 
                                          0.0,  0.0, 1.0, t_z, 
                                          0.0,  0.0, 0.0, 1.0], np.float32)
        
        self.__mat_escala = np.array([escala,  0.0, 0.0, 0.0, 
                                    0.0,  escala, 0.0, 0.0, 
                                    0.0,  0.0, escala, 0.0, 
                                    0.0,  0.0, 0.0, 1.0], np.float32)

    def load(self,tecMag=GL_LINEAR):

        self.vIni = Object.__vIniAvailable

        modelo = load_model_from_file(self.model_file)

        for face in modelo['faces']:
            for vertice_id in face[0]:
                Object.vertices_list.append( modelo['vertices'][vertice_id-1] )
            for texture_id in face[1]:
                Object.textures_coord_list.append( modelo['texture'][texture_id-1] )

        Object.__vIniAvailable = len(Object.vertices_list)
        self.vCount = len(Object.vertices_list) - self.vIni

        load_texture_from_file(self.ID,self.texture_file,tecMag=tecMag)

        #print(self.vertices_list[self.vIni : self.vIni + self.vCount])

        self.__extremidades(self.vertices_list[self.vIni : self.vIni + self.vCount])

        self.__centralizar()

        #print(self.eXMin,self.eXMax,self.eYMin,self.eYMax)

    def __centralizar(self):

        vCentral = np.array([(self.eXMax-self.eXMin)/2,(self.eYMax-self.eYMin)/2,(self.eZMax-self.eZMin)/2,1.0])
        vCentral = self.getMatTransform().reshape(4,4) @ vCentral

        #self.tx -= vCentral[0]
        self.ty -= vCentral[1]
        #self.tz -= vCentral[2]

    def __extremidades(self,vList):
            
        for v in vList:

            if(float(v[0]) < self.eXMin):
                self.eXMin = float(v[0])
            elif(float(v[0]) > self.eXMax):
                self.eXMax = float(v[0])
            elif(float(v[1]) < self.eYMin):
                self.eYMin = float(v[1])
            elif(float(v[1]) > self.eYMax):
                self.eYMax = float(v[1])
            elif(float(v[2]) < self.eZMin):
                self.eZMin = float(v[2])
            elif(float(v[2]) > self.eZMax):
                self.eZMax = float(v[2])

    def setId(self):

        Object.__idTextureAvailable += 1 # incrementa o Id

        return (Object.__idTextureAvailable - 1)
    
    def draw(self):

        # faz o bind da textura
        glBindTexture(GL_TEXTURE_2D, self.ID)
    
        # desenha o modelo
        glDrawArrays(GL_TRIANGLES, self.vIni, self.vCount)

    def getMatTransform(self):

        # Atualiza as matrizes de transformação para o estado mais atual
        self.updateMatriz()
        
        mat_transform = multiplica_matriz(self.__mat_translation,self.__mat_rotation_z)
        mat_transform = multiplica_matriz(mat_transform,self.__mat_rotation_y)
        mat_transform = multiplica_matriz(mat_transform,self.__mat_rotation_x)
        mat_transform = multiplica_matriz(mat_transform,self.__mat_escala)

        # Matriz já com as colisões devidamente tratadas
        mat_transform = self.checaColisao(mat_transform)
        
        return mat_transform
    
    def checaColisao(self,mat):

        matAux = mat.reshape(4,4)

        # Paralelepípedo de segurança
        # Este paralelepípedo lida com as colisões do objeto
        vExtremos = [
                     [self.eXMax,self.eYMax,self.eZMax,1.0],[self.eXMax,self.eYMin,self.eZMax,1.0],
                     [self.eXMax,self.eYMax,self.eZMin,1.0],[self.eXMax,self.eYMin,self.eZMin,1.0],
                     [self.eXMin,self.eYMax,self.eZMax,1.0],[self.eXMin,self.eYMin,self.eZMax,1.0],
                     [self.eXMin,self.eYMax,self.eZMin,1.0],[self.eXMin,self.eYMin,self.eZMin,1.0]
                    ]

        # Analisa extremidades para fora do espaço
        for vAntes in vExtremos:

            vDepois = matAux @ vAntes

            if(vDepois[0] > 1):
                self.tx -= (vDepois[0] - 1)
                matAux[0][3] -= (vDepois[0] - 1)

            if(vDepois[1] > 1):
                self.ty -= (vDepois[1] - 1)
                matAux[1][3] -= (vDepois[1] - 1)

            if(vDepois[0] < -1):
                self.tx -= (vDepois[0] + 1)
                matAux[0][3] -= (vDepois[0] + 1)

            if(vDepois[1] < -1):
                self.ty -= (vDepois[1] + 1)
                matAux[1][3] -= (vDepois[1] + 1)

        # Analisa escala grande demais
        for vAntes in vExtremos:

            vFixed = matAux @ vAntes

            if(abs(vFixed[0]) > 1 or abs(vFixed[1]) > 1 or abs(vFixed[2]) > 1):

                maxError = max(abs(vFixed[0]),abs(vFixed[1]),abs(vFixed[2]))

                self.escala -= (maxError - 1)/100
                matAux[0][0] -= (maxError - 1)/100
                matAux[1][1] -= (maxError - 1)/100
                matAux[2][2] -= (maxError - 1)/100

        return matAux.reshape(1,16)
    
    def updateMatriz(self):

        # Translação:
        self.__mat_translation[3] = self.tx
        self.__mat_translation[7] = self.ty
        self.__mat_translation[11] = self.tz

        # Rotação:
        cos_dx = mt.cos(self.dx)
        sin_dx = mt.sin(self.dx)

        self.__mat_rotation_x[5] = cos_dx
        self.__mat_rotation_x[6] = -sin_dx
        self.__mat_rotation_x[9] = sin_dx
        self.__mat_rotation_x[10] = cos_dx
        
        cos_dy = mt.cos(self.dy)
        sin_dy = mt.sin(self.dy)

        self.__mat_rotation_y[0] = cos_dy
        self.__mat_rotation_y[2] = sin_dy
        self.__mat_rotation_y[8] = -sin_dy
        self.__mat_rotation_y[10] = cos_dy

        cos_dz = mt.cos(self.dz)
        sin_dz = mt.sin(self.dz)

        self.__mat_rotation_z[0] = cos_dz
        self.__mat_rotation_z[1] = -sin_dz
        self.__mat_rotation_z[4] = sin_dz
        self.__mat_rotation_z[5] = cos_dz
        
        # Escala:
        self.__mat_escala[0] = self.escala
        self.__mat_escala[5] = self.escala
        self.__mat_escala[10] = self.escala

        return

# ----------- /// -----------