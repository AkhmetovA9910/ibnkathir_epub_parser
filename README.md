# Tafsir Ibn Kathir EPUB → JSON

Парсер EPUB-книги «Коран. Тафсир ибн Касира» в структурированный JSON-файл для дальнейшей обработки (поиск, индексирование, импорт в БД и т.п.).

## Что делает

`parse_epub.py` читает EPUB, проходит по файлам сур (`content/s2.xhtml` … `content/s115.xhtml`), извлекает из каждого блока `<div class="verse">` номер аята, арабский текст и параграфы тафсира, и собирает всё в один JSON.

## Структура вывода

```json
{
  "title": "Quran - Ибн Касир Translation",
  "author": "Ибн Касир",
  "language": "ru",
  "surahs_count": 114,
  "surahs": [
    {
      "number": 1,
      "title": "Открывающая Коран (Аль-Фатиха)",
      "name_ru": "Открывающая Коран",
      "name_translit": "Аль-Фатиха",
      "verses_count": 7,
      "verses": [
        {
          "reference": "1:1",
          "surah": 1,
          "ayah": 1,
          "arabic": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
          "tafsir": ["...", "..."]
        }
      ]
    }
  ]
}
```

## Требования

- Python 3.10+
- `ebooklib`, `beautifulsoup4`, `lxml`

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip install ebooklib beautifulsoup4 lxml

python3 parse_epub.py
```

На выходе появится `tafsir_ibn_kathir.json` (~17.5 МБ) в корне проекта.

## Проверка целостности

После парсинга должно получиться **114 сур** и **6236 аятов** — это соответствует каноническому количеству аятов в Коране.

## Файлы

- `parse_epub.py` — скрипт-парсер
- `Коран. Тафсир ибн Касира.epub` — исходник
- `tafsir_ibn_kathir.json` — результат (не коммитится, см. `.gitignore`)
