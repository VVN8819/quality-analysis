import pandas as pd
from pathlib import Path
from data_quality_analyzer import DataQualityAnalyzer

def main():
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    # Загрузите данные в DataFrame
    ref_path = project_dir / "raw_data" / "customer_data.csv"
    
    if not ref_path.exists():
        print(f'Не найден справочник: {ref_path}')
        return
    
    print(f'Загружаем файл: {ref_path}')
        
    # =================== Чтение csv ====================
    ref_df = pd.read_csv(ref_path, encoding="utf-8")
    
    analyzer = DataQualityAnalyzer(ref_df)
    
    # =============== Полнота ===================
    completeness_report = analyzer.calculate_completeness()
    print(f'\nРезультат анализа полноты: \n{completeness_report}')
    
    # Сохранение completeness_chart.png
    chart_completeness_path = project_dir / "reports" / "completeness_chart.png"
    
    # визуализируем результаты - Полнота
    analyzer.plot_completeness(save_path=str(chart_completeness_path))
    print(f'\nСтроим график полноты')
    print(f'\nСохраняем график полноты в {chart_completeness_path}')
    
    # ================== Точность ===================
    accuracy_report = analyzer.calculate_accuracy()
    print(f'\nРезультат анализа точности: \n{accuracy_report}')
    
    
if __name__ == "__main__":
    main()