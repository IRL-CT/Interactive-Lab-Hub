"""Optional 1.14-inch Mini PiTFT; reference pins/orientation retained."""
import logging


class PetDisplay:
    def __init__(self, role, disabled=False):
        self.role, self.last, self.disp = role, None, None
        self.pins = []
        if disabled:
            return
        try:
            import board
            import digitalio
            from PIL import Image, ImageDraw
            from adafruit_rgb_display.st7789 import ST7789
            self.Image, self.ImageDraw = Image, ImageDraw
            cs = digitalio.DigitalInOut(board.D5)
            self.pins.append(cs)
            dc = digitalio.DigitalInOut(board.D25)
            self.pins.append(dc)
            light = digitalio.DigitalInOut(board.D22)
            self.pins.append(light)
            light.switch_to_output(value=True)
            self.disp = ST7789(board.SPI(), cs=cs, dc=dc, rst=None, baudrate=64000000,
                               width=135, height=240, x_offset=53, y_offset=40, rotation=90)
        except Exception as exc:
            logging.warning('Display unavailable; continuing headless: %s', exc)
            self.close()

    def show(self, snapshot, feedback=''):
        if not self.disp:
            return
        state = snapshot['state']
        text = f'LONGAN   |   {self.role.upper()}\n'
        if not snapshot['connected']:
            text += 'MQTT offline\n'
        elif not snapshot['fresh']:
            text += 'Waiting for engine...\n'
        if state:
            text += ('TOGETHER, WE DID IT!\n' if state['status'] == 'won' else state['mood'].replace('_', ' ').upper() + '\n')
            text += '\n'.join(f'{k.title():12} {state[k]:3}' for k in ('fullness', 'happiness', 'energy'))
        text += '\n' + feedback
        if text == self.last:
            return
        try:
            img = self.Image.new('RGB', (240, 135), '#182d2c')
            self.ImageDraw.Draw(img).multiline_text((10, 8), text, fill='#f3e9cb', spacing=6)
            self.disp.image(img)
            self.last = text
        except Exception as exc:
            logging.warning('Display failed; headless: %s', exc)
            self.close()

    def close(self):
        self.disp = None
        for pin in self.pins:
            try:
                pin.deinit()
            except Exception:
                pass
        self.pins.clear()
