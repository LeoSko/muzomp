# MUZOMP
MUZOMP stands for MUZic Optimized MultiProcessing.
This project is focused on fast parallel music processing via django-based web-service with the ability to determine similar to each other tracks by extracting characteristics.
## Get started
1. Open project in PyCharm by selecting muzomp folder as project folder;
2. Open requirements.txt in muzomp folder inside IDE and follow installation of additional packages;
3. Select muzomp as current target;
4. Press debug/start.
## Requirements
Versions below may be downgraded, but only for experimental purposes and will not be supported by maintainers.
* Python >= 3.6
* Django >= 2.0
* Librosa >= 0.6
* For librosa, FFMPEG defined in PATH variable for correct audio decoding (or any other way to decode, look in [librosa repo](https://github.com/librosa/librosa/issues/219))
* Celery >= 4.0
* Redis >= 4.0
* Erlang >= 9.2
* Other stuff from requirements.txt
## Authors
St. Petersburg Electrotechnical University "LETI" - Leonid Skorospelov, Andrew Chulanov
