from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont
import io
import re

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (1240, 1754), "A5": (874, 1240), "Letter": (1275, 1650)}
PEN_COLORS = {
    "black": (0, 0, 0),
    "red": (220, 20, 60),
    "blue": (25, 25, 112),
    "green": (34, 139, 34)
}

# Available Fonts
FONTS = {
    "cursive": "fonts/CedarvilleCursive-Regular.ttf",
    "normal": "fonts/Kalam-Regular.ttf"
}

# Function to parse text into question-answer blocks
def parse_text(text):
    pattern = r"<q>(.*?)<\/q>|<a>(.*?)<\/a>"
    matches = re.findall(pattern, text)
    parsed = []
    for match in matches:
        if match[0]:  # Question
            parsed.append(("question", match[0]))
        if match[1]:  # Answer
            parsed.append(("answer", match[1]))
    return parsed

# Function to create an image with question-answer handling
def create_image(page_size, text_blocks, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load the font
        font = ImageFont.truetype(font_path, 50)
        line_spacing = 80
        margin = 100
        max_width = width - 2 * margin
        y_position = 100

        for block_type, content in text_blocks:
            pen_color = PEN_COLORS["black"] if block_type == "question" else PEN_COLORS["blue"]
            words = content.split(" ")
            line = ""

            for word in words:
                test_line = f"{line} {word}".strip()
                text_bbox = font.getbbox(test_line)
                text_width = text_bbox[2] - text_bbox[0]
                if text_width <= max_width:
                    line = test_line
                else:
                    # Draw current line
                    draw.text((margin, y_position), line, fill=pen_color, font=font)
                    y_position += line_spacing
                    line = word

                    # Ensure answer starts on a new line
                    if block_type == "answer" and line == word:
                        break

                # Check if we've reached the bottom of the page
                if y_position + line_spacing > height:
                    raise HTTPException(status_code=400, detail="Text exceeds page height.")

            # Draw any remaining text in the block
            if line:
                draw.text((margin, y_position), line, fill=pen_color, font=font)
                y_position += line_spacing

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint
@app.get("/create/{page_size}/{font_style}/prompt={text}")
def create_image_api(page_size: str, font_style: str, text: str):
    try:
        # Decode URL-encoded text
        decoded_text = unquote(text)

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style. Choose from cursive or normal.")

        # Parse the text into question-answer blocks
        text_blocks = parse_text(decoded_text)
        if not text_blocks:
            raise HTTPException(status_code=400, detail="Invalid input format. Use <q> and <a> tags for questions and answers.")

        # Get the font path
        font_path = FONTS[font_style]

        # Create the image
        image = create_image(PAGE_SIZES[page_size], text_blocks, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
