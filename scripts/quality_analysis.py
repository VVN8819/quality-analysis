import pandas as pd
from pathlib import Path
from data_quality_analyzer import DataQualityAnalyzer

def main():
    
    # Загрузите данные в DataFrame
    ref_path = Path(__file__).parent.parent / "raw_data" / "customer_data.csv"
    
    if not ref_path.exists():
        print(f'Не найден справочник: {ref_path}')
        return
    
    print(f'Загружаем файл: {ref_path}')
    
    # Чтение csv
    ref_df = pd.read_csv(ref_path, encoding="utf-8")
    
    analyzer = DataQualityAnalyzer(ref_df)
    
    # Полнота
    completeness_report = analyzer.calculate_completeness()
    print(f'\nРезультат анализа полноты: \n{completeness_report}')
    
if __name__ == "__main__":
    main()