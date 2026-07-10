pip install -r requirements.txt
brew install tesseract tesseract-lang   # OCR for prepare.py and crop.py

0. Put app screenshots in img_root/raw/
1. python prepare.py [--dry-run] [--verbose]
2. Paste Vietnamese translations below `---` in translate.txt (same line structure)
3. python apply_translate.py name [--dry-run]
4. python crop.py [chapter] [item] [--select]
5. python build_pdf.py [--single-margin] [--verbose]

Manual chapter/item setup (optional):
- python template.py chapter goals_of_chess "Goals of Chess"
- python template.py chapter 1 goals_of_chess "Goals of Chess"
- python template.py item "title"
- python template.py item stalemate "title" note here
