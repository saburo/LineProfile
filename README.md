Line Profile
====

A [QGIS](http://www.qgis.org) plugin that make line profiles (transects) for [micro-QGIS](https://sites.google.com/a/wisc.edu/wiscsims-micro-qgis/).

## Description
Line Profile plugin is a [QGIS](http://www.qgis.org) plugin plotting line profiles for [micro-QGIS](https://sites.google.com/a/wisc.edu/wiscsims-micro-qgis/).

## Demo
![demo gif](img/demo.gif)
<!-- ## VS.  -->

## Requirement
This plugin is using following python modules:
* [GDAL Complete 1.11 framework package](http://www.kyngchaos.com/software/frameworks#gdal_complete)
* [Matplotlib Python module](http:/http://www.kyngchaos.com/files/software/python//www.kyngchaos.com/software/python)
* [NumPy](NumPy-1.8.0-1.dmg)

## Usage
プラグインのインストール後，ツールバーのアイコンをクリックすると下部にプラグインのドックが表示される．
目的のレイヤーを選択し，Add Dataボタンを押すとポップアップが表示されるので．プロットしたいデータを選択する．
断面線の始点クリックすると断面線が描かれる．右クリックで終点を設定できる．
断面線を描くと，自動的にLine Profileが描画される．

ドック右端にあるテーブルの，各データ名右にある歯車マークをダブルクリックすることによって，各データについてのオプションを設定できる．

RasterLayerとVectorLayerで，それぞれに選択できるオプションがある．
RasterLayer:
 Full resolution
 Moving average

VectorLayer:
 Maximum distance from the profile line
 Nearest vertix


## Installation
The most recent development version of Line Profile is available through the repository hosted on Github.
**With git command**
```sh
> cd path-to-qgis-plugin-folder (e.g.: ~/.qgis2/python/plugins)
> git clone https://github.com/saburo/LineProfile.git
```

**Without git command**
* Donwload zip file from [here](https://github.com/saburo/LineProfile/archive/master.zip)
* Unzip file and rename folder to "LineProfile"
* Copy the folder to QGIS plugin folder "`~/.qgis2/python/plugins/`"  

<!-- ## Contribution -->

## Licence
This plugin is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

## Author
Kouki Kitajima [[saburo](https://github.com/saburo)]  


Copyright © 2015 Kouki Kitajima
