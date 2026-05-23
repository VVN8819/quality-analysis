# quality_analysis.py
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
    columns = ["email", "phone", "age", "purchase_amount", "registration_date"]
    accuracy_report = []
    
    for col in columns:
        print(f'\nПроверка: {col}')
        result = analyzer.calculate_accuracy(col)
        accuracy_report.append(result)
        
        # 2. Считает количество корректных значений 
        # 3. Рассчитывает процент точности
        valid = result["Validated_count"].values[0]
        acc = result["Accuracy_%"].values[0]
        
        if acc >= 95:
            status = "Отлично"
        elif acc >= 85:
            status = "Внимание"
        else:
            status = "Критично"
        
        print(f'Результат анализа точности: \n{status}: точность {acc}% корректных значений {valid}')
        
    if accuracy_report:
        full_accuracy_report = pd.concat(accuracy_report, ignore_index=True)
        print(f'\nСводный отчёт по точности: \n{full_accuracy_report}')
        
    # Выводим и сохраняем примеры некорректных данных
    error_examples = analyzer.report_accuracy_errors(columns=columns, max_examples=5)
    
    error_report_path = project_dir / "reports" / "accuracy_errors_report.txt"
    with open(error_report_path, 'w', encoding='utf-8') as f:
        f.write('Примеры некорректных данных (Accuracy)\n')
        for col, df_err in error_examples.items():
            f.write(f'\nСтолбец: {col}\n')
            f.write(f'Показано ошибок первых {len(df_err)}\n')
            f.write(df_err.to_string(index=False) + "\n")
    
    print(f'Детальный отчёт сохранён: {error_report_path}')
    
    # ============ Анализ выбросов методом IQR ==================
    numeric_cols = ["age", "purchase_amount"]
    
    for col in numeric_cols:
        print(f'\nСтолбец: {col}')
        iqr_result = analyzer.ident_outliers_iqr(col, multiplier=1.5)
    
        if iqr_result:
            print(f"татистики для '{iqr_result['Column']}':")
            print(f"Q1 (25%): {iqr_result['Q1']}")
            print(f"Q3 (75%): {iqr_result['Q3']}")
            print(f"IQR: {iqr_result['IQR']}")
            print(f"Нижняя граница: {iqr_result['lower_bound']}")
            print(f"Верхняя граница: {iqr_result['upper_bound']}")
            print(f"\nНайдено выбросов: {iqr_result['outliers_count']}")
        
            if iqr_result["outliers_sample"]:
                print(f"\nПримеры выбросов (первые 10):")
                for idx, val in zip(iqr_result['outliers_indices'], iqr_result['outliers_sample']):
                    if col == "purchase_amount":
                        print(f"[row {idx}] значение: {val:,.2f}руб.")
                    else:
                        print(f"[row {idx}] значение: {val}")
                        
    
if __name__ == "__main__":
    main()
    
    
    