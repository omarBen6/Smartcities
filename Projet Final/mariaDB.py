from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from TablesMariaDB import Image, Battrie, Temperature
from tkinter import*
from tkinter import ttk
import paho.mqtt.client as client
from datetime import datetime
import time

engine = create_engine("mariadb+mariadbconnector://martin:123456@192.168.2.35:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)


id_im = 0
id_bat = 0
id_temp = 0

def fctTopicBattrie(ud,c,m):
    global id_bat
    id_bat += 1
    pourc=m.payload.decode()
    date_reception = datetime.now()

    session = Session()
    maBattrie = Battrie(idb=id_bat,poucentage=pourc,date=date_reception)
    session.add(maBattrie)
    session.commit()
    session.close()

    print(f"Battrie: {m.payload}")

def fctTopicTemperature(ud,c,m):
    global id_temp
    id_temp += 1
    temp=m.payload.decode()
    date_reception = datetime.now()

    session = Session()
    maTemperature = Temperature(idt=id_temp,temperature=temp,date=date_reception)
    session.add(maTemperature)
    session.commit()
    session.close()

    print(f"Temperature: {m.payload}")

def fctTopicImage(ud,c,m):
    global id_im
    id_im += 1
    path_=m.payload.decode()
    date_reception = datetime.now()

    session = Session()
    monImage = Image(idi=id_im,path=path_,date=date_reception)
    session.add(monImage)
    session.commit()
    session.close()

    print(f"Image: {m.payload}")

cli = client.Client()
cli.connect("192.168.2.35", 1883)
cli.subscribe("B3/MartinOmar/parametre/temperature")
cli.subscribe("B3/MartinOmar/parametre/battrie")
cli.subscribe("B3/MartinOmar/image")

cli.message_callback_add("B3/MartinOmar/parametre/battrie",fctTopicBattrie)
cli.message_callback_add("B3/MartinOmar/parametre/temperature",fctTopicTemperature)
cli.message_callback_add("B3/MartinOmar/image",fctTopicImage)

cli.loop_start()

while True:
    print("Je suis dans ma boucle")
    time.sleep(5)

cli.loop_stop()

