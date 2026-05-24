# quality_analysis.py
import pandas as pd
from pathlib import Path
from data_quality_analyzer import DataQualityAnalyzer

def main():
    
    # ========= общий путь для сохранения reports ==========
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    # ================ Загрузите данные ===================
    ref_path = project_dir / "raw_data" / "customer_data.csv"
    
    if not ref_path.exists():
        print(f'Не найден справочник-источник: {ref_path}')
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
        
        # статус точности
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
    print(f'\nАнализ выбросов методом IQR')

    numeric_cols = ["age", "purchase_amount"]
    all_iqr_results = {}
    
    for col in numeric_cols:
        print(f'\nСтолбец: {col}')
        iqr_result = analyzer.ident_outliers_iqr(col, multiplier=1.5)
    
        if iqr_result:
            all_iqr_results[col] = iqr_result
            print(f"Статистики для '{iqr_result['Column']}':")
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
    
    # Boxplot для метода IQR
    print(f"\nВизуализация выбросов (Boxplot)")
    
    # Папка для сохранения графиков
    reports_dir = project_dir / "reports"
    
    # Строим boxplot для каждого столбца
    analyzer.plot_boxplots_all(columns=numeric_cols, save_dir=reports_dir)
    
    print(f'Все графики сохранены в: {reports_dir}')
    
    # ============ Анализ выбросов методом Z-score ==================
    print(f'\nАнализ выбросов методом Z-score')

    zscore_cols = ["age", "purchase_amount"]
    all_zscore_results = {}
    
    for col in zscore_cols:
        print(f'\nСтолбец: {col}')
        zscore_result = analyzer.ident_outliers_zscore(col, threshold=3.0)
        
        if zscore_result:
            all_zscore_results[col] = zscore_result
            
            print(f"Среднее: {zscore_result['Mean']:.2f}")
            print(f"Стандартное отклонение: {zscore_result['std']:.2f}")
            print(f"Порог: ±{zscore_result['Threshold']}")
            print(f"Найдено выбросов: {zscore_result['outlier_count']}шт.")
            
            if zscore_result["outliers_sample"]:
                print(f"\nПримеры выбросов (первые 10):")
                for idx, val, z in zscore_result['outliers_sample']:
                    if col == "purchase_amount":
                        print(f"[row {idx}] значение: {val:,.2f}руб. (Z={z})")
                    else:
                        print(f"[row {idx}] значение: {val} (Z={z})")
    
    # ========== Сравнение методов обнаружения выбросов ==========
    print(f'\nСравнение методов обнаружения выбросов (IQR vs Z-score)')
    
    comparison_results = []
    reports_dir = project_dir / "reports"
    
    for col in numeric_cols:
        print(f'\nСравнение для столбца: {col}')
              
        iqr_res = all_iqr_results.get(col)
        z_res = all_zscore_results.get(col)
        
        # Сравниваем
        if iqr_res and z_res:
            comp = analyzer.compare_outlier_methods(col, iqr_res, z_res)
            comparison_results.append(comp)
            
            print(f'Только IQR: {comp["iqr_only_count"]}')
            print(f'Только Z-score: {comp["zscore_only_count"]}')
            print(f'Нашли оба: {comp["both_count"]}')
            print(f'Согласие методов: {comp["agreement_pct"]}%')
            
            # статус согласия
            if comp["agreement_pct"] >= 70:
                status = "Высокое"
            elif comp["agreement_pct"] >= 40:
                status = "Умеренное"
            else:
                status = "Низкое"
            print(f'{status} согласие')

if __name__ == "__main__":
    main()
    
    
    