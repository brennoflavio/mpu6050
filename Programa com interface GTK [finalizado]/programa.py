#!/usr/bin/python
# coding=UTF-8

#Imports
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import threading
import smbus
import RPi.GPIO as GPIO
import math
import os
import time
import numpy#excluir
import matplotlib.pyplot as plot

#Widgets Importadas
builder = Gtk.Builder()
builder.add_from_file('interface.glade')
janela_principal = builder.get_object('windowprincipal')
janela_offset = builder.get_object('windowoffset')
janela_sensibilidades = builder.get_object('windowsensibilidades')
janela_sobre = builder.get_object('windowsobre')

#Variáveis Globais
loop = False
aceleracao_x = 0.
aceleracao_y = 0.
aceleracao_z = 0.
velocidade_x = 0.
velocidade_y = 0.
velocidade_z = 0.
angulo_x = 0.
angulo_y = 0.
angulo_z = 0.
temperatura_operacao = 0.
tempo = 0.
frequencia = 1.
acelerometro_lsb = 16384.
giroscopio_lsb = 131.
offset_accx = -0.005558989
offset_accy = -0.0182035954
offset_accz = -0.0002035166
offset_velx = -7.8690237043
offset_vely = 5.1442011517
offset_velz = 0.6606066693
iniciado = False





#Determinar a revisão do Raspi
myBus=""
if GPIO.RPI_INFO['P1_REVISION'] == 1:
	myBus=0
else:
	myBus=1
bus = smbus.SMBus(myBus)

def mpu6050():
	global aceleracao_x, aceleracao_y, aceleracao_z, velocidade_x, velocidade_y, velocidade_z, angulo_x, angulo_y, angulo_z, temperatura_operacao, tempo, frequencia, acelerometro_lsb, giroscopio_lsb, offset_accx, offset_accy, offset_accz, offset_velx, offset_vely, offset_velz, bus
	
	#Variáveis globais
	
	endereco_sensor = 0x68
	
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
		
	arquivo = open('dados.txt','w')
	arquivo.write('Tempo[s],AceleracaoX[g][m/s2],AceleracaoY[g][m/s2],AceleracaoZ[g][m/s2],VelocidadeX[o/s],VelocidadeY[o/s],VelocidadeZ[o/s],AnguloX[o],AnguloY[o],AnguloZ[o],Temperatura[C]'+'\n')
	
	now = time.time()
	
	while True:
		if loop == False:
			break
		
		(aceleracao_x,aceleracao_y,aceleracao_z) = normaliza(accx(),accy(),accz())
		(angulo_x,angulo_y,angulo_z) = angulo(aceleracao_x,aceleracao_y,aceleracao_z),angulo(aceleracao_y,aceleracao_x,aceleracao_z),angulo(aceleracao_z,aceleracao_x,aceleracao_y)
		(velocidade_x,velocidade_y,velocidade_z) = girox(),giroy(),giroz()
		temperatura_operacao = temperatura()
		tempo = time.time()-now
		
		arquivo.write(str(tempo)+','+str(aceleracao_x)+','+str(aceleracao_y)+','+str(aceleracao_z)+','+str(velocidade_x)+','+str(velocidade_y)+','+str(velocidade_z)+','+str(angulo_x)+','+str(angulo_y)+','+str(angulo_z)+','+str(temperatura_operacao)+'\n')
		
		time.sleep(1./frequencia)

def labels():
	global loop,aceleracao_x,aceleracao_y,aceleracao_z,velocidade_x,velocidade_y,velocidade_z,angulo_x,angulo_y,angulo_z,temperatura_operacao,tempo,frequencia
	
	label_accx = builder.get_object('labelaccx')
	label_accy = builder.get_object('labelaccy')
	label_accz = builder.get_object('labelaccz')
	label_velx = builder.get_object('labelvelx')
	label_vely = builder.get_object('labelvely')
	label_velz = builder.get_object('labelvelz')
	label_angx = builder.get_object('labelangx')
	label_angy = builder.get_object('labelangy')
	label_angz = builder.get_object('labelangz')
	
	while True:
		if loop == False:
			janela_principal.set_title('Centro de controle MPU6050')
			break
		
		janela_principal.set_title('MPU6050 - Frequência: '+str(frequencia)+'Hz - Temperatura: '+str(round(temperatura_operacao,2))+'ºC - Tempo: '+str(round(tempo,2))+'s')
		label_angx.set_text(str(round(angulo_x,2)))
		label_angy.set_text(str(round(angulo_y,2)))
		label_angz.set_text(str(round(angulo_z,2)))
		label_accx.set_text(str(round(aceleracao_x,2)))
		label_accy.set_text(str(round(aceleracao_y,2)))
		label_accz.set_text(str(round(aceleracao_z,2)))
		label_velx.set_text(str(round(velocidade_x,2)))
		label_vely.set_text(str(round(velocidade_y,2)))
		label_velz.set_text(str(round(velocidade_z,2)))
		
		time.sleep(1)

def graficos():
	global loop, aceleracao_x,aceleracao_y,aceleracao_z,velocidade_x,velocidade_y,velocidade_z,angulo_x,angulo_y,angulo_z,tempo
	
	tipo_grafico = builder.get_object('caixagrafico')
	tipo_eixo = builder.get_object('caixaeixo')
	
	#Angulo
	if tipo_grafico.get_active() == 0:
		#X
		if tipo_eixo.get_active() == 0:
			plot.ion()
			while True:
				plot.scatter(tempo,angulo_x)
				plot.pause(0.05)
		#Y	
		elif tipo_eixo.get_active() == 1:
			plot.ion()
			while True:
				plot.scatter(tempo,angulo_y)
				plot.pause(0.05)
		#Z
		elif tipo_eixo.get_active() == 2:
			plot.ion()
			while True:
				plot.scatter(tempo,angulo_z)
				plot.pause(0.05)
				
		else:
			print "Erro! Angulo selecionado, mas sem eixo"
	#Aceleração
	elif tipo_grafico.get_active() == 1:
		#X
		if tipo_eixo.get_active() == 0:
			plot.ion()
			while True:
				plot.scatter(tempo,aceleracao_x)
				plot.pause(0.05)
		#Y
		elif tipo_eixo.get_active() == 1:
			plot.ion()
			while True:
				plot.scatter(tempo,aceleracao_y)
				plot.pause(0.05)
		#Z
		elif tipo_eixo.get_active() == 2:
			plot.ion()
			while True:
				plot.scatter(tempo,aceleracao_z)
				plot.pause(0.05)
		else:
			print "Erro! Aceleração selecionado, mas sem eixo"
	#Velocidade Angular
	elif tipo_grafico.get_active() == 2:
		#X
		if tipo_eixo.get_active() == 0:
			plot.ion()
			while True:
				plot.scatter(tempo,velocidade_x)
				plot.pause(0.05)
		#Y
		elif tipo_eixo.get_active() == 1:
			plot.ion()
			while True:
				plot.scatter(tempo,velocidade_y)
				plot.pause(0.05)
		#Z
		elif tipo_eixo.get_active() == 2:
			plot.ion()
			while True:
				plot.scatter(tempo,velocidade_z)
				plot.pause(0.05)
				
		else:
			print "Erro! Velocidade Angular selecionada mas sem eixo"
	else:
		print "Erro! Tipo de gráfico não selecionado"

#Esta função retorna o botão ativo de uma lista de Radio buttons
def botao_ativo(botao):
	radiobutton = botao.get_group()
	for radio in radiobutton:
		if radio.get_active():
			return radio.get_label()

class sinais:
	def gtk_main_quit(self,*args):
		Gtk.main_quit()
		
	def on_iniciar_clicked(self,*args):
		global loop, iniciado
		
		if iniciado == False:
			if loop == False:
				iniciado = True
				loop = True
				loop_mpu6050 = threading.Thread(target=mpu6050)
				loop_mpu6050.daemon = True
				loop_mpu6050.start()
			
			loop_labels = threading.Thread(target=labels)
			loop_labels.daemon = True
			loop_labels.start()
		
	def on_parar_clicked(self,*args):
		global loop, iniciado
		loop = False
		iniciado = False
		
	def on_botaogerargrafico_clicked(self,*args):
		global loop
			
		loop_graficos = threading.Thread(target=graficos)
		loop_graficos.daemon = True
		loop_graficos.start()
	
	def on_sensibilidades_activate(self,*args):
		janela_sensibilidades.show_all()
		
	def on_calibrar_activate(self,*args):
		janela_offset.show_all()
		
	def on_sobre_activate(self,*args):
		janela_sobre.run()
		janela_sobre.hide()
		
	def gtk_sensibilidades_hide(self,*args):
		janela_sensibilidades.hide()
		return True
		
	def on_botaoconfirmasensibilidades_clicked(self,*args):
		global iniciado, loop, acelerometro_lsb, giroscopio_lsb, frequencia
		loop = False
		iniciado = False
		
		radio_acelerometro = builder.get_object('botao2g')
		radio_giroscopio = builder.get_object('botao250')
		caixa_frequencia = builder.get_object('caixafrequencia')
		
		sens_acelerometro = botao_ativo(radio_acelerometro)
		sens_giroscopio = botao_ativo(radio_giroscopio)
		
		bus.write_byte_data(0x68, 0x1C, 0x00)
		bus.write_byte_data(0X68, 0X1C, 0x00)
		
		if sens_acelerometro == '±2g':
			bus.write_byte_data(0x68, 0x1c, 0x00)
			acelerometro_lsb = 16384.
		elif sens_acelerometro == '±4g':
			bus.write_byte_data(0x68, 0x1c, 0x08)
			acelerometro_lsb = 8192.
		elif sens_acelerometro == '±8g':
			bus.write_byte_data(0x68, 0x1c, 0x10)
			acelerometro_lsb = 4096.
		elif sens_acelerometro == '±16g':
			bus.write_byte_data(0x68, 0x1c, 0x18)
			acelerometro_lsb = 2048.
			
		if sens_giroscopio == '±250 º/s':
			bus.write_byte_data(0x68, 0x1b, 0x00)
			giroscopio_lsb = 131.
		elif sens_giroscopio == '±500 º/s':
			bus.write_byte_data(0x68, 0x1b, 0x08)
			giroscopio_lsb = 65.5
		elif sens_giroscopio == '±1000 º/s':
			bus.write_byte_data(0x68, 0x1b, 0x10)
			giroscopio_lsb = 32.8
		elif sens_giroscopio == '±2000 º/s':
			bus.write_byte_data(0x68, 0x1b, 0x18)
			giroscopio_lsb = 16.4
			
		frequencia = float(caixa_frequencia.get_text())
		
		janela_sensibilidades.hide()
		return True
		
	def gtk_windowoffset_hide(self,*args):
		janela_offset.hide()
		return True
		
	def on_botaooffsetconfirmar_clicked(self,*args):
		global iniciado, loop, offset_accx, offset_accy, offset_accz, offset_velx, offset_vely, offset_velz
		loop = False
		iniciado = False
		
		off_vx = builder.get_object('caixavxoffset')
		off_vy = builder.get_object('caixavyoffset')
		off_vz = builder.get_object('caixavzoffset')
		
		off_ax = builder.get_object('caixaaxoffset')
		off_ay = builder.get_object('caixaayoffset')
		off_az = builder.get_object('caixaazoffset')
		
		offset_accx = float(off_ax.get_text())
		offset_accy = float(off_ay.get_text())
		offset_accz = float(off_az.get_text())
		
		offset_velx = float(off_vx.get_text())
		offset_vely = float(off_vy.get_text())
		offset_velz = float(off_vz.get_text())
		
		janela_offset.hide()
		return True
		
builder.connect_signals(sinais())
janela_principal.show_all()
Gtk.main()

