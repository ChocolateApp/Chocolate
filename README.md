<p align="center">
    <img src="https://user-images.githubusercontent.com/69050895/185436929-c80736b3-07ce-434b-ba96-d753c8e9f83c.png" height="300px" width="575px">
</p>

<div style="font-style: italic; text-align: center;" markdown="1" align="center">

[![wakatime](https://wakatime.com/badge/user/4cf4132a-4ced-411d-b714-67bdbdc84527/project/ecce3f45-dba9-4e4b-8f78-693c6d237d1c.svg)](https://wakatime.com/badge/user/4cf4132a-4ced-411d-b714-67bdbdc84527/project/ecce3f45-dba9-4e4b-8f78-693c6d237d1c)
  [![GitHub release](https://img.shields.io/github/release/Impre-visible/Chocolate?include_prereleases=&sort=semver&color=blue)](https://github.com/Impre-visible/Chocolate/releases/)
  [![GitHub stars](https://img.shields.io/github/stars/Impre-visible/Chocolate?style=social&label=Stars&color=blue)](https://github.com/Impre-visible/Chocolate)
  [![GitHub watchers](https://img.shields.io/github/watchers/Impre-visible/Chocolate?style=social&label=Watchers&color=blue)](https://github.com/Impre-visible/Chocolate)
  [![License](https://img.shields.io/badge/License-MIT-blue)](#license)
  [![issues - Chocolate](https://img.shields.io/github/issues/Impre-visible/Chocolate)](https://github.com/Impre-visible/Chocolate/issues)

</div>

## Note of the 20/11/2022
There's no update from 15 days, don't worry, I'm currently working on the biggest update of Chocolate.<br>
The new update will rewrite a lot of code, increase a lot of features and add a lot of new features.<br>
Thanks for supporting Chocolate, I hope you'll like the new update.<br>

If you want more information about the new update, you can go the the rubric [**To-do list**](#to-do-list)<br>
or you can join the [**Discord server**](https://discord.gg/6m4ZqmNe) and check the #working-on channel.


## About The Project
Chocolate is an Open Source media manager.<br>
It allows you to manage your media collection and organize it in a way that is easy to use and easy to search.<br>
It's a free software.<br>

### Built With

Chocolate is actually made with this technology :

* ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
* ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
* ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
* ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white) 


<!-- GETTING STARTED -->
## Getting Started

This is what you have to do to get started with Chocolate :

## Prerequisites

### Installation

#### For Linux
* Go to the [latest release](https://github.com/Impre-visible/Chocolate/releases/latest)
* Download the latest installer named `install.sh`
* Place it where you want
* Run it
* Enjoy !

#### For Windows
* No installer available actually
* So download the source code and install the dependencies

### Files organizations

#### For Movies :
* Create a directory
* Put all your movies in with a proper name, like "Batman Begins.mkv" instead of "Batman.Begins.H264.AAC.XxMOVIESxX.mkv"
* Create a new library and select the directory you created with the specific type
* It's done

#### For Shows :
* Create a directory
* Create a directory for each shows
* In this directory create directory for each seasons, if possible named them like that : "S1", "S2", "S26"
* In this seasons directory put all épisodes files, and if possible named them like that : "E1.mkv", "E2.mp4", "E56.avi"
* Precisions : Chocolate will ask you to rename files and directory if it don't understand, you can agree or disagree is proposition
```
📂 Shows
 ├── 📂 The Office           # Perfect
 │    ├── 📂 S1
 │    │    ├── E1.mkv
 │    │    ├── E2.mkv
 │    │    └── E3.mkv
 │    │
 │    └── 📂 S2
 │         └── E1.mkv
 │
 ├── 📂 The Simpsons        # Don't do that please
 │    └── 📂 Season 1
 │         ├── The.Simpsons.EP.One.mkv
 │         ├── The.Simpsons.EP.Two.mkv
 │         └── The.Simpsons.EP.Three.mkv

```
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

#### For Linux
* execute 'chocolate' in your terminal

#### For Windows
* Execute app.py

### Important Informations
* At the first launch, Chocolate will be very fast if you don't renseign the path in config.ini.
* If you don't change all the paths. Go to the settings, and fill in the forms.
* You can change a lot of settings directly on the website.
* The default port is 8500.

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


## TO-DO for Chocolate Server {#to-do-list}
- [ ] Use Flask-PWA
- [ ] Add all audio tracks
- [ ] Add the mobile ui of the video player
- [ ] Dev a mobile/TV app with chromecasting, and download
- [ ] Edit movie metadata directly on the website
- [ ] Add Books, PDF, Epub
- [ ] Add Musics
- [ ] Add TV with M3U/M3U8 playlist
- [ ] Add a watchtogether system
- [ ] Translate in multiple languages
- [ ] Multiple interface
- [ ] Statistics
- [ ] Custom intro
- [ ] Add a system to search for subtitles
- [ ] Send issues directly from the website
- [ ] Order by title, year, release date, note, duration, done, watching, date of add, date of last view
- [ ] Add watched movies, and series to the watchlist of TMDB

### Work in progress

- [ ] Detect series intro and skip them
- [ ] Create a systeme of library
- [ ] Increase the search system
- [ ] Upgrade the responsive

### Tasks Done
- [X] Increase the boot speed
- [X] Added the Consoles on the main page
- [X] Replace JSON by a DB
- [X] Converted all images to webp
- [X] Create a local account system for child and members of the family/friends
- [X] Patch few bugs like :
  - [X] Actors page
  - [X] Popup of the first and random show
- [X] Add Games
- [X] Add shows, tv programs
- [X] Enable or not RPC for Discord
- [X] Add multiple quality vidéos
- [X] Vue systeme by account instead of computer
- [X] Add the loading everywhere


<!-- CONTACT -->
## Contact

Official Discord Server - [https://discord.gg/6m4ZqmNe](https://discord.gg/6m4ZqmNe)<br>
Project Link: [https://github.com/ChocolateApp/Chocolate](https://github.com/ChocolateApp/Chocolate)<br>
Impre'visible#2576 - [@romeo_chevrier](https://twitter.com/romeo_chevrier) - impr.visible@gmail.com<br>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

If you like this project, please consider giving me a star ⭐ to support my work and the futures update of this project. 
[![stars - Chocolate](https://img.shields.io/github/stars/Impre-visible/Chocolate?style=social)](https://github.com/Impre-visible/Chocolate)

This tool was made by Impre-visible, some features needed the help of several volunteers, that I thank, you can contact them on this server : [Dev'Area](https://discord.gg/hTmbFePH)

Original website design from [Mart](https://www.figma.com/@Martbrady) on [figma](https://www.figma.com/community/file/970595453636409922)<br>
A special thanks to Mathias08 who made it possible to release v1 of Chocolate and MONSTA CARDO !! who made the animated logo !

The consoles images are in part from [Jude Coram](https://www.judecoram.com/pixel-art-game-consoles/) the rest are made by me.

This tool was made with ❤ and ☕ by Impre-visible.

<!-- LICENSE -->
## License

Shield: [![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
