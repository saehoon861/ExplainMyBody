import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.getcwd())

from services.ocr.ocr_service import OCRService

async def main():
    print("Initializing OCR Service...")
    try:
        service = OCRService()
        if service.matcher:
            print("OCR Service initialized successfully.")
        else:
            print("OCR Service failed to initialize matcher.")
            sys.exit(1)
            
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
