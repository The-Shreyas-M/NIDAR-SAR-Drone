# Deploying `pi/` to the drone

`pi/` mirrors what's live on the Pi. Deploy from the repo root over SSH
(`user@rpi`). Never edit the Pi copies by hand — change the repo, redeploy.

```bash
# copy up (filenames = install names, no extensions)
scp pi/bin/* user@rpi:/tmp/
scp pi/systemd/* user@rpi:/tmp/
scp pi/networkmanager/dispatcher.d/90-nidar-ap user@rpi:/tmp/

ssh user@rpi
echo <sudo-pw> | sudo -S install -m 0755 /tmp/nidar-portal /usr/local/bin/nidar-portal
echo <sudo-pw> | sudo -S install -m 0755 /tmp/nidar-wifi-fallback /usr/local/bin/nidar-wifi-fallback
echo <sudo-pw> | sudo -S install -m 0755 /tmp/nidar-wifi-watch /usr/local/bin/nidar-wifi-watch
echo <sudo-pw> | sudo -S install -m 0755 /tmp/nidar-ap /usr/local/bin/nidar-ap
echo <sudo-pw> | sudo -S install -o root -g root -m 0755 /tmp/90-nidar-ap /etc/NetworkManager/dispatcher.d/90-nidar-ap
echo <sudo-pw> | sudo -S install -m 0644 /tmp/nidar-wifi-fallback.service /etc/systemd/system/nidar-wifi-fallback.service
echo <sudo-pw> | sudo -S install -m 0644 /tmp/nidar-wifi-watch.service /etc/systemd/system/nidar-wifi-watch.service
echo <sudo-pw> | sudo -S install -m 0644 /tmp/nidar-portal.service /etc/systemd/system/nidar-portal.service
echo <sudo-pw> | sudo -S systemctl daemon-reload
echo <sudo-pw> | sudo -S systemctl enable --now nidar-wifi-fallback.service nidar-wifi-watch.service nidar-portal.service
```

Verify:

```bash
bash -n /usr/local/bin/nidar-wifi-fallback && bash -n /usr/local/bin/nidar-ap \
  && sh -n /etc/NetworkManager/dispatcher.d/90-nidar-ap \
  && python3 -m py_compile /usr/local/bin/nidar-wifi-watch /usr/local/bin/nidar-portal
sudo systemctl is-active nidar-wifi-fallback.service nidar-wifi-watch.service nidar-portal.service
curl -s http://127.0.0.1/api/status | head -c 300; echo
# real proof, not "service started":
sudo reboot   # then: AP must reappear in seconds, http://192.168.50.1/ serves
```

Drift check (repo is source of truth — Pi must match):

```bash
for f in nidar-portal nidar-wifi-fallback nidar-wifi-watch nidar-ap; do
  diff <(cat pi/bin/$f) <(ssh user@rpi "cat /usr/local/bin/$f") && echo "$f OK";
done
```
