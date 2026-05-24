# data_quality_analyzer.py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import re
from datetime import datetime
import numpy as np
from scipy import stats

# Класс, который хранит данные и проводит расчеты.
class DataQualityAnalyzer:

    def __init__(self, df: pd.DataFrame):
        # Копируем данные, чтобы не сломать исходный файл случайными изменениями
        self.df = df.copy()
        self.metrics = {}   # Сюда складываем результаты расчетов
    
    # 1. считаем полноту и визуализируем результаты
    def calculate_completeness(self) -> pd.DataFrame:
        
        # 2. Считает общее количество значений
        total_rows = len(self.df)
        results = []
        
        # 1. Проходит по каждому столбцу
        for column in self.df.columns:
            count_filled = self.df[column].count()
            # 3. Считает количество пропущенных значений
            count_empt = total_rows - count_filled
            # 4. Рассчитывает процент полноты
            completeness_pct = (count_filled / total_rows) * 100 if total_rows > 0 else 0
            
            # 5. Возвращает словарь с результатами для каждого столбца
            results.append({
                "Column": column,
                "Total Rows": total_rows,
                "Filled": count_filled,
                "Empty": count_empt,
                "Completeness_%": completeness_pct
            })
        
        self.metrics["completeness"] = pd.DataFrame(results)
        return self.metrics["completeness"]
    
    # Создайте столбчатую диаграмму, показывающую полноту данных по каждому столбцу
    def plot_completeness(self, save_path: str = None):
        df_comp = self.metrics["completeness"].copy()
        df_comp_sorted = df_comp.sort_values(by="Completeness_%", ascending=True)
        
        def get_color(pct):
            if pct >= 95: return 'green'
            elif pct >= 85: return 'orange'
            else: return 'red'
            
        df_comp_sorted["Color"] = df_comp_sorted["Completeness_%"].apply(get_color)
        
        plt.figure(figsize=(10, 6))
        plt.bar(df_comp_sorted["Column"], df_comp_sorted["Completeness_%"], 
                color=df_comp_sorted["Color"], edgecolor='black', linewidth=0.8)
        
        plt.title('Полнота данных по столбцам (Completeness)', fontsize=15, fontweight='bold', pad=15)
        plt.xlabel('Столбцы', fontsize=12)
        plt.ylabel('Заполненность (%)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 105)  # Немного места сверху для значений
        plt.grid(axis='y', linestyle=':', alpha=0.5)
        plt.tight_layout()
        
        if save_path:
            # Создаем папку reports, если её нет
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f'График сохранен: {save_path}')
        
        plt.show()
    
    # 2. считаем точность
    # ========= Универсальный метод для расчёта Accuracy. ==============
    def _validate_column(self, column: str, validator_func, rule_name: str) -> pd.DataFrame:
        
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        total_valid = len(non_missing)
        
        # Если данных нет
        if total_valid == 0:
            return pd.DataFrame({
            "Column": [column],
            "Rule": [rule_name],
            "Total_valid_non_missing": [0],
            "Validated_count": [0],
            "Invalid_count": [0],
            "Accuracy_%": [0.0]
        })
        
        # проверка всех непустых на правило корректности
        validate_results = non_missing.apply(validator_func)
        
        validated_count = validate_results.sum() # прошли проверку
        invalid_count = total_valid - validated_count # не прошли проверку
        accuracy_pct = (validated_count / total_valid) * 100
        
        return pd.DataFrame({
            "Column": [column],
            "Rule": [rule_name],
            "Total_valid_non_missing": [total_valid],
            "Validated_count": [int(validated_count)],
            "Invalid_count": [int(invalid_count)],
            "Accuracy_%": [round(accuracy_pct, 2)]
        })
    
    # ========= определите правила корректности для столбца ============
    def _get_validator(self, column: str):
        validators = {
            # • email: должен содержать @ и домен (например, user@domain.com) 
            "email": (
                lambda value: (
                    isinstance(value, str) and
                    bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value.strip()))
                ),
                'contains @ and valid domain'
            ),
            
            # • phone: должен начинаться с +7 и содержать 11 цифр 
            "phone": (
                lambda value: (
                    isinstance(value, str) and
                    value.strip().startswith('+7') and
                    len(re.sub(r'\D', '', value)) == 11
                ),
                'starts with +7 and has 11 digits'
            ),
            
            # • age: должен быть в диапазоне 0-120 лет 
            "age": (
                lambda value: (
                    isinstance(value, (int, float)) and
                    0 <= value <= 120
                ),
                'is between 0-120 years old'
            ),
            
            # • purchase_amount: не может быть отрицательным 
            "purchase_amount": (
                lambda value: (
                    isinstance(value, (int, float)) and
                    0 <= value
                ),
                'more than 0'
            ),  
            
            # • registration_date: не может быть в будущем
            "registration_date": (
                lambda value: self._is_valid_date_not_future(value),
                'valid date & not in the future'
            )
        }
        
        if column not in validators:
            raise ValueError(f'Нет правила валидации для столбца: {column}')
        
        return validators[column]
    
    # ================ валидная дата и не в будущем ===================
    def _is_valid_date_not_future(self, value) -> bool:
        try:
            dt = pd.to_datetime(value, errors='coerce')
            if pd.isna(dt):
                return False
            return dt.date() <= datetime.today().date()
        except Exception:
            return False
    
    # ============ Рассчитывает метрику Accuracy для столбца ============
    def calculate_accuracy(self, column: str) -> pd.DataFrame:
        
        # Получаем правила корректности для столбца и название правила
        validator_func, rule_name = self._get_validator(column)
        
        results = self._validate_column(column, validator_func, rule_name)
    
        # Сохраняем результат в metrics
        if "accuracy" not in self.metrics:
            self.metrics["accuracy"] = {}
        self.metrics["accuracy"][column] = results
        
        return results
    
    # ======== Выведите примеры некорректных данных для каждого столбца ==========
    def report_accuracy_errors(self, columns: list, max_examples: int) -> dict:
        error_report = {}
        print(f'\nПримеры некорректных данных')
        for column in columns:
            try:
                # Получаем правила корректности для столбца и название правила
                validator_func, rule_name = self._get_validator(column)
            
                # исключаем пропуски из знаменателя
                non_missing = self.df[column].dropna()
            
                # проверка всех непустых на правило корректности
                validate_results = non_missing.apply(validator_func)
                invalid_mask = ~validate_results
            
                if invalid_mask.sum() > 0:
                    # Берём первые max_examples ошибок
                    invalid_examples = non_missing[invalid_mask].head(max_examples)
                
                    error_report[column] = pd.DataFrame({
                        "index": invalid_examples.index.tolist(),
                        "value": invalid_examples.values.tolist(),
                        "rule": rule_name
                    })
                
                    print(f'\n{column} {rule_name} - ошибок: {invalid_mask.sum()} из {len(non_missing)} проверенных')
                
                else:
                    print(f'{column} - ошибок не обнаружено')
                    
            except ValueError as e:
                print(f"\nСтолбец: `{column}` — пропущен: {e}")
                
        return error_report
    
    # 3. выбросы в числовом столбце методом IQR.
    def ident_outliers_iqr(self, column: str, multiplier: float) -> dict:
        
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        numeric_data = pd.to_numeric(non_missing, errors='coerce').dropna()
        
        if len(numeric_data) == 0:
            print(f"Столбец '{column}' не содержит числовых данных для IQR")
            return {}
        
        # Рассчитайте статистики
        Q1 = numeric_data.quantile(0.25)
        Q3 = numeric_data.quantile(0.75)
        IQR = Q3 - Q1
        
        # Определите значения вне границ [lower_bound, upper_bound]
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        # Найдите выбросы
        outliers_mask = (numeric_data < lower_bound) | (numeric_data > upper_bound)
        outliers = numeric_data[outliers_mask]
        
        # Подсчитайте количество выбросов
        # Выведите примеры найденных выбросов
        outliers_count = len(outliers)
                
        results = {
            "Column": column,
            "Q1": round(Q1, 2),
            "Q3": round(Q3, 2),
            "IQR": round(IQR, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "outliers_count": int(outliers_count),
            "outliers_sample": outliers.head(10).tolist(),
            "outliers_indices": outliers.head(10).index.tolist()
        }
        
        # Сохраняем результат в metrics
        if "outliers_iqr" not in self.metrics:
            self.metrics["outliers_iqr"] = {}
        self.metrics["outliers_iqr"][column] = results
        
        return results
                
    # ======= Постройте boxplot, показываем медиану, квартили и выбросы ========
    def boxplot_iqr(self, column: str, save_path: str=None):
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        numeric_data = pd.to_numeric(non_missing, errors='coerce').dropna()
        
        if len(numeric_data) == 0:
            print(f"Столбец '{column}' не содержит числовых данных для boxplot")
            return {}
        
        # Рассчитайте статистики
        Q1 = numeric_data.quantile(0.25)
        Q3 = numeric_data.quantile(0.75)
        IQR = Q3 - Q1
        median = numeric_data.median()
        # Определите значения вне границ [lower_bound, upper_bound]
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Настройка графика
        plt.figure(figsize=(8, 6))
        
        # boxplot через seaborn
        sns.boxplot(x=numeric_data, color='skyblue', width=0.6,
                   boxprops=dict(edgecolor='navy', linewidth=1.5),
                   medianprops=dict(color='red', linewidth=2.5),
                   whiskerprops=dict(color='navy', linestyle='--', linewidth=1.5),
                   capprops=dict(color='navy', linewidth=1.5),
                   flierprops=dict(marker='o', color='red', markersize=5, alpha=0.7, label='Выбросы'))
        
        # наглядно показывает медиану, квартили и выбросы
        plt.axvline(lower_bound, color='orange', linestyle=':', linewidth=1.5, 
                   label=f'Нижняя граница: {lower_bound:.2f}', alpha=0.8)
        plt.axvline(upper_bound, color='orange', linestyle=':', linewidth=1.5, 
                   label=f'Верхняя граница: {upper_bound:.2f}', alpha=0.8)
        plt.axvline(median, color='green', linestyle='-.', linewidth=1.5, 
                   label=f'Медиана: {median:.2f}', alpha=0.8)
        
        plt.title(f'Boxplot: {column}, метод IQR', 
                 fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Значение', fontsize=11)
        plt.ylabel('Распределение', fontsize=11)
        plt.legend(loc='best', fontsize=9)
        plt.grid(axis='x', linestyle=':', alpha=0.4)
        plt.tight_layout()
        
        # Сохранение
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Boxplot сохранён: {save_path}")
        
        plt.show()
        
    # boxplot для каждого столбца из списка
    def plot_boxplots_all(self, columns: list, save_dir: str = None):
        
        results = {}
        
        for col in columns:
            print(f'Строим boxplot: {col}')
                
            # путь для сохранения
            if save_dir:
                save_path = Path(save_dir) / f"boxplot_iqr_{col}.png"
            else:
                save_path = None
                
            # Строим график
            self.boxplot_iqr(col, save_path=str(save_path) if save_path else None)
            
            results[col] = save_path
        
        return results
    
    # 4. выбросы в числовом столбце методом Z-score
    def ident_outliers_zscore(self, column: str, threshold: float = 3.0) -> dict:
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        numeric_data = pd.to_numeric(non_missing, errors='coerce').dropna()
        
        if len(numeric_data) == 0:
            print(f"Столбец '{column}' не содержит числовых данных для Z-score")
            return {}
        
        # Рассчитайте статистики
        mean_val = numeric_data.mean()
        std_val = numeric_data.std()
        
        # Защита от деления на ноль
        if std_val == 0:
            print(f"Столбец '{column}' имеет нулевое стандартное отклонение")
            return {
                "column": column,
                "mean": round(mean_val, 2),
                "std": 0,
                "outlier_count": 0,
                "outliers_sample": [],
                "outliers_indices": []
            }
        
        # Считаем Z-score 
        z_scores = (numeric_data - mean_val) / std_val
        
        # Находим выбросы: |Z| > threshold
        outliers_mask = z_scores.abs() > threshold
        outliers = numeric_data[outliers_mask]
        outlier_z_scores = z_scores[outliers_mask]
        
        # Считаем метрики
        outlier_count = len(outliers)
        
        outliers_sample = list(zip(
            outliers.head(10).index.tolist(),
            outliers.head(10).tolist(),
            [round(z, 2) for z in outlier_z_scores.head(10).tolist()]
        ))
        
        # Формируем результат
        results = {
            "Column": column,
            "Mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "Threshold": threshold,
            "outlier_count": int(outlier_count),
            "outliers_sample": outliers_sample,
            "outliers_indices": outliers.head(10).index.tolist()
        }
        
        # Сохраняем результат в metrics
        if "outliers_zscore" not in self.metrics:
            self.metrics["outliers_zscore"] = {}
        self.metrics["outliers_zscore"][column] = results
        
        return results
    
    # ===== Сравнивает результаты IQR и Z-score ===============
    def compare_outlier_methods(self, column: str, iqr_result: dict, zscore_result: dict) -> dict:
        
        # Извлекаем индексы выбросов из результатов
        iqr_indices = set(iqr_result.get('outliers_indices', []))
        z_indices = set(zscore_result.get('outliers_indices', []))
        
        # Находим пересечения и различия
        both = iqr_indices & z_indices # Нашли ОБА метода
        only_iqr = iqr_indices - z_indices # Только IQR
        only_z = z_indices - iqr_indices # Только Z-score
        union = iqr_indices | z_indices # Все уникальные выбросы
        
        # метрики согласия
        total_checked = len(self.df[column].dropna())
        agreement_pct = (len(both) / len(union) * 100) if len(union) > 0 else 100
        
        # результат
        comparison = {
            "column": column,
            "total_values": total_checked,
            "iqr_only_count": len(only_iqr),
            "zscore_only_count": len(only_z),
            "both_count": len(both),
            "union_count": len(union),
            "agreement_pct": round(agreement_pct, 2),
            "samples": {
                "both": list(both)[:5], # первые 5 индексов
                "only_iqr": list(only_iqr)[:5],
                "only_z": list(only_z)[:5]
            }
        }
        
        return comparison
    
    # ========= Гистограмма с отмеченными границами ±3σ =========
    def histogram_zscore(self, column: str, save_path: str=None):
        
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        numeric_data = pd.to_numeric(non_missing, errors='coerce').dropna()
        
        if len(numeric_data) == 0:
            print(f"Столбец '{column}' не содержит числовых данных для гистограммы")
            return {}

        # Рассчитайте статистики
        mean_val = numeric_data.mean()
        std_val = numeric_data.std()
        
        # Границы ±3σ
        lower_3sigma = mean_val - 3 * std_val
        upper_3sigma = mean_val + 3 * std_val
        
        # График
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Гистограмма
        ax.hist(numeric_data, bins=30, density=True, alpha=0.7, 
               color='skyblue', edgecolor='black', label='Реальные данные', zorder=1)
        
        # Кривая нормального распределения
        x = np.linspace(numeric_data.min(), numeric_data.max(), 100)
        normal_curve = stats.norm.pdf(x, mean_val, std_val)
        ax.plot(x, normal_curve, 'r-', linewidth=2.5, label='Нормальное распределение', zorder=2)
        
        # Границы ±3σ
        ax.axvline(lower_3sigma, color='orange', linestyle='--', linewidth=2, 
                  label=f'−3σ: {lower_3sigma:.2f}', alpha=0.9, zorder=3)
        ax.axvline(upper_3sigma, color='orange', linestyle='--', linewidth=2, 
                  label=f'+3σ: {upper_3sigma:.2f}', alpha=0.9, zorder=3)
        
        # Среднее значение
        ax.axvline(mean_val, color='green', linestyle=':', linewidth=2, 
                  label=f'Среднее (μ): {mean_val:.2f}', alpha=0.9, zorder=3)
        
        # Область "нормы" между ±3σ
        x_fill = np.linspace(lower_3sigma, upper_3sigma, 100)
        ax.fill_between(x_fill, stats.norm.pdf(x_fill, mean_val, std_val), 
                       alpha=0.15, color='green', label='Норма (±3σ)', zorder=0)
        
        # Подписи
        ax.set_title(f'Гистограмма: {column}\nГраницы аномалий: Z-score = ±3σ', 
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Значение', fontsize=11)
        ax.set_ylabel('Плотность вероятности', fontsize=11)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        ax.grid(axis='y', linestyle=':', alpha=0.4)
        ax.set_axisbelow(True)  # Сетка
        
        # Статистика в угол графика
        stats_text = (f'Среднее μ = {mean_val:.2f}\n'
                     f'Стандартное отклонение σ = {std_val:.2f}\n'
                     f'Количество N = {len(numeric_data)}')
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        
        # Сохранение
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f'Гистограмма сохранена: {save_path}')
        
        plt.show()
        
    # Гистограмма для каждого столбца из списка
    def plot_histogram_zscore_all(self, columns: list, save_dir: str = None):
        
        results = {}
        
        for col in columns:
            print(f'Строим Гистограмму: {col}')
                
            # путь для сохранения
            if save_dir:
                save_path = Path(save_dir) / f"histogram_zscore_{col}.png"
            else:
                save_path = None
                
            # Строим график
            self.histogram_zscore(col, save_path=str(save_path) if save_path else None)
            
            results[col] = save_path
        
        return results
    
    # ========== Создайте таблицу сравнения методов IQR vs Z-score ========
    def create_comparison_table(self, comparison_results: list) -> pd.DataFrame:
        
        table_data = []
        
        for comp in comparison_results:
            col = comp["column"]
            iqr_total = comp["iqr_only_count"] + comp["both_count"]
            z_total = comp["zscore_only_count"] + comp["both_count"]
            
            # статус согласия
            if comp["agreement_pct"] >= 70:
                status = "Высокое"
            elif comp["agreement_pct"] >= 40:
                status = "Умеренное"
            else:
                status = "Низкое"
            # print(f'{status} согласие')
                
            # результат
            table_data.append({
                "Столбец": col,
                "Только IQR": iqr_total,
                "Только Z-score": z_total,
                "Общие выбросы": comp["both_count"],
                "Различия": comp["union_count"],
                "Статус": status
            })
            
        return pd.DataFrame(table_data)
    
    # ========== Сохраняет таблицу сравнения методов IQR vs Z-score в txt ===========
    def save_comparison_table(self, comparison_df: pd.DataFrame, save_path: str):
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        txt_path = save_path + '.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("Сравнительный анализ: IQR vs Z-score\n")
            f.write(comparison_df.to_string(index=False) + "\n")
        
        print(f"Таблица сохранена: {txt_path}")
        
    # 5. Актуальность данных   
    def calc_timeliness(self, date_column: str, reference_date: datetime = None) -> dict:
        
        if reference_date is None:
            reference_date = datetime.today()
        
        column = date_column
        total_records = len(self.df)
        
        # Конвертируем значения в даты
        dates = pd.to_datetime(self.df[column], errors='coerce')
        
        # Считаем статистику  
        valid_dates = dates.dropna()
        invalid_dates_count = total_records - len(valid_dates)

        # актуальность даты
        is_timely = dates <= reference_date
        timely_count = is_timely.sum()
        
        # Нет ли дат регистрации из будущего
        future_mask = (dates > reference_date) & (dates.notna())
        future_recs = self.df[future_mask][column].head(10)
        
        # Считаем метрику
        timeliness_pct = (timely_count / total_records) * 100 if total_records > 0 else 0
        
        results = {
            "column": column,
            "total_records": total_records,
            "valid_dates": len(valid_dates),
            "invalid_dates": int(invalid_dates_count),
            "timely_records": int(timely_count),
            "future_records": int(future_mask.sum()),
            "timeliness_%": round(timeliness_pct, 2),
            "reference_date": reference_date.date(),
            "future_samples": future_recs.tolist()
        }
    
        # Сохраняем результат в metrics
        if "timeliness" not in self.metrics:
            self.metrics["timeliness"] = {}
        self.metrics["timeliness"][column] = results
        
        return results
    
    