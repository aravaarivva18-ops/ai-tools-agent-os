import argparse
import os
import sys

import fastapi
import fastapi.responses
import fastapi.staticfiles
import pydantic
import uvicorn

# Добавляем путь к локальной папке tools в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
import content_gen
import upload_cli

app = fastapi.FastAPI(title="YouTube Faceless Video Generator API")

# Конфигурация путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
UI_DIR = os.path.join(BASE_DIR, "ui")


class GenerationRequest(pydantic.BaseModel):
    niche: str


class ValidationRequest(pydantic.BaseModel):
    niche: str


class UploadRequest(pydantic.BaseModel):
    package_path: str


@app.post("/api/validate")
def validate_niche(request: ValidationRequest):
    """Проверяет тему на соответствие правилам безопасности YouTube."""
    generator = content_gen.VideoGenerator(output_dir=OUTPUT_DIR)
    try:
        generator.validate_content(request.niche)
        return {"status": "ok", "message": "Niche is safe."}
    except content_gen.ContentPolicyError as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/generate")
def generate_video(request: GenerationRequest):
    """Запускает полный цикл генерации видео с SEO и Thumbnail."""
    generator = content_gen.VideoGenerator(output_dir=OUTPUT_DIR)
    try:
        video_path, metadata = generator.run_pipeline(niche=request.niche)
        video_filename = os.path.basename(video_path)
        thumbnail_filename = os.path.basename(metadata["thumbnail_path"])
        return {
            "status": "success",
            "video_url": f"/videos/{video_filename}",
            "thumbnail_url": f"/videos/{thumbnail_filename}",
            "metadata": metadata,
        }
    except content_gen.ContentPolicyError as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=500, detail=f"Generation failed: {e!s}"
        ) from e


@app.post("/api/upload")
def upload_video(request: UploadRequest):
    """Имитирует загрузку видео на YouTube."""
    uploader = upload_cli.YouTubeUploader(output_dir=OUTPUT_DIR)
    try:
        result = uploader.upload_video(request.package_path)
        return result
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/analytics")
def get_analytics():
    """Возвращает заглушку аналитики."""
    uploader = upload_cli.YouTubeUploader(output_dir=OUTPUT_DIR)
    return uploader.get_analytics_stub()


# Раздача сгенерированных медиафайлов
@app.get("/videos/{filename}")
def get_video(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        media_type = "video/mp4"
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            media_type = "image/jpeg"
        elif filename.endswith(".json"):
            media_type = "application/json"
        return fastapi.responses.FileResponse(file_path, media_type=media_type)
    raise fastapi.HTTPException(status_code=404, detail="File not found")


# Раздача статического веб-интерфейса
app.mount("/", fastapi.staticfiles.StaticFiles(directory=UI_DIR, html=True), name="ui")


def run_cli():
    parser = argparse.ArgumentParser(description="YouTube Faceless Video Generator CLI")
    parser.add_argument(
        "--niche", type=str, default=None, help="Niche/topic for the video"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output directory path"
    )
    parser.add_argument("--serve", action="store_true", help="Start Web UI Server")
    parser.add_argument("--port", type=int, default=8000, help="Web UI Server port")
    parser.add_argument(
        "--upload",
        type=str,
        default=None,
        help="Upload package JSON path to upload to YouTube",
    )

    args = parser.parse_args()

    if args.serve:
        print(f"Starting Web UI Server on http://localhost:{args.port}")
        uvicorn.run("main:app", host="0.0.0.0", port=args.port, reload=True)  # nosec B104  # noqa: S104
    elif args.upload:
        uploader = upload_cli.YouTubeUploader(output_dir=args.output or OUTPUT_DIR)
        print(f"Starting YouTube upload for package: {args.upload}...")
        try:
            res = uploader.upload_video(args.upload)
            print("\n==================================================")
            print("🎉 Upload Process Finished!")
            print(f"Status: {res['status'].upper()}")
            print(f"Mock Video URL: {res['youtube_url']}")
            print("\nInstructions:")
            print(res["instructions"])
            print("==================================================")
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
            sys.exit(1)
    elif args.niche:
        out_dir = args.output or OUTPUT_DIR
        generator = content_gen.VideoGenerator(output_dir=out_dir)
        print(f"Starting pipeline for niche: {args.niche}...")
        try:
            video_path, metadata = generator.run_pipeline(niche=args.niche)
            print("\n==================================================")
            print("🎉 Success! Video, SEO, and Thumbnail generated.")
            print(f"Video Path: {video_path}")
            print(f"Thumbnail Path: {metadata['thumbnail_path']}")
            print(f"Upload Package: {metadata['upload_package_path']}")
            print(f"Title: {metadata['title']}")
            print(f"Description: {metadata['description']}")
            print("==================================================")
        except content_gen.ContentPolicyError as e:
            print(f"❌ Policy Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "No CLI arguments specified. Starting Web UI Server on http://localhost:8000..."
        )
        uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104  # noqa: S104
    else:
        run_cli()
