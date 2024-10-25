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
2. Copy all code from `custom_components/nano_pk` of this repository to `config/custom_components/nano_pk`.
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
- msgformat [required]: All Hargassner heatings with touch screen send out their messages in a different format, and this changes with different firmware versions. Out of the box, `NANO_V14K`, `NANO_V14L`, `NANO_V14M`, `NANO_V14N`, `NANO_V14N2` and `NANO_V14O3` are supported (you can see the firmware version on your touch screen). Since newer firmware there are often very indivdual settings, so that it is recommented to always use the SD-Card-system (see below)
- devicename [optional]: The name under which all heating sensors will appear in HA. By default, this is `Hargassner`.
- parameters [optional]: `STANDARD` is, you guessed it, the standard and imports the most important parameters from the heating as sensors. `FULL` will give you everything that is sent out.
- language [optional]: Configures the output of the heating state sensor. `EN` is the default, `DE` is also available.
- In the hargassner.py you can set two parameters related to how the reconnection system works. Fin "class HargassnerBridge(Entity):"      
```
        # reconnect setting:
        self.retry_attempts = 0
        self.max_retries = 5
        #(default settings: 5 (five retries to establish a connection, exponential pause between unsuccessful retries 1.try=2sec; 2.try=4sec; 3.try=8sec; 4.try=16sec; 5. try=32sec)
```
### SD-Card / How to use with other Hargassner models or different firmware versions ###
Apart from the provided templates for `msgformat` (see above), this configuration parameter also allows custom message formats. Follow these steps:
1. To get the correct message format for your heating, enable SD logging on the touch screen and insert a card for a short time (a couple of seconds should be enough). 
2. Check the card on your computer: you should find a file `DAQ00000.DAQ` or similar somewhere.
3. Open this file in a text editor and search for an XML section `<DAQPRJ> ... </DAQPRJ>` right at the beginning.
4. Copy the entire section and place it using quotes in your `configuration.yaml`, so that you have something like this: `msgformat="<DAQPRJ> ... </DAQPRJ>"`
5. For different heating models, set `parameters` to `FULL` to check out which parameters are sent.
6. if its not working out of the box:
   - log into the logs of HA
   - set up a input_boolean.length_check_enabled in HA an disable the lengthcheck temorary to fix this on your own (be aware: not all sensors must be correct!), set up in configuration.yaml:
```
  input_boolean:
   length_check_enabled:
     name: Hargassner Check Message Length
     initial: true
     icon: mdi:heating-coil
```

## Disable automatic update: ##
1. Register your heater inside the hargassner-app / website
2. Log into the app (or direktly to the website and login there)
3. burger-menu --> click "Web-Version" (if asked, login there)
4. click top right -->"info"-button
5. click "Settings"
6. disable automatic update (read the warning and choose like you want)
done
btw: Its not possibe (at least at the moment), to disable automatic updates inside the app

### Acknowledgements ###
[This code](https://github.com/Jahislove/Hargassner) by @Jahislove was very helpful to understand the messages sent by the heating - thank you!
[The original code](https://github.com/TheRealKillaruna/nano_pk) by @TheRealKillaruna is here forked for a few changes - thank you for your work!
