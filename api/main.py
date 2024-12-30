from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# Available page sizes and colors
PAGE_SIZES = {
    'A4': (595, 842),
    'A5': (420, 595),
    'Letter': (612, 792)
}

PEN_COLORS = {
    'black': (0, 0, 0),
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'purple': (128, 0, 128)
}

# Function to create the image
def create_image(page_size, pen_color, text):
    width, height = page_size
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Add ruled lines to the page
    line_spacing = 25
    line_y = 40
    while line_y < height:
        draw.line((20, line_y, width - 20, line_y), fill=(200, 200, 200), width=1)
        line_y += line_spacing

    # Use a handwritten font
    try:
        font = ImageFont.truetype("fonts/DancingScript-Regular.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    # Wrap text to fit the page width
    max_text_width = width - 40
    lines = []
    words = text.split(' ')
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        test_width, _ = draw.textsize(test_line, font=font)
        if test_width <= max_text_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Write the text onto the page
    current_y = 50
    for line in lines:
        draw.text((30, current_y), line, fill=pen_color, font=font)
        current_y += 40

    return image

# API endpoint to generate the image
@app.get("/create/{page_size}/{pen_color}/prompt")
def generate_image(page_size: str, pen_color: str, prompt: str):
    if page_size not in PAGE_SIZES:
        raise HTTPException(status_code=400, detail="Invalid page size")
    if pen_color.lower() not in PEN_COLORS:
        raise HTTPException(status_code=400, detail="Invalid pen color")

    page_size = PAGE_SIZES[page_size]
    pen_color = PEN_COLORS[pen_color.lower()]

    # Create the image
    image = create_image(page_size, pen_color, prompt)

    # Save the image to a byte stream
    byte_io = io.BytesIO()
    image.save(byte_io, 'PNG')
    byte_io.seek(0)

    # Return the image as a response
    return StreamingResponse(byte_io, media_type="image/png")
