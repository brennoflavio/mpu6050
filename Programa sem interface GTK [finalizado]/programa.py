#!/usr/bin/python
# coding=UTF-8

#Imports
import smbus
import RPi.GPIO as GPIO
import math
import os
import time

def mpu6050():
	#Determinar a revisão do Raspi
	myBus=""
	if GPIO.RPI_INFO['P1_REVISION'] == 1:
		myBus=0
	else:
		myBus=1
			
	#Variáveis globais
	bus = smbus.SMBus(myBus)
	endereco_sensor = 0x68
	#Mudar o LSB de acordo com a faixa de operação escolhida. Ver no datasheet
	acelerometro_lsb = 16384.
	giroscopio_lsb = 131.
	frequencia = 1. #[hz]
	
	#offsets
	offset_accx = -0.005558989
	offset_accy = -0.0182035954
	offset_accz = -0.0002035166
	offset_velx = -7.8690237043
	offset_vely = 5.1442011517
	offset_velz = 0.6606066693
	
	#Range de operação. 0x1c corresponde ao acelerômetro, e 0x1b em giroscópio. 0x00(2g/250), 0x08(4g/500), 0x10(8g/1000), 0x18(16,2000)
	bus.write_byte_data(endereco_sensor,0x1c,0x00)
	bus.write_byte_data(endereco_sensor,0x1b,0x00)
	
	#Acorda o sensor
	bus.write_byte_data(endereco_sensor,0x6b,0x00)
	
	#Retorna valores do sensor
	def leitura_i2c(registro):
		high = bus.read_byte_data(endereco_sensor, registro)
		low = bus.read_byte_data(endereco_sensor, registro+1)
		valor = (high << 8) + low
		
		if (valor >= 0x8000):
			return -((65535 -valor)+1)
		else:
			return valor
			
	#Variáveis do sensor
	#Velocidades angulares em torno dos eixos	
	def girox():
		giroscopio = leitura_i2c(0x43)
		giroscopio = giroscopio/giroscopio_lsb
		return giroscopio-offset_velx
		
	def giroy():
		giroscopio = leitura_i2c(0x45)
		giroscopio = giroscopio/giroscopio_lsb
		return giroscopio-offset_vely
		
	def giroz():
		giroscopio = leitura_i2c(0x47)
		giroscopio = giroscopio/giroscopio_lsb
		return giroscopio-offset_velz
	
	#Aceleração nos eixos
	def accx():
		acelerometro = leitura_i2c(0x3b)
		acelerometro = acelerometro/acelerometro_lsb
		return acelerometro-offset_accx
		
	def accy():
		acelerometro = leitura_i2c(0x3d)
		acelerometro = acelerometro/acelerometro_lsb
		return acelerometro-offset_accy
		
	def accz():
		acelerometro = leitura_i2c(0x3f)
		acelerometro = acelerometro/acelerometro_lsb
		return acelerometro-offset_accz
	
	#Temperatura
	def temperatura():
		temperatura = leitura_i2c(0x41)
		temperatura = (temperatura/340.)+36.53
		return temperatura
		
	#Função que obtém o ângulo de um vetor e sua projeção (x), através de suas três projeções (x, y, z)
	def angulo(x,y,z):
		angulo = math.atan2(x,(math.sqrt(y*y+z*z)))
		angulo = math.degrees(angulo)
		return angulo
		
	#Função que normaliza um vetor
	def normaliza(x,y,z):
		r = math.sqrt(x*x+y*y+z*z)
		return x/r,y/r,z/r
		
	arquivo = open('dados','w')
	arquivo.write('Tempo[s],AceleracaoX[g][m/s2],AceleracaoY[g][m/s2],AceleracaoZ[g][m/s2],VelocidadeX[o/s],VelocidadeY[o/s],VelocidadeZ[o/s],AnguloX[o],AnguloY[o],AnguloZ[o],Temperatura[C]'+'\n')
	
	now = time.time()
	
	while True:
		(aceleracao_x,aceleracao_y,aceleracao_z) = normaliza(accx(),accy(),accz())
		(angulo_x,angulo_y,angulo_z) = angulo(aceleracao_x,aceleracao_y,aceleracao_z),angulo(aceleracao_y,aceleracao_x,aceleracao_z),angulo(aceleracao_z,aceleracao_x,aceleracao_y)
		(velocidade_x,velocidade_y,velocidade_z) = girox(),giroy(),giroz()
		temp_operacao = temperatura()
		
		print "Centro de controle MPU6050. Para mais informações: brenno.flavio412@gmail.com"
		print " "
		print "Dados do sensor"
		print "--"
		print "Temperatura de operação [C]: ",temp_operacao
		print "--"
		print "Aceleração em X [g][m/s2]: ",aceleracao_x
		print "Aceleração em Y [g][m/s2]: ",aceleracao_y
		print "Aceleração em Z [g][m/s2]: ",aceleracao_z
		print "--"
		print "Velocidade angular em torno de X [o/s]: ",velocidade_x
		print "Velocidade angular em torno de Y [o/s]: ",velocidade_y
		print "Velocidade angular em torno de Z [o/s]: ",velocidade_z
		print " "
		print "----"
		print "Dados calculados"
		print "Ângulo do vetor g com aceleração em X [o]: ",angulo_x
		print "Ângulo do vetor g com aceleração em Y [o]: ",angulo_y
		print "Ângulo do vetor g com aceleração em Z [o]: ",angulo_z
		print " "
		print "----"
		print "Tempo [s]: ",(time.time()-now) 
		
		arquivo.write(str(time.time()-now)+','+str(aceleracao_x)+','+str(aceleracao_y)+','+str(aceleracao_z)+','+str(velocidade_x)+','+str(velocidade_y)+','+str(velocidade_z)+','+str(angulo_x)+','+str(angulo_y)+','+str(angulo_z)+','+str(temp_operacao)+'\n')
		
		time.sleep(1./frequencia)
		os.system('clear')
			
mpu6050()
		
		
		
	
		
	
	
	
	
