# ============================
# FICHIER : appli.py
# Rôle : Serveur Flask pour configurer le Wi-Fi et les paramètres de la caméra ESP32
# ============================

from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from TablesMariaDB import CamParam, Wifi
from datetime import datetime

app = Flask(__name__)

engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.45:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)
id_param = 0
id_wifi = 0

# ============================
# PAGE PRINCIPALE "/"
# ============================
@app.route('/')
def index():
    # Récupère les images dans static/images/
    image_folder = os.path.join(app.static_folder, "images")
    images = [
        f"images/{file}" for file in os.listdir(image_folder)
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]
    return render_template("index.html", images=images)

# ============================
# TRAITEMENT DES PARAMÈTRES ENVOYÉS PAR LE FORMULAIRE
# ============================
@app.route('/update_params', methods=['POST'])
def update_params():
    # Paramètres Wi-Fi
    global id_param, id_wifi
    id_wifi += 1
    ssid = request.form.get('ssid')
    password = request.form.get('password')

    # Paramètres
    id_param += 1
    resolution = request.form.get('resolution')
    brightness = request.form.get('brightness')
    contrast = request.form.get('contrast')
    saturation = request.form.get('saturation')
    quality = request.form.get('quality')
    mirror = request.form.get('mirror')
    flip = request.form.get('flip')

    session = Session()
    new_param = CamParam(
        id=id_param,
        resolution=resolution,
        brightness=int(brightness),
        contrast=int(contrast),
        saturation=int(saturation),
        quality=int(quality),
        mirror=mirror,
        flip=flip,
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    session.add(new_param)
    session.commit()

    new_param_wifi = Wifi(
        id=id_wifi,
        ssid=ssid,
        pasword=password,
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    session.add(new_param_wifi)
    session.commit()

    # Exemple d’envoi vers l’ESP32 (à activer plus tard)
    # import requests
    # esp32_url = "http://192.168.1.50/config"
    # requests.post(esp32_url, data=request.form)

    return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(debug=True)
