# Useful Home Assistant Repositories

This document contains a curated list of useful Home Assistant Add-on repositories that can be added to your instance.

### 1. [Thomas Mauerer's Add-ons](https://github.com/thomasmauerer/hassio-addons)
**Description:** A highly useful collection of add-ons focused on Home Assistant maintenance.
**Key Add-ons:**
- **Samba Backup:** Automatically create system snapshots/backups and store them safely on a remote Samba (SMB) share.

---

### 2. [Unofficial Home Assistant Apps](https://github.com/homeassistant-apps/repository)
**Description:** A repository dedicated to providing tunneling and networking apps/add-ons for your installation.
**Key Add-ons:**
- **Cloudflared:** Easily create a Cloudflare Tunnel to securely connect to your Home Assistant remotely without needing to open any ports or mess with port forwarding on your router.
- **Newt:** Tunneling client to connect Home Assistant to Pangolin.

---

### 3. [wmbusmeters Add-on](https://github.com/wmbusmeters/wmbusmeters-ha-addon)
**Description:** The official Home Assistant add-on repository for wmbusmeters.
**Key Add-ons:**
- **wmbusmeters:** Allows you to acquire utility meter readings (water, gas, heat, electricity) entirely locally without relying on the vendor's cloud bridge. It works as long as the meters support C1, T1, or S1 telegrams using the wireless m-bus protocol (WMBUS).

---

### 4. [mKeRix's Community Repository](https://github.com/mKeRix/hassio-repo)
**Description:** A small but specialized community repository for Hass.io add-ons.
**Key Add-ons:**
- **room-assistant:** A companion add-on that runs a server for tracking presence, people, and devices on a granular, per-room basis (frequently utilizing Bluetooth Low Energy).

---

### 5. [Alexbelgium's Add-ons](https://github.com/alexbelgium/hassio-addons)
**Description:** A massive, actively-maintained collection of over 70 popular software services wrapped beautifully into Home Assistant add-ons.
**Key Add-ons Included:**
- **Smart Home & Media:** Plex, Jellyfin, Emby, Navidrome.
- **Homelab & Self-Hosting:** Nextcloud, Bitwarden, Immich, Gitea, Portainer, Filebrowser.
- **Arr-Stack:** Sonarr, Radarr, Lidarr, Readarr, Prowlarr, Bazarr, qBittorrent.
- **Misc:** Firefly III, FlareSolverr, Guacamole, Baikal.

---

### 6. [Stanford Genie (Reference)](https://genie.stanford.edu)
**Description:** *(Deprecated / Historic)* The Genie virtual assistant project (formerly known as Almond) developed by Stanford University's Open Virtual Assistant Lab (OVAL).
**Note on HA Compatibility:** This privacy-focused virtual assistant integration was officially removed and is **no longer supported** as a Home Assistant add-on as of 2023. The Stanford lab has shifted its focus. For local smart home voice control today, it is highly recommended to explore Home Assistant's native built-in **Assist** platform (Wake Word, Piper, and Whisper).
