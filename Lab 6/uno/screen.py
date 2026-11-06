"""Draws the game for the 240x135 screen. Only needs Pillow, so it can be previewed anywhere."""

from PIL import Image, ImageDraw, ImageFont

from game import card_color, card_value

WIDTH, HEIGHT = 240, 135
FILLS = {'R': (214, 40, 40), 'Y': (247, 200, 30), 'G': (40, 160, 70), 'B': (30, 100, 210), None: (35, 35, 35)}
COLOR_NAMES = {'R': 'RED', 'Y': 'YELLOW', 'G': 'GREEN', 'B': 'BLUE'}
LABELS = {'S': 'SKIP', 'R': 'REV', 'D': '+2', 'W': 'WILD', 'W4': '+4'}
BG = (12, 12, 16)
WHITE = (255, 255, 255)
DIM = (150, 150, 150)
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def ink_on(color):
    return (0, 0, 0) if color == 'Y' else WHITE


def centered(draw, box, text, size, fill):
    x0, y0, x1, y1 = box
    # Shrink long text until it fits in the box
    while size > 8 and draw.textlength(text, font=font(size)) > x1 - x0 - 4:
        size -= 1
    draw.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font(size), fill=fill, anchor='mm')


def draw_card(draw, box, card, active_color=None, dim=False):
    """active_color shows which color a wild on the pile was set to"""
    color = card_color(card) or active_color
    fill = FILLS[color]
    if dim:
        fill = tuple(c // 3 for c in fill)
    draw.rounded_rectangle(box, radius=7, fill=fill, outline=WHITE, width=2)
    value = card_value(card)
    ink = DIM if dim else ink_on(color)
    centered(draw, box, LABELS.get(value, value), 30, ink)


def draw_full(fill, title, subtitle='', ink=WHITE, detail=''):
    image = Image.new('RGB', (WIDTH, HEIGHT), fill)
    draw = ImageDraw.Draw(image)
    centered(draw, (0, 15, WIDTH, 75), title, 38, ink)
    if subtitle:
        centered(draw, (0, 75, WIDTH, 100), subtitle, 18, ink)
    if detail:
        centered(draw, (0, 102, WIDTH, 125), detail, 14, ink)
    return image


def render(view):
    """view is the plain dict built by Player.view()"""
    mode = view['mode']
    if mode == 'connecting':
        return draw_full(BG, 'UNO', view.get('message', 'Finding the referee...'), detail=view['name'])
    if mode == 'lobby':
        return draw_full(BG, 'UNO', f"{view['joined']}/{view['needed']} players here", detail=view['name'])
    if mode == 'over':
        won = view['winner'] == view['name']
        return draw_full(FILLS['G'] if won else BG, 'YOU WIN!' if won else f"{view['winner']} wins",
                         'Good round', detail=view['scores'])
    if mode == 'uno':
        owner = view['uno_player']
        title = 'SAY UNO!' if view['mine'] else f'CATCH {owner}!'
        subtitle = 'Cover your sensor!' if view['mine'] else 'Cover your sensor first!'
        detail = 'Sent!' if view['called'] else f"{view['remaining']} s"
        return draw_full(FILLS['Y'], title, subtitle, ink=(0, 0, 0), detail=detail)
    if mode == 'pick':
        color = view['pick_color']
        return draw_full(FILLS[color], COLOR_NAMES[color], 'Hold a color to the sensor',
                         ink=ink_on(color), detail='A: change   B: choose')

    image = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Top bar and frame: you should be able to tell it's your turn from across the table
    mine = view['my_turn']
    bar = (40, 160, 70) if mine else (45, 45, 55)
    draw.rectangle((0, 0, WIDTH, 21), fill=bar)
    arrow = '>' if view['direction'] == 1 else '<'
    centered(draw, (0, 0, WIDTH, 21), 'YOUR TURN' if mine else f"{arrow} {view['current']}'s turn", 15, WHITE)
    if mine:
        draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), outline=bar, width=3)

    # Pile on the left, the card you're pointing at on the right
    draw_card(draw, (10, 26, 72, 106), view['top'], view['color'])
    if view['cards']:
        draw_card(draw, (90, 26, 152, 106), view['selected'], dim=not view['selected_legal'])
        centered(draw, (154, 26, 236, 44), f"{view['index'] + 1} of {len(view['cards'])}", 13, WHITE)

    # Everyone's card counts, in table order
    y = 47
    for player, count in view['counts']:
        fill = WHITE if player == view['current'] else DIM
        name = 'you' if player == view['name'] else player[:6]
        draw.text((158, y), f'{name}: {count}', font=font(12), fill=fill)
        y += 15

    # One chip per card, so you can see your whole hand
    chip = min(14, (WIDTH - 20) // max(1, len(view['cards'])))
    for i, card in enumerate(view['cards'][:40]):
        x = 10 + i * chip
        draw.rectangle((x, 111, x + chip - 2, 119), fill=FILLS[card_color(card)],
                       outline=WHITE if i == view['index'] else None)

    bottom = view.get('message') or view['last']
    draw.text((WIDTH // 2, 127), bottom, font=font(11), fill=WHITE, anchor='mm')
    return image
