import pandas as pd

# Класс , который хранит данные и проводит расчеты.
class DataQualityAnalyzer:

    def __init__(self, df: pd.DataFrame):
        # Копируем данные, чтобы не сломать исходный файл случайными изменениями
        self.df = df.copy()
        self.metrics = {}   # Сюда складываем результаты расчетов
    
    # считаем полноту
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
            completeness_pct = (count_filled / total_rows) * 100
            
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