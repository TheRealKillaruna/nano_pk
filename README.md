# nano_pk
Home Assistant integration of Hargassner Nano-PK pellet heating systems.

This is a custom component to integrate Hargassner heatings with Touch Tronic (touch screen control) into Home Assistant.
It will add a number of new sensors to your HA that display the current state of the heating.
All you need is a connection from your Hargassner heating directly from the Touch Tronic to your local LAN, the internet gateway is not required.
The nano_pk component does not allow remote control of your heating.

I have developed and tested it on a Nano-PK model, but chances are high it will work on other Hargassner models as well.
According to user reports, it is also compatible with Rennergy Mini PK heating models.
Read on how to try this and let me know if it works!

### Quick setup guide ###

1. Create a folder `custom_components` in your Home Assistant `config` folder (if not yet done).
2. Copy all code from this repository to `config/custom_components/nano_pk`.
3. Add a section like this to your configuration.yaml:
```
nano_pk:
  host: 192.168.0.10
  msgformat : NANO_V14L
  devicename: Nano-PK
  parameters: STANDARD
  language: DE
```
4. Restart HA.

### Supported parameters ###
- host [required]: IP of your heating. After connecting the heating with your local network, the touch screen will show this.
- msgformat [required]: All Hargassner heatings with touch screen send out their messages in a different format, and this changes with different firmware versions. Out of the box, `NANO_V14K`, `NANO_V14L`, `NANO_V14M`, `NANO_V14N`, `NANO_V14N2` and `NANO_V14O3` are supported, which are recent firmwares for the Nano-PK (you can see the firmware version on your touch screen).
- devicename [optional]: The name under which all heating sensors will appear in HA. By default, this is `Hargassner`.
- parameters [optional]: `STANDARD` is, you guessed it, the standard and imports the most important parameters from the heating as sensors. `FULL` will give you everything that is sent out.
- language [optional]: Configures the output of the heating state sensor. `EN` is the default, `DE` is also available.


### How to use with other Hargassner models or different firmware versions ###
Apart from the provided templates for `msgformat` (see above), this configuration parameter also allows custom message formats. Follow these steps:
1. To get the correct message format for your heating, enable SD logging on the touch screen and insert a card for a short time (a couple of seconds should be enough). 
2. Check the card on your computer: you should find a file `DAQ00000.DAQ` or similar somewhere.
3. Open this file in a text editor and search for an XML section `<DAQPRJ> ... </DAQPRJ>` right at the beginning.
4. Copy the entire section and place it using quotes in your `configuration.yaml`, so that you have something like this: `msgformat="<DAQPRJ> ... </DAQPRJ>"`
5. For different heating models, set `parameters` to `FULL` to check out which parameters are sent.


### Acknowledgements ###
[This code](https://github.com/Jahislove/Hargassner) by @Jahislove was very helpful to understand the messages sent by the heating - thank you!


### Feedback ###
You can leave feedback for this custom component in the [corresponding thread](https://community.home-assistant.io/t/hargassner-heating-integration/288568) at the Home Assistant community forum.
