# ![PyYTI](./images/Logo.SVG#gh-light-mode-only) ![PyYTI](./images/LogoDark.SVG#gh-dark-mode-only)
![Alpha](https://img.shields.io/badge/alpha-red) ![Stars](https://img.shields.io/github/stars/wuj1av/PyYTI?color=blue&style=square)

Простенький клиент для ютуба. Полностью бесплатный (работает на InnerTube), безопасный (обновляется каждое изменение / по issues), only-metadata (т.е. видео не качает; метаданных много).

ПРОЕКТ **НЕ** СВЯЗАН С ЮТУБОМ ***И ПОКА В АЛЬФЕ***!!1!!1!1!!11
## Оглавление
- [Установка](#установка)
- [Гайд](#базовый-пример)
- [Лицензия](#лицензия)
## Установка
Windows / Linux:
```terminal
python -m pip install pyyti
```
Git (исходники):
```terminal
git clone https://github.com/wuj1av/PyYTI
cd PyYTI
pip install -e .
```
## Базовый пример
```python
import pyyti

client = pyyti.YouTube()  # Сокращенная форма - pyyti.YT()

v = client.videos.get("dQw4w9WgXcQ")

print("Название: ", v.title)
```
Вывод:
```terminal
D:\PyYTI>test
Название: Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)

D:\PyYTI>
```
Дальше можно узнать в [официальной документации](https://wuj1av.github.io/PyYTI/doc/)
## Лицензия
Unlicense
