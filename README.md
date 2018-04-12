
# [XBillBoard](http://www.samir-kherraz.tk/apps/xbillboard)

A tool to transform your ubuntu/debian into a billboard

[View in my blog](http://www.samir-kherraz.tk/apps/xbillboard)

<center><img src="http://www.samir-kherraz.tk/public/uploads/xbillboard/xbillboard.svg" width="100%"/></center>

* * *

## Execution

In order execute the application call `xbillboard-start` on a terminal

* * *

## The boot `__main__.py`

The boot is used to start the application, initialize the Gtk window and build the interface.

Each screen is a gtk.gtkgl.DrawingArea in opengl mode or a gtk.DrawingArea

The boot also allows to initialize the threads for round Robin screens as well as those for synchronization

* * *

## Screen Manager `Screen.py`

Allows you to load the cached files and make a Robin round on the list of compatible files.  
the list of compatible file types is PDF JPEG JPG PNG GIF.

Each screen will be displayed during a waiting time defined in the configuration file except for gifs that last the duration of the animation. do not confuse screen and file. a file to contain a set of screens clearly for PDFs: each page is a screen and remains on screen for the time defined in the configuration file.

In case of error on a file (corrupted for example) the logo of xbillboard will be displayed instead for the duration of the waiting time

* * *

## Sync & cache `Sync.py`

Each instance will call wget every Delay seconds to check if the file has changed or not. if yes, it will be re-downloaded.

* * *

## Configuration `xbillboard.conf`

The configuration file is duplicated during the installation and at each launch of the application if it does not exist. 

There is a default configuration file `/etc/xbillboard/xbillboard.conf` [default config]

The configuration file to handle is `$HOME/.xbillboard/xbillboard.conf`


| General ||
|--|---|
|Sync_Delay|The waiting time between each synchronization attempt in seconds|
|Screen_Delay|The wait time at each screen second|
|Sync_Directory|The synchronization directory|
|OpenGL|Use of openGl <br> Values : YES / NO|
|LayoutX|Number of screens in horizontal|
|LayoutY|Number of screens in vertical|
|Screen_List|The list of active screens, separated by a carriage return.<br>  The screens must be listed in the following order  <br> \| 1 \| 2 \| 3 \|<br>\| 4 \| 5 \| 6 \|
|Screen_Main|Identifier if the main screen|
|Screen_Rotation|Number of rotation before switching screen|
|Screen_Alignement|Align to inside container <br> Format : VERTICAL::HORIZENTAL <br> VERTICAL Values : TOP / DOWN / CENTER <br> HORIZENTAL Values : LEFT / RIGHT / CENTER|
|Screen_Ratio|Screen ratio either to FIT or to STRETCH<br> Values : FIT / STRETCH|



|ScreenX ||
|---|---|
|FileList|The list of files to display on the screen.<br> the list is separated by carriage returns|
|Delay|This parameter is an overload of General::Screen_Delay<br> The wait time on the screen in question in seconds|
|CopyOf|Allows to make a copy of another screen|
|Rotation|This parameter is an overload of General::Screen_Rotation<br> Number of rotation before switching screen|
|Alignement|This parameter is an overload of General::Screen_Alignement<br> Align to inside container <br> Format : VERTICAL::HORIZENTAL <br> VERTICAL Values : TOP / DOWN / CENTER<br> HORIZENTAL Values : LEFT / RIGHT / CENTER|
|Ratio|This parameter is an overload of General::Screen_RatioScreen<br> Screen ratio either to FIT or to STRETCH<br> Values : FIT / STRETCH|


## Source and PPA Repository :

[Launchpad](https://launchpad.net/xbillboard)

#### For Ubuntu add xbillboard daily build ppa :
##### Install :

`sudo add-apt-repository ppa:samirkherraz/xbillboard-stable`  
`sudo apt-get update`   
`sudo apt-get install xbillboard`   

##### Run :
`xbillboard-start`

#### For others debian based distros you need to add this line into your sources.list file :

`deb http://ppa.launchpad.net/samirkherraz/xbillboard-stable/ubuntu <code> main`

replace \<code> with ubuntu equivalent of your debian

|Debian|Ubuntu|
|---|---|
|buster|bionic|
|stretch|xenial|
|jessie|trusty|
|wheezy|precise|
 
