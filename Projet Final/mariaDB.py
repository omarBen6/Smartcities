from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from TablesMariaDB import Image, Battrie, Wifi, CamParametre, Camera
import paho.mqtt.client as client
from datetime import datetime
import time
import os
import base64

# Configuration BDD
engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.58:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)

# Dictionnaires pour gérer plusieurs caméras en même temps
# Structure : { camera_id : [chunk1, chunk2, ...] }
buffers_images = {} 
noms_images = {}

# Variables globales config
dernier_wifi = {}
dernier_cam = {}
update = False

def envoyerParametresVersESP32(cli):
    global dernier_wifi, dernier_cam
    session = Session()

    # NOTE: Ici, on envoie à TOUTES les caméras via le wildcard '+' si nécessaire
    # ou on pourrait cibler une caméra spécifique si on gérait une file d'attente.
    
    # --- Code d'envoi conservé (simplifié pour l'exemple) ---
    # Pour l'instant, on publie sur un topic générique (sans ID spécifique)
    # Si tu veux configurer la Caméra 1, le topic devrait être B3/MartinOmar/1/...
    cam = session.query(CamParametre).order_by(CamParametre.id.desc()).first()
    if cam:
        cli.publish("B3/MartinOmar/parametre/camera/resolution", str(cam.resolution))
        # ... (reste des publications) ...
        print("Paramètres envoyés aux caméras.")
    
    session.close()

# --- CALLBACKS MQTT ---

def fctTopicBattrie(client, userdata, message):
    try:
        topic = message.topic
        payload = message.payload.decode()
        
        # 1. Extraction de l'ID de la caméra depuis le topic
        # Ex: B3/MartinOmar/1/parametre/battrie/level
        parts = topic.split('/')
        if len(parts) < 3 or not parts[2].isdigit():
            return # Topic invalide
            
        cam_id = int(parts[2]) 
        
        pourc = 0
        volt = 0.0

        # On traite selon le type de message
        if "level" in topic:
            pourc = int(float(payload)) # Conversion safe
            print(f"[Cam {cam_id}] Batterie Level: {pourc}%")
        elif "tension" in topic:
            volt = float(payload)
            print(f"[Cam {cam_id}] Tension: {volt}V")

        # Enregistrement en BDD
        # Note: Idéalement, il faudrait grouper level et tension, 
        # mais ici on insère dès qu'on reçoit une info pour simplifier.
        session = Session()
        maBattrie = Battrie(
            NumeroCam=cam_id,  # AJOUT IMPORTANT : On lie à la caméra
            poucentage=pourc,
            voltage=volt,
            date=datetime.now()
        )
        session.add(maBattrie)
        session.commit()
        session.close()

    except Exception as e:
        print(f"Erreur Batterie: {e}")


def fctTopicImage(client, userdata, message):
    global buffers_images, noms_images

    topic = message.topic
    
    # 1. Extraction ID Caméra
    parts = topic.split('/')
    if len(parts) < 3 or not parts[2].isdigit():
        return
    cam_id = int(parts[2])

    if "start" in topic:
        nom_fic = message.payload.decode().strip()
        buffers_images[cam_id] = [] # On initialise une liste pour CETTE caméra
        noms_images[cam_id] = nom_fic
        print(f"[Cam {cam_id}] Début réception : {nom_fic}")

    elif "data" in topic:
        # On ajoute le morceau au buffer de CETTE caméra
        if cam_id in buffers_images:
            buffers_images[cam_id].append(message.payload.decode())
            # Optionnel: print un point pour montrer l'activité
            # print(".", end="", flush=True) 

    elif "end" in topic:
        if cam_id in buffers_images and len(buffers_images[cam_id]) > 0:
            print(f"\n[Cam {cam_id}] Fin réception. Reconstruction...")
            
            try:
                # Reconstruction
                full_data_str = "".join(buffers_images[cam_id])
                image_bytes = base64.b64decode(full_data_str)
                
                # Chemin
                dossier = r"/home/martin/Desktop/smartcities/static/images"
                os.makedirs(dossier, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nom_final = f"cam{cam_id}_{timestamp}.jpg"
                chemin_complet = os.path.join(dossier, nom_final)

                # Écriture disque
                with open(chemin_complet, "wb") as f:
                    f.write(image_bytes)
                
                # Écriture BDD
                session = Session()
                nouvelle_image = Image(
                    NumeroCam=cam_id, # AJOUT IMPORTANT
                    path=chemin_complet, # Stocke le chemin, pas les bytes
                    date=datetime.now()
                )
                session.add(nouvelle_image)
                session.commit()
                session.close()
                print(f"[Cam {cam_id}] Image sauvegardée : {nom_final}")

            except Exception as e:
                print(f"[Cam {cam_id}] Erreur reconstruction : {e}")
            
            # Nettoyage mémoire pour cette caméra
            buffers_images[cam_id] = []
            noms_images[cam_id] = None


def fctTopicUpdate(client, userdata, message):
    global update
    print("Demande de mise à jour reçue.")
    update = True


# --- CONFIGURATION MQTT ---
cli = client.Client()
cli.connect("192.168.2.58", 1883)

# 1. Abonnements avec le Wildcard '+' pour l'ID
# Ex: B3/MartinOmar/1/image/start
cli.subscribe("B3/MartinOmar/+/parametre/battrie/#") # '#' attrape level et tension
cli.subscribe("B3/MartinOmar/+/image/start")
cli.subscribe("B3/MartinOmar/+/image/data", qos=1)
cli.subscribe("B3/MartinOmar/+/image/end")
cli.subscribe("B3/MartinOmar/parametre/camera/update") # Celui-ci peut rester global

# 2. Ajout des callbacks AVEC le wildcard '+'
# C'est ici que tu avais l'erreur principale
cli.message_callback_add("B3/MartinOmar/+/parametre/battrie/#", fctTopicBattrie)
cli.message_callback_add("B3/MartinOmar/+/image/start", fctTopicImage)
cli.message_callback_add("B3/MartinOmar/+/image/data", fctTopicImage)
cli.message_callback_add("B3/MartinOmar/+/image/end", fctTopicImage)
cli.message_callback_add("B3/MartinOmar/parametre/camera/update", fctTopicUpdate)

print("Système prêt. En attente de données...")
cli.loop_start()

while True:
    if update:
        envoyerParametresVersESP32(cli)
        update = False
    time.sleep(1)
