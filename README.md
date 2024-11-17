<p align="center">
    <img src="https://user-images.githubusercontent.com/69050895/185436929-c80736b3-07ce-434b-ba96-d753c8e9f83c.png" height="300px" width="575px">
</p>

<div style="font-style: italic; text-align: center;" markdown="1" align="center">

  ![wakatime](https://wakatime.com/badge/user/4cf4132a-4ced-411d-b714-67bdbdc84527/project/ecce3f45-dba9-4e4b-8f78-693c6d237d1c.svg)
  [![PyPI version](https://badge.fury.io/py/chocolate-app.svg)](https://badge.fury.io/py/chocolate-app)
  [![GitHub release](https://img.shields.io/github/release/ChocolateApp/Chocolate?include_prereleases=&sort=semver&color=blue)](https://github.com/ChocolateApp/Chocolate/releases/)
  [![GitHub stars](https://img.shields.io/github/stars/ChocolateApp/Chocolate?style=social&label=Stars&color=blue)](https://github.com/ChocolateApp/Chocolate)
  [![GitHub watchers](https://img.shields.io/github/watchers/ChocolateApp/Chocolate?style=social&label=Watchers&color=blue)](https://github.com/ChocolateApp/Chocolate)
  [![License](https://img.shields.io/badge/License-MIT-blue)](#license)
  [![issues - Chocolate](https://img.shields.io/github/issues/ChocolateApp/Chocolate)](https://github.com/ChocolateApp/Chocolate/issues)

</div>

**Thanks everyone for the support, I'm still working on Chocolate, way less due to my studies, but I'm still here !**<br>
**I'm currently working on the 7.2.0 version, which will include the docker image, for all the GPU/CPU users.**<br>
**I have a lot of ideas for the future, I'm looking at how to make a plugin system, and a watchtogether system, and I'm working on an intro detection system.**<br>

## About The Project
Chocolate is a free and Open Source media manager.<br>
It allows you to manage your media collection and organize it in a way that is easy to use and easy to search.<br>
Pair your popcorn with Chocolate and enjoy your favorite movie!<br>
It's a free software.<br>

<p style="display: inline-flex;
    align-items: center;">
This product uses the TMDB API but is not endorsed or certified by TMDB | <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_1-5bdc75aaebeb75dc7ae79426ddd9be3b2be1e342510f8202baf6bffa71d7f5c4.svg" height="20px"></p><br>

<a href="https://hosted.weblate.org/engage/chocolate/">
  <img src="https://hosted.weblate.org/widget/chocolate/translation/multi-auto.svg"/>
</a>

### Built With

Chocolate is actually made with this technologies:

* <img src="https://ziadoua.github.io/m3-Markdown-Badges/badges/HTML/html1.svg" alt="HTML5" style="display: flex; align-items: center;">
* <img src="https://ziadoua.github.io/m3-Markdown-Badges/badges/CSS/css1.svg" alt="CSS3" style="display: flex; align-items: center;">
* <img src="https://ziadoua.github.io/m3-Markdown-Badges/badges/Javascript/javascript1.svg" alt="Javascript" style="display: flex; align-items: center;">
* <img src="https://ziadoua.github.io/m3-Markdown-Badges/badges/Python/python1.svg" alt="Python" style="display: flex; align-items: center;">
* <img src="https://ziadoua.github.io/m3-Markdown-Badges/badges/Flask/flask1.svg" alt="Flask" style="display: flex; align-items: center;">


<!-- GETTING STARTED -->
## Getting Started

This is what you have to do to get started with Chocolate :

## Prerequisites

### Installation

#### For Windows/Linux/Mac
* Make sure you have at least python 3.10 and pip installed
* Execute ```pip install chocolate_app```
* To run chocolate, simply execute ```python -m chocolate_app``` or ```python3 -m chocolate_app```

#### For QNAP
* Go here: [https://www.myqnap.org/product/chocolate81/](https://www.myqnap.org/product/chocolate81/)
* Enjoy !

#### For Docker
* WIP (Release soon)

### Files organizations

#### For Movies :
* Create a directory
* Put all your movies in (directly the files or in a subfolder)
* Create a new library and select the directory you created with the specific type
* It's done

#### For Shows :
* Create a directory where you will put all your shows
* Choose between two ways to organize your shows :
  * One directory per show, with directories for each season, and files for each episode
  * All files in one directory, for all shows, with a good name that can be analyzed
* Create a new library and select the directory you created with the specific type
* It's done

#### For Games :
* Create a directory
* Create a directory for each consoles
* For each directory put games for this console
* Some consoles need a bios, go to /static/bios/
  * Create a directory named by the console
  * Put in the bios file
* It's done

#### For Books :
* Create a directory
* Put all your books in with the name that you want
* It's done

### List of supported console :
  * Gameboy
  * Gameboy Color
  * Gameboy Advance
  * Nintendo DS
  * Nintendo 64
  * Nintendo Entertainment System
  * Super Nintendo Entertainment System
  * Sega Master System
  * Sega Mega Drive
  * Sega Saturn
  * Sony Playstation 1 (for .cue and .bin you have to .zip all files) (need a bios)

### Start Chocolate

#### For Linux & Windows
* execute 'python3 -m chocolate_app' in your terminal


#### For Docker
/!\ The docker image has some problems, it's not working for now /!\
* Execute :
  * CMD : `docker run -d -v %cd%:/chocolate imprevisible/chocolate`
  * Powershell : `docker run -d -v ${PWD}:/chocolate imprevisible/chocolate`
  * Linux : `docker run -d -v $(pwd):/chocolate imprevisible/chocolate`

### Important Informations
* The port of Chocolate is 8888.

<!-- USAGE EXAMPLES -->
## Usage
![screencapture-localhost-8500-2022-08-18-18_03_30](https://user-images.githubusercontent.com/69050895/185441919-61db8093-8aa7-49d1-aa58-d04520b9a250.png)
![screencapture-localhost-8500-films-2022-08-18-18_04_53](https://user-images.githubusercontent.com/69050895/185442124-ecf72fe9-344f-4836-b21b-597c4c36c1d0.png)



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- TO-DO -->
## TO-DO for Chocolate Server
- [ ] A docker image **URGENT**
- [X] Allow library fusion (for example, if you have two libraries for movies, you can merge them, so only one library will be displayed)
- [X] Create a plugin system
- [ ] Add the mobile ui of the video player
- [ ] Add a watchtogether system
- [ ] Multiple interface
- [ ] Allow custom css
- [ ] Statistics
- [ ] Custom intro
- [ ] Add a system to search for subtitles (By using OpenSubtitles API [here](https://opensubtitles.stoplight.io/docs/opensubtitles-api/b1eb44d4c8502-open-subtitles-api) ) (with the plugin system)
- [ ] Send issues directly from the website
- [ ] Add watched movies, and series to TRAKT (with the plugin system)
- [ ] Add support to trakt (with the plugin system)
- [X] Use the GPU to encode videos if possible
- [ ] Change season with the buttons
- [X] Add logs
- [ ] Design a UI for the path selection instead of a string
- [ ] Use two pages for books on horizontal screen
- [ ] NFO support
- [ ] Allow support of PosgreSQL/MySQL

### Work in progress
- [ ] Detect series intro and skip them
- [ ] Dev a mobile/TV app with chromecasting, and download
- [ ] Add all audio tracks

<!-- CONTACT -->
## Contact

Official Discord Server - [https://discord.gg/qbWdzuPhZ4](https://discord.gg/qbWdzuPhZ4)<br>
Project Link: [https://github.com/ChocolateApp/Chocolate](https://github.com/ChocolateApp/Chocolate)<br>
Impre'visible#2576 - [@romeo_chevrier](https://twitter.com/romeo_chevrier) - impr.visible@gmail.com<br>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

If you like this project, please consider giving me a star ⭐ to support my work and the futures update of this project.
[![stars - Chocolate](https://img.shields.io/github/stars/ChocolateApp/Chocolate?style=social)](https://github.com/ChocolateApp/Chocolate)

This tool was made by Impre-visible, some features needed the help of several volunteers, that I thank, you can contact them on this server : [Dev'Area](https://discord.gg/hTmbFePH)

Original website design from [Mart](https://www.figma.com/@Martbrady) on [figma](https://www.figma.com/community/file/970595453636409922)<br>
A special thanks to Mathias08 who made it possible to release v1 of Chocolate and MONSTA CARDO !! who made the animated logo !

The consoles images are in part from [Jude Coram](https://www.judecoram.com/pixel-art-game-consoles/) the rest are made by me.

This tool was made with ❤ and ☕ by Impre-visible.

<!-- LICENSE -->
## License

<div style="display: flex; align-items: center;">
  <span>This work is licensed under a </span>
  <a href="https://www.gnu.org/licenses/gpl-3.0.html" style="margin-left:5px;display: flex; align-items: center;">
    <img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg" alt="GNU GENERAL PUBLIC LICENSE">
  </a>
</div>
