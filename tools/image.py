import os
import gc
import pytesseract
from fuzzywuzzy import fuzz
from PIL import Image, ImageOps, ImageDraw, ImageFont

class ImageProcessor:
    BORDER_SIZE = 0.035
    BORDER_COLOR = (255, 255, 255)
    SHOW_COLOR = (0, 0, 0)
    TEXT_COLOR = '#fefefe'
    TEXT_DETECTION_ACCURACY = 75
    
    def insert_mark(image, text):
        image = ImageProcessor.__insert_mark(image, text)
        # gc.collect()
        return image

    def __insert_mark(image, text):
        ip = ImageProcessor
        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'font.ttf'
        )

        # insert border
        w, h = image.size
        size = round(h * ip.BORDER_SIZE) # border/font size
        new_w, new_h = w - 2 * size, h - 2 * size
        image = image.resize((new_w, new_h))
        image = ImageOps.expand(
            image = image,
            border = size,
            fill = ip.BORDER_COLOR
        )

        # insert text
        font = ImageFont.truetype(font_path, size)
        ImageDraw.Draw(image).text(
            xy = (0, h - size * 1.15),
            text = text,
            fill = ip.TEXT_COLOR,
            font = font
        )

        return image
    
    def detect_mark(image, text):
        match_ = ImageProcessor.__detect_mark(image, text)
        # gc.collect()
        return match_ >= ImageProcessor.TEXT_DETECTION_ACCURACY

    def __detect_mark(image, text):
        ip = ImageProcessor
        
        # apply filter
        w, h = image.size
        
        for x in range(w):
            for y in range(h):
                pixel = image.getpixel((x, y))
                if pixel[0:3] != ip.BORDER_COLOR:
                    color = (
                        ip.SHOW_COLOR
                            if len(pixel) == 3
                            else ip.SHOW_COLOR + (pixel[3], )
                    )
                    image.putpixel((x, y), color)
        
        # crop image
        size = h * ip.BORDER_SIZE
        border_coordinate = (0, h - size, w, h)
        image_crop = image.crop(border_coordinate)

        # computer vision
        config = '--psm 6 --oem 3'
        lang = 'eng+rus'
        
        string = pytesseract.image_to_string(
            image_crop,
            lang = lang,
            config = config
        )

        image_crop.close()

        match_ = fuzz.partial_ratio(string, text)
        return match_ 

def test():
    image = Image.open('./img1.png')
    image = ImageProcessor.insert_mark(image, 'CHUNGA CHANGA')
    match_ = ImageProcessor.detect_mark(image, 'CHUNGA CHANGA')
    print(match_)
    image.close()


def main():
    while True:
        input('> ')
        test()
        input('> ')
        
if __name__ == '__main__':
    main()

