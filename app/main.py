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

# Available Fonts
FONTS = {
    "cursive": "fonts/CedarvilleCursive-Regular.ttf",
    "normal": "fonts/Kalam-Regular.ttf"
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

        # Split input text into segments (questions and answers)
        segments = text.split('<q>')[1:]  # Split by question tags, remove the first empty element
        for segment in segments:
            # Separate question and answer by <a> tags
            question_text = segment.split('</q>')[0]
            answer_text = segment.split('<a>')[1].split('</a>')[0]

            # Write question in black color
            question_bbox = font.getbbox(question_text)
            question_width = question_bbox[2] - question_bbox[0]
            if question_width <= max_width:
                draw.text((margin, y_position), f"{question_text}?", fill=PEN_COLORS["black"], font=font)
                y_position += line_spacing
            else:
                # Handle long question text with wrapping
                lines = wrap_text(question_text, font, max_width)
                for line in lines:
                    draw.text((margin, y_position), line, fill=PEN_COLORS["black"], font=font)
                    y_position += line_spacing

            # Write "Ans-" before answer text in blue color
            y_position += line_spacing // 2  # Add some space after the question
            draw.text((margin, y_position), "Ans-", fill=PEN_COLORS["blue"], font=font)
            y_position += line_spacing // 2  # Space between "Ans-" and actual answer

            # Handle answer wrapping
            answer_bbox = font.getbbox(answer_text)
            answer_width = answer_bbox[2] - answer_bbox[0]
            if answer_width <= max_width:
                draw.text((margin, y_position), answer_text, fill=PEN_COLORS["blue"], font=font)
                y_position += line_spacing
            else:
                # Handle long answer text with wrapping
                answer_lines = wrap_text(answer_text, font, max_width)
                for line in answer_lines:
                    draw.text((margin, y_position), line, fill=PEN_COLORS["blue"], font=font)
                    y_position += line_spacing

            # Check if there's enough space, and break if the page is filled
            if y_position + line_spacing > height:
                break

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def wrap_text(text, font, max_width):
    """
    Wrap the text into multiple lines to fit within the max width.
    """
    words = text.split(" ")
    lines = []
    line = ""

    for word in words:
        # Test if adding the word exceeds the max width
        test_line = f"{line} {word}".strip()
        test_bbox = font.getbbox(test_line)
        test_width = test_bbox[2] - test_bbox[0]
        
        if test_width <= max_width:
            line = test_line
        else:
            if line:  # Add current line to lines
                lines.append(line)
            line = word

    if line:  # Add the last line
        lines.append(line)

    return lines


# API Endpoint
@app.get("/create/{page_size}/{pen_color}/{font_style}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, font_style: str, text: str):
    try:
        # Decode URL-encoded text
        decoded_text = unquote(text)

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color. Choose from black, red, blue, or green.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style. Choose from cursive or normal.")

        # Get the font path based on font style
        font_path = FONTS[font_style]

        # Create the image
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], decoded_text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)  # High quality for better output
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
