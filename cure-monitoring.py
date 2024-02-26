# Raspi Aushaerteueberwachung

# Funktion:
# Knopf 1s drücken, um die Messung zu starten (ab jetzt werden Temperaturdaten eingelesen und über das Kinetikmodell der Aushärtegrad bestimmt)
# Knopf erneut für 1s drücken, um die Messung wieder zu stoppen (die Daten werden in einer Exceltabelle mit den Spalten Zeit[s], Temperatur[K] und alpha gespeichert und im selben Ordner abespeichert, in dem sich dieses Programm befindet)

import numpy as np
import time
from math import isnan
import RPi.GPIO as GPIO     # ('#' zum Testen am PC)
import openpyxl

# Kinetikmodell nach Grindling:
def grindlingModell(alpha, T):

    K_2diffT_g, E_1, E_2, c_1, c_2, deltaTg, A_1, A_2, n_1, n_2, m = (1.88963840e-02, 7.74862316e+04, 5.26859969e+04, 4.56550329e-01, 1.44188898e+00, 2.78375900e+02, 1.75745854e+08, 2.25672390e+05, 3.07641009e+00, 1.31031748e+00, 6.25391337e-01)
    G_1 = 0.718172483
    G_2 = 2.375009844
    R = 8.31446     # ideale Gaskonstante

    T_g = (-37.195+273.15) * np.exp((G_1*alpha)/(G_2-alpha))
    E_1diff = R*pow(T_g,2)*(c_1/c_2)
    E_2diff = R*(c_1*c_2*pow((T_g+deltaTg),2))/pow((c_2+deltaTg),2)

    if T < T_g:
        K_2diff = K_2diffT_g * np.exp((-E_1diff/R)*(1/T-1/T_g))
    elif T <= (T_g+deltaTg):
        K_2diff = K_2diffT_g * np.exp((c_1*(T-T_g))/(c_2+T-T_g))
    else:
        K_2diff = K_2diffT_g * np.exp(c_1*(deltaTg)/(c_2+deltaTg))*np.exp((-E_2diff/R)*(1/T-1/(T_g+deltaTg)))

    K_1 = A_1*np.exp(-E_1/(R*T))
    K_2 = A_2*np.exp(-E_2/(R*T))
    K_eff = 1/(1/K_2diff+1/K_2)

    deltaAlphaDeltaZeit = (K_1*pow((1-alpha),n_1)+K_eff*pow(alpha,m)*pow((1-alpha),n_2))

    return deltaAlphaDeltaZeit

def toggle_button():
    if button_pushed == True:
        button_pushed = False
    else:
        button_pushed = True

def exportDataToExcel(data, name_exceldatei, name_sheet):   # schreibt eine list of lists in eine Exceltabelle gemäß listOfLists[zeile][spalte].

    workbook = openpyxl.Workbook()
    workbook.create_sheet(name_sheet)
    sheet = workbook[name_sheet]

    row_max = len(data)
    for row in range(row_max):
        col_max = len(data[row])
        for col in range(col_max):
            sheet.cell(row=row+1, column=col+1).value = data[row][col]

    workbook.save(filename=str(name_exceldatei))
    workbook.close()

def readTemperature():      # liest die Temperatur des Sensors aus. Falls der Wert 'nan' entspricht, wird ein neuer Messwert angefordert, bis eine gültige Zahl vorliegt
#    temp = sensor.readTempC()
    temp = 100  # Testtemperatur
    if isnan(temp):
        return(readTemperature())
    else:
        return(temp)

def giveTemperatureValue():
    temperatures = []
    for i in range(1,10):
        temp = readTemperature()
        temperatures.append(temp)
    temperatures.sort()
    trimmed = temperatures[2:-2]        # höchste und niedrigste zwei Werte werden entfernt
    average = sum(trimmed)/len(trimmed) # Durchschnittswert der Messwerte berechnen
    return(average)




#button_pushed = False
button_pushed = True
button_last_time_pressed = 0
alpha = 0.
alpha_list = []
clock = time.time()
startzeit = time.time()
time_list = []
Temperatur_list = []
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering       # ()'#' zum Testen am PC)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)         # ()'#' zum Testen am PC)

pause_between_measurements = 0.3

#while True:
for i in range(1,1000):
    if (time.time()-button_last_time_pressed > 5):  # ein Knopfdruck wird erst wieder 5s nach der letzten Betätigung registriert
        if GPIO.input(11) == GPIO.HIGH: #()'False' zum Testen am PC)
            toggle_button()
            button_last_time_pressed = time.time()
            if (button_pushed == True):
                clock = time.time()     # Startzeitpunkt der Messung setzen
                startzeit = clock
            else:                       # Messung Abschließen
                zeit = time.localtime(time.time())
                zeit_str = str(zeit.tm_year)+'-'+str(zeit.tm_mon)+'-'+str(zeit.tm_mday)+' '+str(zeit.tm_hour)+'-'+str(zeit.tm_min)+'-'+str(zeit.tm_sec)
                dateiname = zeit_str+'Aushaerteverlauf.xlsx'
                exportDataToExcel([time_list,Temperatur_list,alpha_list],dateiname,zeit_str)

    if (button_pushed == True):
        temp = giveTemperatureValue()+273.15    # aktuelle Temperatur in K anfordern
        #temp = 100+273.15   # Testtemperatur
        clock_new = time.time()
        delta_t = clock_new - clock
        alpha = alpha+(grindlingModell(alpha,temp) * delta_t)
        Temperatur_list.append(temp)
        time_list.append(clock_new-startzeit)
        alpha_list.append(alpha)
        clock = clock_new
        print('Zeit[s]:',time_list[-1],',  Temperatur[K]:', Temperatur_list[-1], ',  alpha:', alpha_list[-1])

    time.sleep(pause_between_measurements)


