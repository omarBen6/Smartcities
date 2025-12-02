from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from TablesMariaDB import Image, Battrie, Temperature, Wifi, CamParam
from tkinter import *
from tkinter import ttk
import paho.mqtt.client as client
from datetime import datetime
import time
import os
import base64

engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.45:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)

id_im = 0
id_bat = 0
id_temp = 0

# Variables pour la reconstruction d'image
image_chunks = {}            # Dictionnaire {index: bytes}
dernier_wifi = {}
dernier_cam = {}
nom_image_courante = None
image_en_reception = False   

def envoyerParametresVersESP32():
    global dernier_wifi, dernier_cam
    session = Session()

    # Récupérer les derniers paramètres Wi-Fi
    wifi = session.query(Wifi).order_by(Wifi.id.desc()).first()
    if wifi:
        data_wifi = {
            "ssid": wifi.ssid,
            "password": wifi.pasword
        }
        if data_wifi != dernier_wifi:
            print("Envoi des paramètres Wi-Fi :")
            cli.publish("B3/MartinOmar/parametre/wifi/ssid", str(wifi.ssid))
            print(f"ssid = {wifi.ssid}")
            cli.publish("B3/MartinOmar/parametre/wifi/password", str(wifi.pasword))
            print(f"password = {wifi.pasword}")
            dernier_wifi = data_wifi.copy()
    else:
        print("Aucun paramètre Wi-Fi trouvé en base.")

    # Récupérer les derniers paramètres caméra
    cam = session.query(CamParam).order_by(CamParam.id.desc()).first()
    if cam:
        data_cam = {
            "resolution": cam.resolution,
            "brightness": cam.brightness,
            "contrast": cam.contrast,
            "saturation": cam.saturation,
            "quality": cam.quality,
            "mirror": cam.mirror,
            "flip": cam.flip
        }
        if data_cam != dernier_cam:
            print("\nEnvoi des paramètres caméra :")
            cli.publish("B3/MartinOmar/parametre/camera/resolution", str(cam.resolution))
            cli.publish("B3/MartinOmar/parametre/camera/brightness", str(cam.brightness))
            cli.publish("B3/MartinOmar/parametre/camera/contrast", str(cam.contrast))
            cli.publish("B3/MartinOmar/parametre/camera/saturation", str(cam.saturation))
            cli.publish("B3/MartinOmar/parametre/camera/quality", str(cam.quality))
            cli.publish("B3/MartinOmar/parametre/camera/mirror", str(cam.mirror))
            cli.publish("B3/MartinOmar/parametre/camera/flip", str(cam.flip))
            print("Paramètres caméra envoyés.")
            dernier_cam = data_cam.copy()
    else:
        print("Aucun paramètre caméra trouvé en base.")

    session.close()

# Callbacks MQTT
def fctTopicBattrie(ud, c, m):
    global id_bat
    id_bat += 1
    pourc = m.payload.decode()
    date_reception = datetime.now()

    session = Session()
    maBattrie = Battrie(idb=id_bat, poucentage=pourc, date=date_reception)
    session.add(maBattrie)
    session.commit()
    session.close()

    print(f"Batterie: {m.payload.decode()}")


def fctTopicTemperature(ud, c, m):
    global id_temp
    id_temp += 1
    temp = m.payload.decode()
    date_reception = datetime.now()

    session = Session()
    maTemperature = Temperature(idt=id_temp, temperature=temp, date=date_reception)
    session.add(maTemperature)
    session.commit()
    session.close()

    print(f"Température: {m.payload.decode()}")


def fctTopicImage(ud, c, m):
    global id_im, image_chunks, nom_image_courante, image_en_reception

    topic = m.topic
    payload = m.payload

    # Début de la transmission
    if topic == "B3/MartinOmar/image/start":
        nom_image_courante = payload.decode().strip()
        image_chunks = {}
        image_en_reception = True
        print(f"Début réception de {nom_image_courante}")

    # Réception d'un morceau avec index
    elif topic == "B3/MartinOmar/image/data":
        try:
            message = payload.decode()
            # Découper le message en "index|base64data"
            index_str, chunk_b64 = message.split("|", 1)
            index = int(index_str)
            image_chunks[index] = base64.b64decode(chunk_b64)
            print(f"Morceau #{index} reçu ({len(chunk_b64)} caractères base64)")
        except Exception as e:
            print("Erreur lors du traitement d’un morceau :", e)

    # Fin de la transmission
    elif topic == "B3/MartinOmar/image/end" and image_en_reception:
        id_im += 1

        # Créer le dossier de destination s'il n'existe pas!!!!
        dossier_destination = r"C:\Users\UItilisateur\Desktop\BAc 3\Smartcities\ImagesRecues"
        os.makedirs(dossier_destination, exist_ok=True)

        # 🔹 Générer un nom d'image unique (avec horodatage précis)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nom_fichier_unique = f"image_{timestamp}.jpg"
        chemin_complet = os.path.join(dossier_destination, nom_fichier_unique)

        try:
            # Réassembler les morceaux dans le bon ordre
            image_finale = b"".join(image_chunks[i] for i in sorted(image_chunks.keys()))

            # Écrire l'image sur le disque
            with open(chemin_complet, "wb") as f:
                f.write(image_finale)

            print(f"Image terminée : {chemin_complet} ({len(image_finale)} octets)")

            # Enregistrer le chemin et la date dans la base MariaDB
            session = Session()
            monImage = Image(
                idi=id_im,
                path=chemin_complet,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(monImage)
            session.commit()
            session.close()

        except Exception as e:
            print("Erreur lors de la reconstruction :", e)

        # Réinitialiser les variables pour la prochaine image
        image_chunks = {}
        nom_image_courante = None
        image_en_reception = False

    else:
        print("Paquet reçu hors contexte image.")




# Connexion MQTT
cli = client.Client()
cli.connect("192.168.2.35", 1883)

cli.subscribe("B3/MartinOmar/parametre/temperature")
cli.subscribe("B3/MartinOmar/parametre/battrie")
cli.subscribe("B3/MartinOmar/image/start")
cli.subscribe("B3/MartinOmar/image/data", qos=1)  # QoS 1 : garantit la réception
cli.subscribe("B3/MartinOmar/image/end")

cli.message_callback_add("B3/MartinOmar/parametre/battrie", fctTopicBattrie)
cli.message_callback_add("B3/MartinOmar/parametre/temperature", fctTopicTemperature)
cli.message_callback_add("B3/MartinOmar/image/start", fctTopicImage)
cli.message_callback_add("B3/MartinOmar/image/data", fctTopicImage)
cli.message_callback_add("B3/MartinOmar/image/end", fctTopicImage)

cli.loop_start()

while True:
    print("Je suis dans ma boucle")
    envoyerParametresVersESP32()
    time.sleep(5)

cli.loop_stop()
