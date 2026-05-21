# Training Zone — Simulation bateau ROS2/Gazebo

Environnement de simulation d'un bateau autonome basé sur [VRX](https://github.com/osrf/vrx), adapté pour un robot à **1 moteur + 1 gouvernail** commandé via `/cmd_vel`.

---

## Prérequis

- Ubuntu 24.04 + ROS2 Jazzy
- Gazebo Harmonic (gz-sim 8)
- Le workspace compilé :

```bash
git clone https://github.com/guivarchVauban/training_zone
cd training_zone
colcon build
source install/setup.bash
```

> Relancer `colcon build` + `source install/setup.bash` après toute modification de fichier Python (`.py`) dans `vrx_gz/src/` ou `vrx_gz/scripts/`  ou des fichiers `.sdf` (monde)

---

## Lancement

```bash
cd training_zone
./launch.sh
```

Ce script :
1. Tue les processus Gazebo résiduels d'une session précédente
2. Lance le nœud de téléopération joystick (`teleop_twist_joy` + `joy`)
3. Lance la simulation complète (`vrx_gz competition.launch.py`)

---

## Architecture du monde simulé

### Repère et coordonnées GPS

L'origine `(x=0, y=0)` du monde Gazebo correspond aux coordonnées GPS réelles :

| Paramètre | Valeur |
|-----------|--------|
| Latitude  | 48.292509° N |
| Longitude | -5.240584° E |
| Zone      | Au large de Brest |

Le repère local suit la convention **ENU** (East-North-Up) :
- **+x** = Est
- **+y** = Nord
- **+z** = Haut

### Position du bateau au démarrage

Le WAM-V spawne à l'origine : `(x=0, y=0, z=0)`, cap vers l'Est (+x).

### Les bouées

6 bouées forment un **hexagone régulier** centré à 200 m devant le spawn, avec 100 m entre bouées adjacentes :

| # | Couleur | x (m) | y (m) | Angle |
|---|---------|--------|--------|-------|
| 0 | Rouge        | 300  |   0  |   0° |
| 1 | Noire        | 250  | +87  |  60° |
| 2 | Verte        | 150  | +87  | 120° |
| 3 | Blanche      | 100  |   0  | 180° |
| 4 | Orange ronde | 150  | -87  | 240° |
| 5 | Noire ronde  | 250  | -87  | 300° |

Circuit suggéré (sens horaire) : **B0 → B1 → B2 → B3 → B4 → B5 → B0**

### Le bateau cible

Une frégate statique (silhouette type FREMM, ~120 m) est positionnée à :
- `(x=400, y=0)` — 400 m devant le spawn
- Orientée **de profil** (côté visible depuis la caméra du WAM-V)

---

## Topics ROS2

### Commande du robot

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | Commande principale du bateau |

Le champ `linear.x` contrôle la **poussée** (valeur normalisée, 1.0 = poussée max ~1500 N).
Le champ `angular.z` contrôle **l'angle de gouvernail** (valeur normalisée, 1.0 = ~0.5 rad ≈ 28°).

```bash
# Exemple : avancer et tourner à gauche
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.3}}"
```

### Capteurs

| Topic | Type | Description |
|-------|------|-------------|
| `/fix` | `sensor_msgs/NavSatFix` | Position GPS (latitude, longitude) |
| `/imu/data` | `sensor_msgs/Imu` | Centrale inertielle (orientation, accélération) |
| `/image_raw` | `sensor_msgs/Image` | Image caméra frontale |
| `/camera_info` | `sensor_msgs/CameraInfo` | Paramètres intrinsèques de la caméra |

### Topics utilitaires

| Topic | Description |
|-------|-------------|
| `/tf` / `/tf_static` | Arbre de transformations (repères) |
| `/clock` | Horloge de simulation |
| `/wamv/joint_states` | État des articulations du robot |

```bash
# Lister tous les topics actifs
ros2 topic list

# Voir la position GPS en temps réel
ros2 topic echo /gps/fix
```

---

## Personnalisation

### Changer la position GPS de l'origine

Fichier : `vrx_gz/worlds/brest_coast.sdf`

```xml
<spherical_coordinates>
  <latitude_deg>48.292509</latitude_deg>   <!-- modifier ici -->
  <longitude_deg>-5.240584</longitude_deg> <!-- modifier ici -->
  <elevation>0.0</elevation>
</spherical_coordinates>
```



### Déplacer le bateau au spawn

Fichier : `vrx_gz/launch/competition.launch.py`, ligne ~48

```python
m = Model(robot_name, model_type, [0, 0, 0, 0, 0, 0])
#                                   x  y  z  R  P  Y
```

> Recompilation nécessaire (`colcon build --merge-install`).

### Déplacer ou ajouter des bouées

Fichier : `vrx_gz/worlds/brest_coast.sdf`

Chaque bouée suit ce format :

```xml
<include>
  <name>buoy_0_red</name>
  <pose>300.0 0.0 0 0 0 0</pose>   <!-- x y z roulis tangage cap -->
  <uri>https://fuel.gazebosim.org/1.0/openrobotics/models/mb_marker_buoy_red</uri>
  ...
</include>
```

Modèles de bouées disponibles :
- `mb_marker_buoy_red` / `_black` / `_green` / `_white` — bouées cylindriques
- `mb_round_buoy_orange` / `mb_round_buoy_black` — bouées sphériques



### Déplacer le bateau cible

Fichier : `vrx_gz/worlds/brest_coast.sdf`

```xml
<model name="target_warship">
  <static>true</static>
  <pose>400 0 0 0 0 1.5708</pose>
  <!--      x y z R P Y         -->
  <!-- yaw=1.5708 rad = profil face au WAM-V depuis (0,0) -->
  <!-- yaw=0                    = proue face au WAM-V     -->
```



### Changer les topics des capteurs

Fichier : `vrx_gz/src/vrx_gz/payload_bridges.py`

Les fonctions `imu()`, `navsat()`, `image()`, `camera_info()` définissent les noms de topics via le champ `ros_topic`. Un chemin commençant par `/` est **absolu** (ignore le namespace `/wamv`).

```python
def imu(...):
    return Bridge(
        ...
        ros_topic='/imu/data',   # <- modifier ici
    )
```

> Recompilation nécessaire.

### Changer les paramètres de propulsion

Fichier : `vrx_gz/scripts/cmd_vel_to_thrusters.py`

```python
self.declare_parameter('max_thrust', 1500.0)  # Newtons
self.declare_parameter('max_angle',  0.5)     # radians (~28°)
```

> Recompilation nécessaire.

---

## Structure des fichiers clés

```
training_zone/
├── launch.sh                          # Script de lancement principal
├── vrx_gz/
│   ├── worlds/
│   │   └── brest_coast.sdf            # Monde simulé (bouées, bateau cible, GPS...)
│   ├── launch/
│   │   └── competition.launch.py      # Position de spawn du robot
│   ├── scripts/
│   │   └── cmd_vel_to_thrusters.py    # Conversion /cmd_vel -> moteurs
│   └── src/vrx_gz/
│       ├── model.py                   # Capteurs activés (GPS, IMU, caméra...)
│       ├── bridges.py                 # Bridges ROS<->Gazebo globaux
│       └── payload_bridges.py        # Bridges ROS<->Gazebo par capteur
└── vrx_urdf/
    └── wamv_gazebo/urdf/              # Modèle URDF/xacro du bateau
```

---

## Dépannage

**Plusieurs bateaux apparaissent à chaque relance**
→ `./launch.sh` tue automatiquement Gazebo. Si le problème persiste : `pkill -f "gz sim"`

**Les topics ne sont pas publiés**
→ Vérifier que le build est à jour : `colcon build --merge-install && source install/setup.bash`

**Gazebo ne démarre pas / crash**
→ Vérifier les variables d'environnement : `source /opt/ros/jazzy/setup.bash` puis `source install/setup.bash`
