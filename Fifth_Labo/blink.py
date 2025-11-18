#<----------------------------------->
#Import of the different library 
from machine import Pin, PWM
import machine
from utime import sleep
import utime
import urequests
import gc
import json
import network
import time
import socket
import sys
import uerrno
#<////////////////////////////////////>


#<----------------------------------->
#Function reads the data from the worldtimeapi to have the time 
def Lecture_of_time(time_utc, index, new_time):
    first = False
    last_time=new_time
    try :
        print("######################################")
        response =urequests.get(f'https://worldtimeapi.org/api/timezone/{time_utc[index]}')#tihs is the website of the API
                    
        data =(response.json())#Transform the data into a Json
        datetime_str = data['datetime']#Get the interesting data
        gtm = data['timezone']#Get the gtm time
        print("Le gtm renvoyé par l'api est : ",gtm)
        #try to obtain the corresponding data into the right format
        try :
            heure  = int(datetime_str[11:13])  
            minute = int(datetime_str[14:16])   
            seconde = int(datetime_str[17:19]) 
        #Management of the different types of errors
        except IndexError:
            print("Le formatage des données n'est pas correct")
                        
        except ValueError:
                print("Les données recues ne correspondent pas aux valeurs attendues")
        except Exception as e:
            print("[ERREUR]", type(e).__name__, e)

        response.close()#it closes the HTTPs connexion
        gc.collect()#it realeses the RAM memory
        print(f"L'heure actuelle du fuseau horaire : {time_utc[index]}, l'heure actuelle est de :{heure} {minute} {seconde}")#Display the different data
    #this are the mainly different erros which are met
    except OSError as e:
        if e.args[0] == uerrno.EHOSTUNREACH:
            print("Hôte injoignable (EHOSTUNREACH)")
        elif e.args[0] == uerrno.ECONNRESET:
            print("Le serveur a coupé la connexion avec le Raspberry 2w")
        #This is for the others possibilities
        else :
            print("[ERREUR]", type(e).__name__, e)

    return heure, minute,seconde, first, last_time
#<////////////////////////////////////>



#<----------------------------------->
#Function which adds one to the index 
def Index(index,new_time, time_utc):
    if index == len(time_utc):
        index=0
    else :
        index +=1
    
    boutom_pressed=new_time#it is used to pressed the buttom one time
    print(f"Le fuseau horaire actuelle est le : {time_utc[index]}")
    return index, boutom_pressed
#<////////////////////////////////////>


#<----------------------------------->
#Function which changes the reference time
def Change_time(new_time, change, heure_ref):
    last_time_bottom=new_time
    if change:
        change = False
        heure_ref = 24
    else :
        change = True
        heure_ref = 12
    print("l'heure de ref est :",heure_ref)
    return last_time_bottom, heure_ref, change  
#<////////////////////////////////////>


#<----------------------------------->
#Function which displays the differents datas
def Print(new_time, heure_ref, freq, time_utc, index):
    affichage=new_time
    print(time_utc[index])
    print("l'heure de la référence",heure_ref)
    print("la fréquence est de", freq)
    return affichage
#<////////////////////////////////////>           

#<----------------------------------->
#Set the pin of the differents parts and the frequency of the motor
moteur = PWM(Pin(20))
button = machine.Pin(16, machine.Pin.IN)
moteur.freq(100)
#<////////////////////////////////////>    
 

#<----------------------------------->
#Set the data to be connected
ssid = input("Donnez le nom du wifi :")       
password = input("Donnez le mdp du wifi")
ssid = ssid.replace(' ','')
password = password.replace(' ','')
#<////////////////////////////////////>


#<----------------------------------->
#try to be connected to the network and displays the errors
try :
    wlan = network.WLAN(network.STA_IF)  
    wlan.active(True)
    print("Affichage des différents wifis disponnibles :", wlan.scan()) 
    print(f"Tentative de connexion avec le réseau wifi : {ssid}, avec comme mdp : {password}")                   
    wlan.connect(ssid, password)
except Exception as e:
    print("Erreur dans l'utlisation de la bibliothèque Network :")
    print("[ERREUR]", type(e).__name__, e)
#<////////////////////////////////////>    
 
#<----------------------------------->
#Watch if it is connectd after 10 seconds. if it is not the scipt
#will do anything. 
max_wait = 10
while max_wait > 0:
    if wlan.isconnected():
        max_wait=0
    print('Connexion en cours...')
    time.sleep(1)
    max_wait -= 1
 
if wlan.isconnected():#Display the different data over the connexion
    print('Connecté !')
    print('Adresse IP :', wlan.ifconfig()[0])
    next = True 
else:
    print('Échec de connexion.')
    next = False
#<////////////////////////////////////> 


#<----------------------------------->
#Set initial data which are used in the cript
last_time = utime.ticks_ms()
last_time_bottom=last_time
affichage = last_time
buttom_pressed=0
time_utc = ["Etc/GMT","Etc/GMT+0","Etc/GMT+1","Etc/GMT+10","Etc/GMT+11","Etc/GMT+12","Etc/GMT+2","Etc/GMT+3","Etc/GMT+4","Etc/GMT+5","Etc/GMT+6","Etc/GMT+7","Etc/GMT+8","Etc/GMT+9","Etc/GMT-0","Etc/GMT-1","Etc/GMT-10","Etc/GMT-11","Etc/GMT-12","Etc/GMT-13","Etc/GMT-14","Etc/GMT-2","Etc/GMT-3","Etc/GMT-4","Etc/GMT-5","Etc/GMT-6","Etc/GMT-7","Etc/GMT-8","Etc/GMT-9","Etc/GMT0","Etc/Greenwich","Etc/UCT","Etc/UTC","Etc/Universal","Etc/Zulu"]
index = 0
change =True
heure_ref = 12
pressed = False
first = True
heure = 0
#<////////////////////////////////////> 

#<----------------------------------->
#infinite loop of the script
if next:
    while True:
        try:
    
            new_time = utime.ticks_ms()
            if button.value()==1 :
                #if the bottom was pressed one time or two time it changes differents parameters
                print("heure de ref",new_time-boutom_pressed)
                if new_time-boutom_pressed>1000:#if the bottom was pressed two times it wil change the utc
                    index, boutom_pressed =Index(index,new_time, time_utc)
                    
                if new_time-last_time_bottom>250:#if the bottom was pressed one time it chnages the timre reference
                    last_time_bottom, heure_ref, change =Change_time(new_time, change, heure_ref)

            else :
                boutom_pressed=new_time

            if (new_time-last_time)>6000 or first:#Every second it reads the datas from the API
                heure, minute,seconde, first, last_time = Lecture_of_time(time_utc, index, new_time)

            if change:#Allows us to display 24 hour into 12 values 0hour to 12hour
                heure = heure%12  

            #calculate the freq which depends on the time
            freq = int((13000/heure_ref)*(heure)+4000)
            #the motor will move 
            moteur.duty_u16(freq)

            #It displays the datas
            if (new_time-affichage)>5000:
                affichage = Print(new_time, heure_ref, freq, time_utc, index)

        #Allow us to shut down the scipt   
        except KeyboardInterrupt:
                print("La fin du programme")
                sys.exit()
        #it reads the differents errors
        except Exception as e:
            print("[ERREUR]", type(e).__name__, e)
#<////////////////////////////////////> 

    
 