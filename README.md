<p align="center">
    <img src="https://user-images.githubusercontent.com/69050895/185436929-c80736b3-07ce-434b-ba96-d753c8e9f83c.png" height="300px" width="575px">
</p>

<div style="font-style: italic; text-align: center;" markdown="1" align="center">

  ![wakatime](https://wakatime.com/badge/user/4cf4132a-4ced-411d-b714-67bdbdc84527/project/ecce3f45-dba9-4e4b-8f78-693c6d237d1c.svg)
  [![GitHub release](https://img.shields.io/github/release/ChocolateApp/Chocolate?include_prereleases=&sort=semver&color=blue)](https://github.com/ChocolateApp/Chocolate/releases/)
  [![GitHub stars](https://img.shields.io/github/stars/ChocolateApp/Chocolate?style=social&label=Stars&color=blue)](https://github.com/ChocolateApp/Chocolate)
  [![GitHub watchers](https://img.shields.io/github/watchers/ChocolateApp/Chocolate?style=social&label=Watchers&color=blue)](https://github.com/ChocolateApp/Chocolate)
  [![License](https://img.shields.io/badge/License-MIT-blue)](#license)
  [![issues - Chocolate](https://img.shields.io/github/issues/ChocolateApp/Chocolate)](https://github.com/ChocolateApp/Chocolate/issues)

</div>

## About The Project
Chocolate is a free and Open Source media manager.<br>
It allows you to manage your media collection and organize it in a way that is easy to use and easy to search.<br>
Pair your popcorn with Chocolate and enjoy your favorite movie!<br>
It's a free software.<br>
<p style="display: inline-flex;
    align-items: center;">
This product uses the TMDB API but is not endorsed or certified by TMDB | <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_1-5bdc75aaebeb75dc7ae79426ddd9be3b2be1e342510f8202baf6bffa71d7f5c4.svg" height="20px"></p><br>

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

#### For Linux
* Go to the [latest release](https://github.com/ChocolateApp/Chocolate/releases/latest)
* Download the latest installer named `install.sh`
* Place it where you want
* Run it
* Enjoy !

#### For Windows
No installer available, either:
* [Use Docker]( https://github.com/ChocolateApp/Chocolate#for-docker)
* Install manually
    * So download the source code and install the dependencies (requirements.txt, ffmpeg and winrar (only for cbr files so books))
    * For ffmpeg and winrar, you have to add them to your PATH

#### For QNAP
* Go here: [https://www.myqnap.org/product/chocolate81/](https://www.myqnap.org/product/chocolate81/)
* Enjoy !

#### For Docker
* Execute `docker pull imprevisible/chocolate`
* Enjoy !

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

#### For Linux
* execute 'chocolate' in your terminal

#### For Windows
* Execute app.py

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


## TO-DO for Chocolate Server
- [ ] A docker image **URGENT**
- [ ] Create a plugin system
- [ ] Add the mobile ui of the video player
- [ ] Add Musics
- [ ] Add a watchtogether system
- [ ] Translate in multiple languages
- [ ] Multiple interface
- [ ] Allow custom css
- [ ] Statistics
- [ ] Custom intro
- [ ] Add a system to search for subtitles (By using OpenSubtitles API [here](https://opensubtitles.stoplight.io/docs/opensubtitles-api/b1eb44d4c8502-open-subtitles-api) )
- [ ] Send issues directly from the website
- [ ] Add watched movies, and series to TRAKT
- [ ] Add support to trakt
- [ ] Use the GPU to encode videos if possible
- [ ] Change season with the buttons
- [ ] Add logs
- [ ] Use arrow keys to change books pages
- [ ] Design a UI for the path selection instead of a string
- [ ] Use two pages for books on horizontal screen
- [ ] Package on chocolatey
- [ ] NFO support
- [ ] Allow support of PosgreSQL/MySQL

### Work in progress
- [ ] Detect series intro and skip them
- [ ] Dev a mobile/TV app with chromecasting, and download
- [ ] Add all audio tracks
- [ ] Translate the rescan buttons

<!--LANGUAGES TO TRANSLATE -->
## Languages to translate

- [X] AF: Afrikaans
- [X] SQ: Albanian
- [X] AM: Amharic
- [X] AR: Arabic
- [X] HY: Armenian
- [X] AZ: Azerbaijani
- [X] EU: Basque
- [X] BE: Belarusian
- [X] BN: Bengali
- [X] BS: Bosnian
- [X] BG: Bulgarian
- [X] CA: Catalan
- [X] NY: Chichewa
- [X] CO: Corsican
- [X] HR: Croatian
- [X] CS: Czech
- [X] DA: Danish
- [X] NL: Dutch
- [X] EN: English
- [X] EO: Esperanto
- [X] ET: Estonian
- [X] FI: Finnish
- [X] FR: French
- [ ] FY: Frisian
- [ ] GL: Galician
- [ ] KA: Georgian
- [X] DE: German
- [ ] EL: Greek
- [ ] GU: Gujarati
- [ ] HT: Haitian Creole
- [ ] HA: Hausa
- [ ] HE: Hebrew
- [ ] HI: Hindi
- [ ] HU: Hungarian
- [ ] IS: Icelandic
- [ ] IG: Igbo
- [ ] ID: Indonesian
- [ ] GA: Irish
- [X] IT: Italian
- [ ] JA: Japanese
- [ ] JV: Javanese
- [ ] KN: Kannada
- [ ] KK: Kazakh
- [ ] KM: Khmer
- [ ] KO: Korean
- [ ] KU: Kurdish (Kurmanji)
- [ ] LO: Lao
- [ ] LA: Latin
- [ ] LV: Latvian
- [ ] LT: Lithuanian
- [ ] LB: Luxembourgish
- [ ] MK: Macedonian
- [ ] MG: Malagasy
- [ ] MS: Malay
- [ ] ML: Malayalam
- [ ] MT: Maltese
- [X] ZH: Mandarin
- [ ] MI: Maori
- [ ] MR: Marathi
- [ ] MN: Mongolian
- [ ] NE: Nepali
- [ ] NO: Norwegian
- [ ] PS: Pashto
- [ ] FA: Persian
- [ ] PL: Polish
- [ ] PT: Portuguese
- [ ] PA: Punjabi
- [ ] RO: Romanian
- [ ] RU: Russian
- [ ] SM: Samoan
- [ ] GD: Scots Gaelic
- [ ] SR: Serbian
- [ ] SN: Shona
- [ ] SD: Sindhi
- [ ] SK: Slovak
- [ ] SL: Slovenian
- [ ] SO: Somali
- [X] ES: Spanish
- [ ] SU: Sundanese
- [ ] SW: Swahili
- [ ] SV: Swedish
- [ ] TG: Tajik
- [ ] TA: Tamil
- [ ] TT: Tatar
- [ ] TE: Telugu
- [ ] TH: Thai
- [ ] TR: Turkish
- [ ] TK: Turkmen
- [ ] UK: Ukrainian
- [ ] UR: Urdu
- [ ] UZ: Uzbek
- [ ] VI: Vietnamese
- [ ] CY: Welsh
- [ ] XH: Xhosa
- [ ] YI: Yiddish
- [ ] YO: Yoruba
- [ ] ZU: Zuluv

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
