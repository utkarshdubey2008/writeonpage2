from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (595, 842), "A5": (420, 595), "Letter": (612, 792)}
PEN_COLORS = {"black": (0, 0, 0), "red": (255, 0, 0), "blue": (0, 0, 255), "green": (0, 255, 0)}

# Function to create an image with the given parameters
def create_image(page_size, pen_color, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load the font locally
        font = ImageFont.truetype(font_path, 40)  # Set default size to 40

        # Draw ruled lines
        for y in range(50, height, 50):
            draw.line((0, y, width, y), fill=(200, 200, 200), width=1)

        # Write text with the specified font
        y_position = 60  # Start writing below the top margin
        for line in text.split("\\n"):  # Support for multiline text
            draw.text((50, y_position), line, fill=pen_color, font=font)
            y_position += 50

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint
@app.get("/create/{page_size}/{pen_color}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, text: str):
    try:
        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color. Choose from black, red, blue, or green.")

        # Create the image
        font_path = "fonts/Cedavillie_Cursive.ttf"  # Path to your font
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG")
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
