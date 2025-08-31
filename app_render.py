from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import shutil
import tempfile
import os
import time
from downloader_render import main_function  # tvoja funkcija koja generira zip

app = FastAPI()

#def cleanup_temp_dir(path: str):
#    try:
#        if os.path.exists(path):
#            shutil.rmtree(path)
#            print(f"🗑️ Obrisan temp direktorij: {path}")
#    except Exception as e:
#        print(f"⚠️ Greška pri brisanju {path}: {e}")

@app.get("/generate")
async def generate(background_tasks: BackgroundTasks,text: str = Query(..., description="Tekst za generiranje zipa")):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        temp_dir = tempfile.mkdtemp(prefix="output_")
        # unikatno ime fajla
        timestamp = int(time.time())
        zip_filename = f"output_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        # main_function neka snimi zip na disk i vrati path
        generated_path = main_function(text, output_path=temp_dir)
        #DOSAD output_path=zip_path

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
        print("prc")
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

