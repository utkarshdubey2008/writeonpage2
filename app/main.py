from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
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

        # Load the fonts
        regular_font = ImageFont.truetype(font_path, 50)  # Regular font for body text
        heading_font = ImageFont.truetype(font_path, 80)  # Larger font for heading

        # Draw ruled lines (optional, if you want lines)
        line_spacing = 80  # Adjust spacing between ruled lines

        # Split text into lines
        lines = text.split("\n")
        if not lines:
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        # Handle heading (first line)
        heading = lines[0].strip()
        heading_uppercase = heading.upper()  # Convert heading to uppercase
        heading_bbox = heading_font.getbbox(heading_uppercase)
        heading_width = heading_bbox[2] - heading_bbox[0]
        heading_height = heading_bbox[3] - heading_bbox[1]
        heading_x = (width - heading_width) // 2  # Center align the heading
        heading_y = 50  # Position at the top
        draw.text((heading_x, heading_y), heading_uppercase, fill=pen_color, font=heading_font)

        # Handle body text (remaining lines)
        body_text = "\n".join(lines[1:]).strip()
        margin = 100  # Left margin for text
        max_width = width - 2 * margin  # Maximum width for text
        y_position = heading_y + heading_height + 50  # Start body text below the heading

        # Split body text into words for word wrapping
        words = body_text.split(" ")
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            text_bbox = regular_font.getbbox(test_line)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width <= max_width:
                line = test_line
            else:
                draw.text((margin, y_position), line, fill=pen_color, font=regular_font)
                y_position += line_spacing
                line = word

            # Check if we've reached the bottom of the page
            if y_position + line_spacing > height:
                break

        # Draw any remaining text
        if line:
            draw.text((margin, y_position), line, fill=pen_color, font=regular_font)

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint
@app.get("/create/{page_size}/{pen_color}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, text: str):
    try:
        # Decode URL-encoded text
        decoded_text = unquote(text)

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color. Choose from black, red, blue, or green.")

        # Create the image
        font_path = "fonts/CedarvilleCursive-Regular.ttf"  # Path to your font
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], decoded_text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)  # High quality for better output
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
