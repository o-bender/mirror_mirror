# mirror_mirror

```
sudo apt update
sudo apt install build-essential cmake
sudo apt install libopenblas-dev liblapack-dev 
sudo apt install libx11-dev libgtk-3-dev
sudo apt install python python-dev python-pip
sudo apt install python3 python3-dev python3-pip
```

```
pip install dlib
```

### Калибровка гаммы
```
python3 main.py -adjust-gamma 1 --calibrate-adjust-gamma
```

### Тренировка модели
--train - имя будущей модели
--images - папка с фотографиями
```
python3 main.py --train pavel --images models
```