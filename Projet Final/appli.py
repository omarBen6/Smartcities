from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# AJOUT : Import de la table Battrie
from TablesMariaDB import CamParametre, Wifi, Battrie 
from datetime import datetime
import paho.mqtt.client as mqtt
import json # AJOUT : Nécessaire pour passer les listes au JavaScript

app = Flask(__name__)

engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.58:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)

# On garde ton code de connexion MQTT tel quel
cli = mqtt.Client()
cli.connect("192.168.2.58", 1883)

# --- FONCTION UTILITAIRE POUR LES GRAPHIQUES ---
def get_battery_data():
    """Récupère les 50 dernières données de batterie pour les graphiques"""
    session = Session()
    # On récupère les données triées par date
    donnees = session.query(Battrie).order_by(Battrie.date.asc()).limit(50).all()
    session.close()

    # On prépare les listes
    labels = [d.date.strftime("%H:%M:%S") for d in donnees]
    levels = [d.poucentage for d in donnees] # Attention à l'orthographe 'poucentage' de ta BDD
    voltages = [d.voltage for d in donnees]

    return json.dumps(labels), json.dumps(levels), json.dumps(voltages)

# PAGE PRINCIPALE 
@app.route('/')
def index():
    # 1. Gestion des Images (Ton code original)
    image_folder = os.path.join(app.static_folder, "images")
    try:
        images = [
            f"images/{file}" for file in os.listdir(image_folder)
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        ]
        images.sort(reverse=True) # On trie pour voir les plus récentes d'abord
    except FileNotFoundError:
        images = []

    # 2. Gestion des Graphiques (NOUVEAU)
    dates_json, levels_json, voltages_json = get_battery_data()

    return render_template("index.html", 
                           images=images, 
                           dates_json=dates_json, 
                           levels_json=levels_json, 
                           voltages_json=voltages_json)
    
@app.route('/search')
def search():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    image_folder = os.path.join(app.static_folder, "images")
    try:
        all_images = [
            f"images/{file}" for file in os.listdir(image_folder)
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        ]
    except FileNotFoundError:
        all_images = []

    filtered_images = []
    for img in all_images:
        path = os.path.join(image_folder, os.path.basename(img))
        file_time = datetime.fromtimestamp(os.path.getmtime(path))

        if start_date and file_time < datetime.fromisoformat(start_date):
            continue
        if end_date and file_time > datetime.fromisoformat(end_date):
            continue

        filtered_images.append(img)
    
    # On renvoie aussi les données graphiques même lors d'une recherche
    dates_json, levels_json, voltages_json = get_battery_data()

    return render_template("index.html", 
                           images=filtered_images,
                           dates_json=dates_json, 
                           levels_json=levels_json, 
                           voltages_json=voltages_json)


# TRAITEMENT DES PARAMÈTRES
@app.route('/update_params', methods=['POST'])
def update_params():
    ssid = request.form.get('ssid')
    password = request.form.get('password')

    resolution = request.form.get('resolution')
    brightness = request.form.get('brightness')
    contrast = request.form.get('contrast')
    saturation = request.form.get('saturation')
    quality = request.form.get('quality')
    mirror = request.form.get('mirror') # Checkbox: renvoie 'on' ou None
    flip = request.form.get('flip')

    # Conversion des checkbox en booléen ou entier si nécessaire
    mirror_val = 1 if mirror else 0
    flip_val = 1 if flip else 0

    session = Session()
    
    # Création WiFi si des données sont entrées
    if ssid:
        new_param_wifi = Wifi(
            ssid=ssid,
            pasword=password,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(new_param_wifi)

    # Création Paramètres Caméra
    # Attention aux conversion int() qui peuvent planter si le champ est vide
    try:
        new_param = CamParametre(
            resolution=resolution,
            brightness=int(brightness) if brightness else 0,
            contrast=int(contrast) if contrast else 0,
            saturation=int(saturation) if saturation else 0,
            quality=int(quality) if quality else 10,
            mirror=mirror_val,
            flip=flip_val,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(new_param)
        session.commit()
        
        # Envoi MQTT seulement si succès DB
        cli.publish("B3/MartinOmar/parametre/camera/update","update")
        
    except Exception as e:
        print(f"Erreur lors de l'enregistrement : {e}")
        session.rollback()
    finally:
        session.close()

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
