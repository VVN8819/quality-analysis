# data_quality_analyzer.py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import re
from datetime import datetime

# Класс , который хранит данные и проводит расчеты.
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
            print(f"Столбец '{column}' не содержит числовых данных")
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
            print(f"Столбец '{column}' не содержит числовых данных")
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