from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from TablesMariaDB import CamParametre, Wifi, Battrie, Image, Camera
from datetime import datetime
import paho.mqtt.client as mqtt
import json 

app = Flask(__name__)

engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.58:3306/RPG", echo=True)
Session = sessionmaker(bind=engine)

# --- CONFIGURATION MQTT (Juste pour l'envoi) ---
# On ne définit PAS de on_message ici, car c'est mariaDB.py qui gère la réception.
cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cli.connect("192.168.2.58", 1883)
cli.loop_start() 

def get_battery_data(cam_id):
    session = Session()
    donnees = session.query(Battrie).filter(Battrie.NumeroCam == cam_id).order_by(Battrie.date.asc()).limit(50).all()
    session.close()

    labels = [d.date for d in donnees]
    levels = [d.poucentage for d in donnees]
    voltages = [d.voltage for d in donnees]

    return json.dumps(labels), json.dumps(levels), json.dumps(voltages)

@app.route('/')
def index():
    session = Session()
    
    # 1. Menu déroulant : Récupérer toutes les caméras
    cameras = session.query(Camera).all()
    
    # 2. Quelle caméra afficher ?
    cam_id_arg = request.args.get('cam_id', type=int)
    
    selected_cam = None
    if cameras:
        if cam_id_arg:
            for cam in cameras:
                if cam.id == cam_id_arg:
                    selected_cam = cam
                    break
        if not selected_cam:
            selected_cam = cameras[0]
            
    current_id = selected_cam.id if selected_cam else 0

    # 3. Données pour la caméra sélectionnée
    images_db = session.query(Image).filter(Image.NumeroCam == current_id).order_by(Image.date.desc()).all()
    current_config = session.query(CamParametre).filter(CamParametre.NumeroCam == current_id).order_by(CamParametre.id.desc()).first()
    
    session.close()

    images_data = []
    for img in images_db:
        nom_fichier = os.path.basename(img.path)
        images_data.append({"id": img.idi, "url": f"images/{nom_fichier}", "date": img.date})

    dates_json, levels_json, voltages_json = get_battery_data(current_id)

    return render_template("index.html", 
                           images=images_data,
                           dates_json=dates_json, 
                           levels_json=levels_json, 
                           voltages_json=voltages_json,
                           cameras=cameras,          
                           selected_cam=selected_cam, 
                           config=current_config)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    session = Session()
    image_to_delete = session.query(Image).filter_by(idi=image_id).first()
    
    if image_to_delete:
        try:
            if os.path.exists(image_to_delete.path):
                os.remove(image_to_delete.path)
        except Exception as e:
            print(f"Erreur suppression fichier : {e}")

        session.delete(image_to_delete)
        session.commit()
        
    session.close()
    return redirect(url_for('index'))    
    
@app.route('/update_params', methods=['POST'])
def update_params():
    cam_id = request.form.get('cam_id', type=int) # L'ID vient du formulaire caché ou du select
    
    # Si cam_id est None, on ne peut rien faire
    if not cam_id:
        return redirect(url_for('index'))

    ssid = request.form.get('ssid')
    password = request.form.get('password')

    resolution = request.form.get('resolution')
    brightness = request.form.get('brightness')
    contrast = request.form.get('contrast')
    saturation = request.form.get('saturation')
    quality = request.form.get('quality')
    mirror = request.form.get('mirror')
    flip = request.form.get('flip')

    mirror_val = 1 if mirror else 0
    flip_val = 1 if flip else 0

    session = Session()
    
    if ssid:
        new_param_wifi = Wifi(NumeroCam=cam_id, ssid=ssid, pasword=password, date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        session.add(new_param_wifi)

    try:
        new_param = CamParametre(
            NumeroCam=cam_id,
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
        
        # Envoi MQTT : On cible la caméra spécifique ou le topic général
        # Pour faire simple, on envoie le signal d'update
        cli.publish("B3/MartinOmar/parametre/camera/update", "update")
        
    except Exception as e:
        print(f"Erreur enregistrement : {e}")
        session.rollback()
    finally:
        session.close()

    return redirect(url_for('index', cam_id=cam_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
