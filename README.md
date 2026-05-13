# nano_pk

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for Hargassner Nano-PK pellet heating systems.

This custom component integrates Hargassner heaters equipped with Touch Tronic (touch-screen control) into Home Assistant.
It adds sensors that display the current state of the heater.
All you need is a direct LAN connection from the Touch Tronic to your local network — the internet gateway is not required.
The nano_pk integration does **not** allow remote control of the heater.

I developed and tested it on a Nano-PK model, but it is likely to work on other Hargassner models as well.
According to user reports it is also compatible with Rennergy Mini PK heaters.
Read on to find out how to try it and let me know if it works!

---

## Installation

### HACS (recommended)

1. Open **HACS** in your Home Assistant UI.
2. Go to **Integrations** → click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/TheRealKillaruna/nano_pk` as an **Integration** repository.
4. Click **Download** on the newly listed **Hargassner Nano-PK** integration.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **Hargassner Nano-PK**.
7. Enter your heater's IP address, firmware type and preferences in the configuration flow.

### Manual install

1. Create a folder `custom_components` in your Home Assistant `config` folder (if it does not yet exist).
2. Copy everything from `custom_components/nano_pk` in this repository into `config/custom_components/nano_pk`.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for **Hargassner Nano-PK**.

### Legacy YAML (deprecated)

If you prefer the old YAML-based setup, add this to your `configuration.yaml` and restart Home Assistant:

```yaml
nano_pk:
  host: 192.168.0.10
  msgformat: NANO_V14L
  devicename: Nano-PK
  parameters: STANDARD
  language: DE
```

> **Note:** YAML configuration continues to work but is deprecated. The configuration flow allows you to change settings without editing YAML and is the recommended approach.

---

## Configuration parameters

The UI configuration flow (and the legacy YAML) support the following options:

| Parameter | Required | Default | Description |
|---|---|---|---|
| `host` | **yes** | — | IP address of your heater. After connecting the heater to the local network the touch screen will display this. |
| `msgformat` | **yes** | — | Firmware / message format. All Hargassner heaters with touch screen use different message formats depending on firmware version. Built-in templates are `NANO_V14K`, `NANO_V14L`, `NANO_V14M`, `NANO_V14N`, `NANO_V14N2` and `NANO_V14O3` (check the exact version on your touch screen). You can also paste a custom `<DAQPRJ>…</DAQPRJ>` XML string. |
| `devicename` | no | `Hargassner` | Display name used for the heater's device card and entity names in Home Assistant. |
| `parameters` | no | `STANDARD` | `STANDARD` exposes the most important sensors. `FULL` creates a sensor for every parameter sent by the heater. |
| `language` | no | `EN` | Language for the boiler-state sensor text. Supported: `EN`, `DE`, `FR`. |
| `unique_id` | no | `1` | Unique identifier used to distinguish multiple heaters. Only change if you run more than one heater. |

---

## Using custom message formats (other models or firmware)

If your model or firmware is not covered by the built-in templates, follow these steps:

1. Enable **SD logging** on the touch screen and insert an SD card for a few seconds.
2. Check the card on your computer: look for a file named `DAQ00000.DAQ` (or similar).
3. Open the file in a text editor and copy the XML section `<DAQPRJ>…</DAQPRJ>` at the very beginning.
4. Paste the entire section, including quotation marks, into the **Message format** field of the configuration flow (or into `configuration.yaml` as `msgformat: "<DAQPRJ>…</DAQPRJ>"`).
5. Use `FULL` parameters during the first run to see which channels are available.

---

## Acknowledgements

[This code](https://github.com/Jahislove/Hargassner) by @Jahislove was very helpful for understanding the messages sent by the heater — thank you!

---

## Feedback

You can leave feedback for this custom component in the [corresponding thread](https://community.home-assistant.io/t/hargassner-heating-integration/288568) at the Home Assistant community forum.
