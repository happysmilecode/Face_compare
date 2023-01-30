import os
from PIL import (Image,
                 ImageFont,
                 ImageDraw)


# by Daniel Yoshida
default_font_size = 10
text = 'Python In Office ©'
# text_width, text_height = ImageFont.truetype(r'C:\Windows\Fonts\ALGER.TTF').getsize(text)
text_width, text_height = (50, 50)
folder_path = r'C:\images'

for f in os.listdir(folder_path):
    img = Image.open(rf'{folder_path}\{f}')
    img_width, img_height = img.size
    scaler = img_width/2/text_width

    scale_text_font = int(default_font_size * scaler)
    scale_text_width = int(scaler * text_width)
    scale_text_height = int(scaler * text_height)

    # font = ImageFont.truetype(r'C:\Windows\Fonts\ALGER.TTF', size=scale_text_font)

    draw = ImageDraw.Draw(img)
    start_x = img_width - scale_text_width - 20
    start_y = img_height - scale_text_height - 20
    # draw.text((start_x,start_y), text = text, font = font, fill = (0,0,0))
    draw.text((start_x, start_y), text=text, fill=(0, 0, 0))
    file_name = f.split('.')[0] + '_w_text.jpg'
    img.save(rf'{folder_path}\{file_name}')
# by Daniel Yoshida