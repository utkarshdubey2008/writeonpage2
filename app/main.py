from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont
import io

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
    "normal": "fonts/Kalam-Regular.ttf",
    "sansita": "fonts/Sansita-Regular.ttf"
}

# Function to create a ruled page background
def create_ruled_page(width, height, line_spacing=70):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Draw horizontal lines
    for y in range(100, height, line_spacing):
        draw.line([(50, y), (width - 50, y)], fill=(200, 200, 200), width=2)

    return image

# Function to overlay question-answer text on the ruled page
def create_question_answer_image(page_size, question_color, answer_color, qa_pairs, font_path):
    try:
        width, height = page_size
        # Create a ruled page
        image = create_ruled_page(width, height)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, 50)  # Default font size is 50

        # Line Spacing and Margins
        line_spacing = 70
        margin = 100
        max_width = width - 2 * margin
        y_position = 100

        for idx, (question, answer) in enumerate(qa_pairs, start=1):
            # Write the question
            question_text = f"{idx}. {question}"
            draw.text((margin, y_position), question_text, fill=question_color, font=font)
            y_position += line_spacing

            # Check if we've reached the bottom of the page
            if y_position + line_spacing > height:
                raise HTTPException(status_code=400, detail="Text exceeds page size")

            # Write the answer
            answer_text = f"Ans:- {answer}"
            draw.text((margin, y_position), answer_text, fill=answer_color, font=font)
            y_position += line_spacing

            # Check if we've reached the bottom of the page again
            if y_position + line_spacing > height:
                raise HTTPException(status_code=400, detail="Text exceeds page size")

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint for Question-Answer Mode
@app.get("/create/{page_size}/{font_style}/{qa_path:path}")
def create_question_answer_api(page_size: str, font_style: str, qa_path: str):
    try:
        # Decode URL-encoded text
        decoded_path = unquote(qa_path)
        qa_segments = decoded_path.split("/")
        qa_pairs = []

        # Parse question-answer pairs
        for i in range(0, len(qa_segments), 4):
            if i + 3 >= len(qa_segments) or not qa_segments[i].startswith("q") or not qa_segments[i + 2].startswith("a"):
                raise HTTPException(status_code=400, detail="Invalid question-answer format.")
            question = qa_segments[i + 1]
            answer = qa_segments[i + 3]
            qa_pairs.append((question, answer))

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style. Choose from cursive, normal, or sansita.")

        # Get the font path based on font style
        font_path = FONTS[font_style]

        # Create the image
        image = create_question_answer_image(
            PAGE_SIZES[page_size],
            PEN_COLORS["black"],  # Questions are in black
            PEN_COLORS["blue"],   # Answers are in blue
            qa_pairs,
            font_path
        )

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
