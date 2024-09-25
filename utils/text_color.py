import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init(autoreset=True)

# ANSI escape sequences for text colors
COLORS = {
    'black': Fore.BLACK,
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'blue': Fore.BLUE,
    'magenta': Fore.MAGENTA,
    'cyan': Fore.CYAN,
    'white': Fore.WHITE,

    'bright_black': Fore.LIGHTBLACK_EX,
    'bright_red': Fore.LIGHTRED_EX,
    'bright_green': Fore.LIGHTGREEN_EX,
    'bright_yellow': Fore.LIGHTYELLOW_EX,
    'bright_blue': Fore.LIGHTBLUE_EX,
    'bright_magenta': Fore.LIGHTMAGENTA_EX,
    'bright_cyan': Fore.LIGHTCYAN_EX,
    'bright_white': Fore.LIGHTWHITE_EX,
}

BACKGROUNDS = {
    'black': Back.BLACK,
    'red': Back.RED,
    'green': Back.GREEN,
    'yellow': Back.YELLOW,
    'blue': Back.BLUE,
    'magenta': Back.MAGENTA,
    'cyan': Back.CYAN,
    'white': Back.WHITE,

    'bright_black': Back.LIGHTBLACK_EX,
    'bright_red': Back.LIGHTRED_EX,
    'bright_green': Back.LIGHTGREEN_EX,
    'bright_yellow': Back.LIGHTYELLOW_EX,
    'bright_blue': Back.LIGHTBLUE_EX,
    'bright_magenta': Back.LIGHTMAGENTA_EX,
    'bright_cyan': Back.LIGHTCYAN_EX,
    'bright_white': Back.LIGHTWHITE_EX,
}

STYLES = {
    'dim': Style.DIM,
    'normal': Style.NORMAL,
    'bright': Style.BRIGHT,
}

def color_text(text, color=None, background=None, style=None):
    """
    Returns the text string wrapped in ANSI escape sequences to display the specified color.

    :param text: The text to color.
    :param color: The color name as a string (e.g., 'red', 'green').
    :param background: The background color name as a string.
    :param style: The text style as a string (e.g., 'bright', 'dim').
    :return: Colored text string.
    """
    color_code = COLORS.get(color.lower(), '') if color else ''
    bg_code = BACKGROUNDS.get(background.lower(), '') if background else ''
    style_code = STYLES.get(style.lower(), '') if style else ''
    return f"{style_code}{color_code}{bg_code}{text}{Style.RESET_ALL}"

def print_color(text, color=None, background=None, style=None):
    """
    Prints the text in the specified color.

    :param text: The text to print.
    :param color: The color name as a string.
    :param background: The background color name as a string.
    :param style: The text style as a string.
    """
    print(color_text(text, color, background, style))
