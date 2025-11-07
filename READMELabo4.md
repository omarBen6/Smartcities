# Sound Reactive RGB LED with BPM Detection

## Description
Ce projet utilise un capteur sonore et une LED RGB WS2812 connectés à un Raspberry Pi Pico pour détecter le rythme cardiaque (BPM) ou le rythme sonore environnant.  
Chaque battement détecté change la couleur de la LED et le programme enregistre les valeurs moyennes du BPM dans un fichier `bpm_log.txt`.

---

## Matériel requis
- Raspberry Pi Pico (ou Pico W)  
- Capteur sonore analogique (connecté sur GP26 / ADC0)  
- LED RGB WS2812 (connectée sur GP20)  
- Câbles Dupont  
- MicroPython installé sur le Pico  

---

## Fonctionnement
1. Le Pico lit les valeurs du capteur sonore via l’entrée ADC(0).  
2. Il calcule une moyenne du bruit et détecte les pics (battements).  
3. Chaque battement provoque un changement de couleur RGB.  
4. Le BPM est calculé avec la formule :  BPM = 60000 / (new_time - last_time)
5. Toutes les minutes, le BPM moyen est sauvegardé dans `bpm_log.txt`.

---

## Couleurs RGB
La couleur affichée dépend :
- du niveau sonore moyen,  
- du dernier battement détecté,  
- et d’une variable `led_value` pour faire varier les teintes.  

---

## Fichier généré
Le fichier `bpm_log.txt` contient l’historique des moyennes de BPM : (2025, 11, 6, 14, 22, 30, 3, 310): 72.5 BPM

---

## Fonctions principales
lecture() : Met à jour la liste des valeurs sonores récentes. 
moyenne() : Calcule et lisse la moyenne du bruit. 
BPM_function() : Calcule le BPM actuel à partir du temps entre deux battements. 
LED() : Change la couleur de la LED RGB à chaque battement. 
writting() : Enregistre le BPM moyen toutes les 60 secondes. 

