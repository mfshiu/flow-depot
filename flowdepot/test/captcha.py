# pip install --upgrade openai>=1.40.0
import base64, mimetypes, argparse
import base64, mimetypes
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openai_client = OpenAI()
print("使用的 OpenAI API Key:", openai_client.api_key)


def _to_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime: mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

  
def ocr_id(image_path: str) -> str:
    """用 gpt-4o-mini 進行 OCR，回傳純文字"""
    data_url = _to_data_url(image_path)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "請輸出圖片中的純文字，不要任何解釋或符號。"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        temperature=0,
    )
    content = resp.choices[0].message.content
    
    return content.strip() if content else ""


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="OCR via ChatGPT (gpt-4o-mini)")
    p.add_argument("image", help="圖片路徑（png/jpg/webp）")
    args = p.parse_args()
    print(ocr_id(args.image))