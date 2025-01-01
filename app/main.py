from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (1240, 1754), "A5": (874, 1240), "Letter": (1275, 1650)}
PEN_COLORS = {"black": (0, 0, 0), "red": (220, 20, 60), "blue": (25, 25, 112), "green": (34, 139, 34)}

FONTS = {"cursive": "fonts/CedarvilleCursive-Regular.ttf", "normal": "fonts/Kalam-Regular.ttf"}

def wrap_text(text, font, max_width):
    """
    Wrap text so that it fits within the specified width.
    """
    lines = []
    current_line = []
    
    for word in text.split():
        # Check the width of the current line with the next word
        test_line = ' '.join(current_line + [word])
        text_width, _ = font.getsize(test_line)  # Use getsize() to get the width of the text
        if text_width <= max_width:
            current_line.append(word)
        else:
            # Start a new line
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))  # Add the last line
    return lines

def create_image(page_size, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, 50)

        # Draw ruled lines
        line_spacing = 80
        for y in range(line_spacing, height, line_spacing):
            draw.line((0, y, width, y), fill=(200, 200, 200), width=2)

        # Decode URL-encoded input and split questions and answers
        text = unquote(text)  # Decode URL-encoded input
        segments = text.split("<q>")
        y_position = 100
        margin = 100
        question_number = 1

        for segment in segments[1:]:
            # Extract question and answer, ensuring both parts exist
            question_answer = segment.split("</q>")[0]
            answer = segment.split("</q>")[1].split("<a>")[1].split("</a>")[0] if "<a>" in segment else ""

            # Wrap and draw the question with numbering
            question_lines = wrap_text(f"{question_number}. {question_answer.strip()}", font, width - 2 * margin)
            for line in question_lines:
                draw.text((margin, y_position), line, fill=PEN_COLORS["black"], font=font)
                y_position += line_spacing

            # Write "Ans-" prefix and the answer
            if answer:
                answer_lines = wrap_text(f"Ans- {answer.strip()}", font, width - 2 * margin)
                for line in answer_lines:
                    draw.text((margin, y_position), line, fill=PEN_COLORS["blue"], font=font)
                    y_position += line_spacing

            question_number += 1

            # Stop if out of page space and continue on new page if necessary
            if y_position + line_spacing > height:
                y_position = 100  # Reset to top of the next page
                image.paste(create_image(page_size, text, font_path), (0, y_position))
                break

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/create/{page_size}/{font_style}/prompt={text}")
def create_image_api(page_size: str, font_style: str, text: str):
    try:
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style. Choose from cursive or normal.")

        font_path = FONTS[font_style]
        image = create_image(PAGE_SIZES[page_size], text, font_path)

        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
