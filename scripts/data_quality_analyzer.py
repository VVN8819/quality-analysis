import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import re

# Класс , который хранит данные и проводит расчеты.
class DataQualityAnalyzer:

    def __init__(self, df: pd.DataFrame):
        # Копируем данные, чтобы не сломать исходный файл случайными изменениями
        self.df = df.copy()
        self.metrics = {}   # Сюда складываем результаты расчетов
    
    # считаем полноту и визуализируем результаты
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
    
    # считаем точность
    def calculate_accuracy(self) -> pd.DataFrame:
        
        column = 'email'
        results = []
        
        # исключаем пропуски из знаменателя
        non_missing = self.df[column].dropna()
        total_valid = len(non_missing)
        
        # правила корректности: email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Проверяем на соответствие паттерну
        def is_valid_email(value):
            # должна быть строка и =email_pattern
            if not isinstance(value, str):
                return False
            return bool(re.match(email_pattern, value.strip()))
        
        # проверка всех непустых на email_pattern
        validate_results = non_missing.apply(is_valid_email)
        
        validated_count = validate_results.sum() # прошли проверку
        invalid_count = total_valid - validated_count # не прошли проверку
        accuracy_pct = (validated_count / total_valid) * 100 if total_valid > 0 else 0
        
        results.append({
            "Column": column,
            "Rule": 'Contains @ and valid domain',
            "Total_valid_non_missing": total_valid,
            "Validated_count": int(validated_count),
            "Invalid_count": int(invalid_count),
            "Accuracy_%": round(accuracy_pct, 2)
        })
        
        self.metrics["accuracy"] = pd.DataFrame(results)
        return self.metrics["accuracy"]