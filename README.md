# quality-analysis
Учебный проект на тему "Анализ качества данных интернет-магазина".

**Цель:** Научиться рассчитывать метрики качества данных, использовать статистические методы для поиска аномалий и создавать отчеты о качестве данных.

**Проект демонстрирует:**
- Расчет метрик полноты данных, визуализация и анализ результатов
- Расчет метрик точности данных, определение правил валидации, отчет о найденных ошибках
- Статистический анализ выбросов методом IQR и Z-score, визуализация (boxplot, гисторамма), сравнительный анализ методов
- Расчет актуальности данных

Структура:
    raw_data/ - Исходные данные
        customer_data.csv - CSV-файл с данными о клиентах (10 000 записей)
    reports/ - Результаты анализа
        accuracy_errors_report.txt - Примеры некорректных данных, метрика Точности (email, phone, age...)
        boxplot_iqr_age.png - Boxplot для age (метод IQR)
        boxplot_iqr_purchase_amount.png - Boxplot для purchase_amount
        completeness_chart.png - Столбчатая диаграмма полноты данных
        histogram_zscore_age.png - Гистограмма age с границами ±3σ
        histogram_zscore_purchase_amount.png - Гистограмма purchase_amount
        outlier_comparison_summary.txt - Сравнение методов IQR vs Z-score
        timeliness_report.txt - Расчет актуальности данных с примерами данных из будущего и старых данных (Timeliness) — registration_date
    scripts/ - Python-скрипты
        __pycache__/ - Кэширование
        data_quality_analyzer.py - Класс DataQualityAnalyzer (логика анализа)
        quality_analysis.py - Главный скрипт (запуск пайплайна)
    .gitignore - Игнорируемые файлы для Git
    LICENSE - Лицензия проекта
    README.md - Описание проекта
    report.md - Итоговый отчёт о качестве данных