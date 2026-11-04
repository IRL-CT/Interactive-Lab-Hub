# Server Configuration Files

This folder contains systemd service files for running the Lab 6 servers on `farlab.infosci.cornell.edu`.

**Students do not need these files** - they are only for server deployment.

## Services

### pixel_grid.service
Runs the collaborative pixel grid web server on port 5000.

**Install:**
```bash
sudo cp pixel_grid.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pixel_grid.service
sudo systemctl start pixel_grid.service
```

### mqtt_viewer.service
Runs the MQTT message viewer debugging tool on port 5001.

**Install:**
```bash
sudo cp mqtt_viewer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mqtt_viewer.service
sudo systemctl start mqtt_viewer.service
```

## Management Commands

```bash
# Check status
sudo systemctl status pixel_grid.service
sudo systemctl status mqtt_viewer.service

# View logs
sudo journalctl -u pixel_grid.service -n 50
sudo journalctl -u mqtt_viewer.service -n 50

# Restart
sudo systemctl restart pixel_grid.service
sudo systemctl restart mqtt_viewer.service

# Stop
sudo systemctl stop pixel_grid.service
sudo systemctl stop mqtt_viewer.service
```
