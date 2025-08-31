from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import os
import time
from downloader_render import main_function  # tvoja funkcija koja generira zip

app = FastAPI()
OUTPUT_FOLDER = "outputs"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


@app.get("/generate")
async def generate(text: str = Query(..., description="Tekst za generiranje zipa")):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # unikatno ime fajla
        timestamp = int(time.time())
        zip_filename = f"output_{timestamp}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)

        # main_function neka snimi zip na disk i vrati path
        generated_path = main_function(text, output_path=zip_path)

        # funkcija za streamanje fajla
        def file_iterator(path, chunk_size=8192):
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk
            # cleanup nakon što je fajl poslan
      #      try:
      #          if os.path.exists(path):
      #              os.remove(path)
      #              print(f"🗑️ Obrisan fajl: {path}")
      #      except Exception as e:
      #          print(f"⚠️ Greška pri brisanju fajla: {e}")

        return StreamingResponse(
            file_iterator(generated_path),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Connection": "keep-alive",
                "Keep-Alive": "timeout=5, max=1000"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pokretanje preko uvicorn:
# python -m uvicorn app_fastapi:app --reload

