"""
GRUAN Radiosonde Data Acquisition and Visualization Tool
=========================================================
Полнофункциональный инструмент для загрузки и анализа данных GRUAN RS92-GDP
Использует библиотеку pycontrails для работы с данными GRUAN Network

Установка зависимостей:
pip install pycontrails xarray netCDF4 pandas matplotlib numpy
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from pycontrails.datalib.gruan import GRUAN
    PYCONTRAILS_AVAILABLE = True
except ImportError:
    PYCONTRAILS_AVAILABLE = False
    print("⚠️  pycontrails не установлен. Установите: pip install pycontrails")


class GRUANDataManager:
    """
    Менеджер для работы с данными GRUAN (GCOS Reference Upper-Air Network).
    
    Поддерживает:
    - RS92-GDP.2 (основной продукт Vaisala RS92)
    - RS92-GDP.1 (старая версия)
    - RS41-EDT.1 (новый Vaisala RS41)
    - RS-11G-GDP.1 (Meisei RS-11G)
    """
    
    def __init__(self, product: str = "RS92-GDP.2", cache_dir: str = "./gruan_cache"):
        """
        Инициализация менеджера GRUAN данных.
        
        Args:
            product: Продукт GRUAN (RS92-GDP.2, RS92-GDP.1, RS41-EDT.1, RS-11G-GDP.1)
            cache_dir: Директория для кэширования загруженных файлов
        """
        if not PYCONTRAILS_AVAILABLE:
            raise ImportError("Установите pycontrails: pip install pycontrails")
        
        self.product = product
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Информация о доступных станциях
        self.available = GRUAN.AVAILABLE
        
        # Станции для выбранного продукта
        self.available_sites = self.available.get(product, [])
        
        # Информация о станциях GRUAN
        self.station_info = {
            'LIN': {'name': 'Lindenberg', 'country': 'Germany', 'lat': 52.21, 'lon': 14.12},
            'NYA': {'name': 'Ny-Ålesund', 'country': 'Norway', 'lat': 78.93, 'lon': 11.93},
            'TAT': {'name': 'Tateno', 'country': 'Japan', 'lat': 36.06, 'lon': 140.13},
            'SOD': {'name': 'Sodankylä', 'country': 'Finland', 'lat': 67.37, 'lon': 26.63},
            'PAY': {'name': 'Payerne', 'country': 'Switzerland', 'lat': 46.49, 'lon': 6.57},
            'LAU': {'name': 'Lauder', 'country': 'New Zealand', 'lat': -45.04, 'lon': 169.68},
            'BOU': {'name': 'Boulder', 'country': 'USA', 'lat': 40.04, 'lon': -105.24},
            'CAB': {'name': 'Cabauw', 'country': 'Netherlands', 'lat': 51.97, 'lon': 4.93},
            'POT': {'name': 'Potenza', 'country': 'Italy', 'lat': 40.60, 'lon': 15.72},
            'NAU': {'name': 'Nauru', 'country': 'Nauru', 'lat': -0.52, 'lon': 166.92},
            'MAN': {'name': 'Manus', 'country': 'Papua New Guinea', 'lat': -2.06, 'lon': 147.43},
            'DAR': {'name': 'Darwin', 'country': 'Australia', 'lat': -12.43, 'lon': 130.89},
            'BAR': {'name': 'Barrow', 'country': 'USA', 'lat': 71.32, 'lon': -156.61},
            'BEL': {'name': 'Beltsville', 'country': 'USA', 'lat': 39.05, 'lon': -76.88},
            'GRA': {'name': 'Graciosa', 'country': 'Portugal', 'lat': 39.09, 'lon': -28.03},
            'REU': {'name': 'Reunion', 'country': 'France', 'lat': -21.08, 'lon': 55.38},
            'SGP': {'name': 'Southern Great Plains', 'country': 'USA', 'lat': 36.61, 'lon': -97.49},
            'SYO': {'name': 'Syowa', 'country': 'Antarctica', 'lat': -69.01, 'lon': 39.59},
            'TEN': {'name': 'Tenerife', 'country': 'Spain', 'lat': 28.32, 'lon': -16.38},
            'GVN': {'name': 'Greifswald', 'country': 'Germany', 'lat': 54.10, 'lon': 13.40},
            'SNG': {'name': 'Singapore', 'country': 'Singapore', 'lat': 1.37, 'lon': 103.98}
        }
        
        self.gruan_instances = {}
    
    def list_available_products(self) -> Dict[str, List[str]]:
        """Показать все доступные продукты и станции."""
        return self.available
    
    def list_stations(self) -> pd.DataFrame:
        """Получить список доступных станций для выбранного продукта."""
        stations_data = []
        for site_code in self.available_sites:
            info = self.station_info.get(site_code, {})
            stations_data.append({
                'Код': site_code,
                'Название': info.get('name', 'N/A'),
                'Страна': info.get('country', 'N/A'),
                'Широта': info.get('lat', np.nan),
                'Долгота': info.get('lon', np.nan)
            })
        return pd.DataFrame(stations_data)
    
    def get_gruan(self, site: str) -> GRUAN:
        """Получить или создать экземпляр GRUAN для станции."""
        if site not in self.gruan_instances:
            if site not in self.available_sites:
                raise ValueError(f"Станция {site} недоступна для продукта {self.product}")
            self.gruan_instances[site] = GRUAN(self.product, site)
        return self.gruan_instances[site]
    
    def list_years(self, site: str) -> List[int]:
        """Получить список доступных лет для станции."""
        gruan = self.get_gruan(site)
        return gruan.years()
    
    def list_files(self, site: str, year: int, month: Optional[int] = None) -> List[str]:
        """
        Получить список файлов для станции и периода.
        
        Args:
            site: Код станции (например, 'LIN')
            year: Год
            month: Месяц (опционально, для фильтрации)
        
        Returns:
            Список имен файлов NetCDF
        """
        gruan = self.get_gruan(site)
        files = gruan.list_files(year)
        
        if month is not None:
            month_str = f"{year}{month:02d}"
            files = [f for f in files if month_str in f]
        
        return sorted(files)
    
    def download_file(self, site: str, filename: str, show_info: bool = True) -> xr.Dataset:
        """
        Скачать и открыть файл GRUAN.
        
        Args:
            site: Код станции
            filename: Имя файла
            show_info: Показать информацию о файле
        
        Returns:
            xarray.Dataset с данными профиля
        """
        gruan = self.get_gruan(site)
        ds = gruan.get(filename)
        
        if show_info:
            self._print_file_info(ds, filename)
        
        return ds
    
    def download_period(self, site: str, start_date: datetime, end_date: datetime, 
                       hours: List[int] = [0, 6, 12, 18]) -> List[xr.Dataset]:
        """
        Скачать все зондирования за период.
        
        Args:
            site: Код станции
            start_date: Начальная дата
            end_date: Конечная дата
            hours: Часы запусков UTC (по умолчанию синоптические сроки)
        
        Returns:
            Список Dataset'ов
        """
        gruan = self.get_gruan(site)
        datasets = []
        
        # Получаем все файлы за нужные годы
        years = range(start_date.year, end_date.year + 1)
        all_files = []
        for year in years:
            all_files.extend(gruan.list_files(year))
        
        # Фильтруем по дате и часам
        for file in all_files:
            file_dt = self._extract_datetime_from_filename(file)
            if file_dt and start_date <= file_dt <= end_date and file_dt.hour in hours:
                try:
                    ds = gruan.get(file)
                    datasets.append(ds)
                    print(f"✓ Загружен: {file}")
                except Exception as e:
                    print(f"✗ Ошибка при загрузке {file}: {e}")
        
        return datasets
    
    def _extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """Извлечь дату из имени файла GRUAN."""
        try:
            # Формат: SITE-RS-XX_Y_PRODUCT_VVV_YYYYMMDDThhmmss_Z-ZZZ-ZZZ.nc
            parts = filename.split('_')
            datetime_str = parts[3]  # YYYYMMDDThhmmss
            return datetime.strptime(datetime_str, "%Y%m%dT%H%M%S")
        except:
            return None
    
    def _print_file_info(self, ds: xr.Dataset, filename: str):
        """Вывести информацию о файле."""
        print(f"\n{'='*70}")
        print(f"Файл: {filename}")
        print(f"{'='*70}")
        print(f"Станция: {ds.attrs.get('g.General.SiteCode', 'N/A')}")
        print(f"Дата: {ds.attrs.get('g.Ascent.StandardTime', 'N/A')}")
        print(f"Инструмент: {ds.attrs.get('g.Instrument.TypeFamily', 'N/A')}")
        print(f"Производитель: {ds.attrs.get('g.Instrument.Manufacturer', 'N/A')}")
        print(f"\nПараметры:")
        print(f"  - Количество точек профиля: {len(ds.time)}")
        print(f"  - Диапазон давления: {ds['press'].values.min():.1f} - {ds['press'].values.max():.1f} hPa")
        print(f"  - Диапазон высоты: {ds['alt'].values.min():.0f} - {ds['alt'].values.max():.0f} м")
        print(f"  - Диапазон температуры: {ds['temp'].values.min():.1f} - {ds['temp'].values.max():.1f} K")
        print(f"{'='*70}\n")
    
    def plot_profile(self, ds: xr.Dataset, variables: List[str] = ['temp', 'rh', 'wspeed'],
                    pressure_levels: bool = True, save_path: Optional[str] = None):
        """
        Построить вертикальные профили.
        
        Args:
            ds: Dataset с данными
            variables: Список переменных для отображения
            pressure_levels: Использовать давление как ось Y (иначе высота)
            save_path: Путь для сохранения графика
        """
        n_vars = len(variables)
        fig, axes = plt.subplots(1, n_vars, figsize=(5*n_vars, 8))
        
        if n_vars == 1:
            axes = [axes]
        
        y_coord = 'press' if pressure_levels else 'alt'
        y_label = 'Давление (hPa)' if pressure_levels else 'Высота (м)'
        
        var_labels = {
            'temp': 'Температура (K)',
            'rh': 'Относительная влажность',
            'wspeed': 'Скорость ветра (м/с)',
            'wdir': 'Направление ветра (град)',
            'geopot': 'Геопотенциальная высота (м)'
        }
        
        for i, var in enumerate(variables):
            if var in ds:
                axes[i].plot(ds[var], ds[y_coord])
                axes[i].set_xlabel(var_labels.get(var, var))
                axes[i].set_ylabel(y_label if i == 0 else '')
                axes[i].grid(True, alpha=0.3)
                
                if pressure_levels:
                    axes[i].invert_yaxis()
                    axes[i].set_yscale('log')
                    axes[i].set_ylim(1000, max(1, ds[y_coord].min()))
        
        site_code = ds.attrs.get('g.General.SiteCode', 'Unknown')
        ascent_time = ds.attrs.get('g.Ascent.StandardTime', 'Unknown')
        plt.suptitle(f'GRUAN Профиль: {site_code} - {ascent_time}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"График сохранен: {save_path}")
        
        plt.show()
    
    def export_to_csv(self, ds: xr.Dataset, output_path: str, 
                     variables: Optional[List[str]] = None):
        """
        Экспорт данных в CSV.
        
        Args:
            ds: Dataset с данными
            output_path: Путь для сохранения CSV
            variables: Список переменных (если None, экспортируются все основные)
        """
        if variables is None:
            variables = ['press', 'temp', 'rh', 'wdir', 'wspeed', 'alt', 'geopot']
        
        # Создаем DataFrame
        df_data = {'time': ds['time'].values}
        df_data['lat'] = ds['lat'].values
        df_data['lon'] = ds['lon'].values
        
        for var in variables:
            if var in ds:
                df_data[var] = ds[var].values
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False)
        print(f"✓ Данные экспортированы в: {output_path}")


def interactive_mode():
    """Интерактивный режим работы с GRUAN данными."""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║       GRUAN Data Acquisition Tool v1.0                         ║
    ║       Инструмент загрузки данных GRUAN радиозондов             ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    if not PYCONTRAILS_AVAILABLE:
        print("❌ Ошибка: pycontrails не установлен!")
        print("Установите: pip install pycontrails")
        return
    
    # Выбор продукта
    print("\n📋 Доступные продукты GRUAN:")
    manager = GRUANDataManager()
    products = manager.list_available_products()
    for i, product in enumerate(products.keys(), 1):
        print(f"  {i}. {product}")
    
    product_choice = input(f"\nВыберите продукт (1-{len(products)}) [по умолчанию RS92-GDP.2]: ").strip()
    if product_choice.isdigit() and 1 <= int(product_choice) <= len(products):
        selected_product = list(products.keys())[int(product_choice) - 1]
    else:
        selected_product = "RS92-GDP.2"
    
    print(f"\n✓ Выбран продукт: {selected_product}")
    manager = GRUANDataManager(product=selected_product)
    
    # Показать доступные станции
    print("\n🌍 Доступные станции:")
    stations_df = manager.list_stations()
    print(stations_df.to_string(index=False))
    
    # Выбор станции
    site = input("\n📍 Введите код станции (например, LIN): ").strip().upper()
    if site not in manager.available_sites:
        print(f"❌ Станция {site} недоступна для продукта {selected_product}")
        return
    
    # Показать доступные годы
    years = manager.list_years(site)
    print(f"\n📅 Доступные годы для {site}: {years[0]} - {years[-1]}")
    
    # Выбор периода
    year = int(input("Введите год: ").strip())
    month = input("Введите месяц (1-12) или Enter для всего года: ").strip()
    month = int(month) if month else None
    
    # Получить список файлов
    files = manager.list_files(site, year, month)
    print(f"\n📂 Найдено файлов: {len(files)}")
    
    if len(files) == 0:
        print("Нет доступных файлов для выбранного периода")
        return
    
    # Показать первые 10 файлов
    print("\nПримеры файлов:")
    for i, f in enumerate(files[:10], 1):
        file_dt = manager._extract_datetime_from_filename(f)
        print(f"  {i}. {file_dt.strftime('%Y-%m-%d %H:%M') if file_dt else f}")
    
    # Действия
    print("\n⚙️  Выберите действие:")
    print("  1. Загрузить и просмотреть один файл")
    print("  2. Загрузить все файлы за период")
    print("  3. Построить графики профиля")
    print("  4. Экспортировать в CSV")
    
    action = input("Действие (1-4): ").strip()
    
    if action == "1":
        # Загрузить один файл
        file_idx = int(input(f"Номер файла (1-{min(10, len(files))}): ").strip()) - 1
        filename = files[file_idx]
        ds = manager.download_file(site, filename, show_info=True)
        
        # Построить график
        if input("\nПостроить график? (y/n): ").lower() == 'y':
            manager.plot_profile(ds)
    
    elif action == "2":
        # Загрузить все за период
        start_date = datetime(year, month if month else 1, 1)
        if month:
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, 12, 31, 23, 59, 59)
        
        datasets = manager.download_period(site, start_date, end_date)
        print(f"\n✓ Загружено профилей: {len(datasets)}")
    
    elif action == "3":
        # График первого файла
        filename = files[0]
        ds = manager.download_file(site, filename, show_info=True)
        
        vars_input = input("\nПеременные для графика (через запятую) [temp,rh,wspeed]: ").strip()
        variables = [v.strip() for v in vars_input.split(',')] if vars_input else ['temp', 'rh', 'wspeed']
        
        manager.plot_profile(ds, variables=variables)
    
    elif action == "4":
        # Экспорт в CSV
        filename = files[0]
        ds = manager.download_file(site, filename, show_info=False)
        
        output_path = f"gruan_{site}_{year}_{month if month else 'all'}.csv"
        manager.export_to_csv(ds, output_path)
    
    print("\n✅ Готово!")


# ============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ В СКРИПТЕ
# ============================================================================

def example_usage():
    """Пример использования для автоматизации."""
    
    # Инициализация менеджера
    manager = GRUANDataManager(product="RS92-GDP.2", cache_dir="./gruan_data")
    
    # 1. Показать доступные станции
    print("Доступные станции:")
    print(manager.list_stations())
    
    # 2. Выбрать станцию и посмотреть доступные годы
    site = "LIN"  # Lindenberg, Germany
    years = manager.list_years(site)
    print(f"\nСтанция {site}, доступные годы: {years}")
    
    # 3. Получить файлы за январь 2020
    files = manager.list_files(site, year=2020, month=1)
    print(f"\nФайлы за январь 2020: {len(files)}")
    
    # 4. Загрузить один файл
    if files:
        ds = manager.download_file(site, files[0])
        
        # 5. Построить профиль
        manager.plot_profile(ds, variables=['temp', 'rh', 'wspeed'])
        
        # 6. Экспортировать в CSV
        manager.export_to_csv(ds, "gruan_profile_example.csv")
    
    # 7. Загрузить все зондирования за период
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 7)
    datasets = manager.download_period(site, start, end)
    print(f"\nЗагружено профилей: {len(datasets)}")


if __name__ == "__main__":
    # Запустить в интерактивном режиме
    interactive_mode()
    
    # Или использовать функцию example_usage() для автоматизации
    # example_usage()
