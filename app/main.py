from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io
from urllib.parse import unquote
from random import randint

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (595, 842), "A5": (420, 595), "Letter": (612, 792)}
PEN_COLORS = {"black": (0, 0, 0), "red": (255, 0, 0), "blue": (0, 0, 255), "green": (0, 255, 0)}

# Function to create an image
def create_image(page_size, pen_color, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load the font
        font = ImageFont.truetype(font_path, size=40)

        # Draw ruled lines
        for y in range(50, height, 50):
            draw.line((0, y, width, y), fill=(200, 200, 200), width=1)

        # Add jitter to mimic handwritten style
        def jitter(value, intensity=2):
            return value + randint(-intensity, intensity)

        # Write text with wrapping and alignment
        y_position = 60  # Start writing below the top margin
        margin = 50
        max_width = width - 2 * margin
        for line in text.split("\\n"):  # Split for multiline text
            words = line.split()
            line_text = ""
            for word in words:
                # Check if the word fits in the line
                test_line = f"{line_text} {word}".strip()
                test_width, _ = font.getsize(test_line)  # Get the size of the test line
                if test_width <= max_width:
                    line_text = test_line
                else:
                    # Write the current line and start a new one
                    draw.text((jitter(margin), jitter(y_position)), line_text, fill=pen_color, font=font)
                    y_position += 50  # Move to the next line
                    line_text = word  # Start with the new word

            # Draw the last line of the paragraph
            if line_text:
                draw.text((jitter(margin), jitter(y_position)), line_text, fill=pen_color, font=font)
                y_position += 50

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint
@app.get("/create/{page_size}/{pen_color}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, text: str):
    try:
        # Decode the text to handle URL-encoded characters
        decoded_text = unquote(text)

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color. Choose from black, red, blue, or green.")

        # Font path (ensure the font is uploaded to the fonts directory)
        font_path = "font/CedarvilleCursive-Regular.ttf"

        # Create the image
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], decoded_text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG")
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
