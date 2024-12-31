from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (1240, 1754), "A5": (874, 1240), "Letter": (1275, 1650)}  # High resolution for good quality
PEN_COLORS = {
    "black": (0, 0, 0),
    "red": (220, 20, 60),
    "blue": (25, 25, 112),
    "green": (34, 139, 34)
}

# Function to create an image with the given parameters
def create_image(page_size, pen_color, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load the font locally
        font = ImageFont.truetype(font_path, 50)  # Set default font size to 50 for high-quality text

        # Draw ruled lines
        line_spacing = 80  # Adjust spacing between ruled lines
        for y in range(line_spacing, height, line_spacing):
            draw.line((0, y, width, y), fill=(200, 200, 200), width=2)

        # Handle word wrapping and alignment
        margin = 100  # Left margin for text
        max_width = width - 2 * margin  # Maximum width for text
        y_position = 100  # Start writing below the top margin

        # Split text into words
        words = text.split(" ")
        line = ""
        for word in words:
            # Check if adding the next word exceeds the maximum width
            test_line = f"{line} {word}".strip()
            text_width, _ = font.getsize(test_line)  # Use getsize to measure text width
            if text_width <= max_width:
                line = test_line
            else:
                # Draw the current line and start a new one
                draw.text((margin, y_position), line, fill=pen_color, font=font)
                y_position += line_spacing
                line = word

            # Check if we've reached the bottom of the page
            if y_position + line_spacing > height:
                break

        # Draw any remaining text
        if line:
            draw.text((margin, y_position), line, fill=pen_color, font=font)

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
        font_path = "fonts/CedarvilleCursive-Regular.ttf"  # Path to your font
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)  # High quality for better output
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
