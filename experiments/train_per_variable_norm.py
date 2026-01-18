"""
FINAL CORRECT version with PER-VARIABLE normalization.
Each variable (T, RH, Z, U, V) normalized separately.
Uses RELATIVE HUMIDITY (r) instead of specific humidity (q).
Enhanced with flexible temporal downloading parameters.
Supports both ERA5 and MERRA2 data sources with extension to 0.1 hPa.
"""
import warnings
warnings.filterwarnings('ignore')

import resource
import os
import json
import numpy as np
import xarray as xr
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from datetime import datetime
from pathlib import Path
import torch.backends.cudnn as cudnn
from torch.cuda.amp import autocast, GradScaler  # Mixed precision
# from model_architecture import AtmosphericProfileResNet
from model_architecture import  create_model, PhysicsInformedLoss


# ============================================================================
# ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ ЗАГРУЗКИ ДАННЫХ
# ============================================================================

# ВЫБОР ИСТОЧНИКА ДАННЫХ: 'ERA5' или 'MERRA2'
DATA_SOURCE = 'MERRA2'  # Переключите на 'MERRA2' для использования MERRA-2

# Временной диапазон загрузки
DOWNLOAD_YEARS = list(range(2015, 2021))  # 2015-2020

# Определение сезонных месяцев
SEASONAL_MONTHS = {
    'winter': ['12','01', '02'],      # Зимние месяцы
    'spring': ['03','04', '05'],      # Весенние месяцы
    'summer': ['06','07', '08'],      # Летние месяцы
    'autumn': ['09','10', '11']       # Осенние месяцы
}

# Выбор сезонов для загрузки (можно изменить)
SEASONS_TO_DOWNLOAD = ['winter', 'spring', 'summer', 'autumn']

# Временные срезы в сутках (часы UTC)
TIME_SLICES = ['00:00', '12:00']

# Пространственное разрешение (опционально для уменьшения объема)
SPATIAL_AREA = [90, -180, -90, 180]  # [North, West, South, East]

# Уровни давления (hPa) - расширены до 0.1 гПа для обоих источников
# ERA5 поддерживает уровни от 1000 до 1 гПа в стандартной конфигурации
# Расширение до 0.1 гПа может потребовать специального запроса или недоступно
PRESSURE_LEVELS_ERA5 = [
    '1', '2', '3', '5', '7', '10', '20', '30', '50', '70', '100',
    '125', '150', '175', '200', '225', '250', '300', '350', '400',
    '450', '500', '550', '600', '650', '700', '750', '775', '800',
    '825', '850', '875', '900', '925', '950', '975', '1000'
]
# Примечание: ERA5 может иметь ограниченную доступность уровней выше 1 гПа.
# Для полного диапазона до 0.1 гПа используйте MERRA2.

# MERRA2 изобарические уровни (42 уровня, включая 0.1 гПа)
PRESSURE_LEVELS_MERRA2 = [
    1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 725, 700,
    650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100,
    70, 50, 40, 30, 20, 10, 7, 5, 4, 3, 2, 1, 0.7, 0.5, 0.4, 0.3, 0.1
]

BATCH_SIZE = 128
MAX_EPOCHS = 150

# Extended pressure levels to 0.1 hPa for both sources
# Input levels: troposphere (1000-100 hPa)
INPUT_LEVELS = [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750,
                700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]  # 24 levels

# Output levels: stratosphere and mesosphere (70-0.1 hPa)
OUTPUT_LEVELS = [70, 50, 40, 30, 20, 10, 7, 5, 4, 3, 2, 1, 0.7, 0.5, 0.4, 0.3, 0.1]  # 17 levels

# Метеорологические переменные ERA5
VARIABLES_ERA5 = [
    'geopotential',           # Z - геопотенциальная высота
    'temperature',            # T - температура воздуха
    'u_component_of_wind',    # U - зональная компонента ветра
    'v_component_of_wind',    # V - меридиональная компонента ветра
    'relative_humidity',      # RH - относительная влажность
]

# Метеорологические переменные MERRA2 (соответствие с ERA5)
VARIABLES_MERRA2 = {
    'H': 'geopotential',      # Z - геопотенциальная высота (будет преобразована)
    'T': 'temperature',       # T - температура воздуха
    'U': 'u_component_of_wind',     # U - зональная компонента ветра
    'V': 'v_component_of_wind',     # V - меридиональная компонента ветра
    'RH': 'relative_humidity',      # RH - относительная влажность
}

# Конфигурация MERRA2 OPeNDAP
MERRA2_CONFIG = {
    'collection': 'M2I3NPASM',  # Изобарические уровни, 3-часовые мгновенные данные
    'server': 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap',
    'path': 'MERRA2/M2I3NPASM.5.12.4',
    'stream': 400  # Номер потока обработки
}


def download_merra2_https(
    output_dir='./data/merra2',
    years=None,
    seasons=None,
    time_slices=None,
    days_per_month=None,
    day_step=10,
    skip_existing=True
):
    """
    Загрузка данных реанализа MERRA-2 через HTTPS (прямое скачивание).

    ВАЖНО: NASA GES DISC изменила метод доступа - теперь используется прямое
    скачивание файлов через HTTPS вместо OPeNDAP для индивидуальных файлов.

    Parameters
    ----------
    output_dir : str
        Директория для сохранения загруженных файлов NetCDF
    years : list of int, optional
        Список годов для загрузки. По умолчанию используется DOWNLOAD_YEARS
    seasons : list of str, optional
        Список сезонов из SEASONAL_MONTHS. По умолчанию SEASONS_TO_DOWNLOAD
    time_slices : list of str, optional
        Временные срезы в формате 'HH:MM'. По умолчанию TIME_SLICES
    days_per_month : int, optional
        Количество дней для загрузки в каждом месяце (1-31).
        None означает загрузку всех дней месяца с учетом day_step
    day_step : int
        Шаг выборки дней (1 = все дни, 10 = каждый 10-й день и т.д.)
    skip_existing : bool
        Пропускать ли существующие файлы

    Returns
    -------
    bool
        True при успешной загрузке, False при критических ошибках
    """
    import subprocess
    import sys
    import requests

    print("\n" + "="*80)
    print("ЗАГРУЗКА ДАННЫХ MERRA-2 ЧЕРЕЗ HTTPS (ПРЯМОЕ СКАЧИВАНИЕ)")
    print("="*80)
    print("\n⚠ ВАЖНО: Для доступа к MERRA-2 требуется настройка ~/.netrc")
    print("   Файл ~/.netrc должен содержать:")
    print("   machine urs.earthdata.nasa.gov")
    print("       login YOUR_USERNAME")
    print("       password YOUR_PASSWORD")
    print("   Установите права: chmod 600 ~/.netrc")
    print("="*80)

    # Проверка ~/.netrc и чтение credentials
    netrc_path = Path.home() / '.netrc'
    if not netrc_path.exists():
        print("\n✗ ОШИБКА: Файл ~/.netrc не найден!")
        print("   Зарегистрируйтесь на https://urs.earthdata.nasa.gov/users/new")
        print("   и создайте ~/.netrc с учетными данными")
        return False

    # Читаем credentials из .netrc
    username = None
    password = None
    try:
        with open(netrc_path, 'r') as f:
            for line in f:
                if 'login' in line:
                    username = line.split()[1]
                if 'password' in line:
                    password = line.split()[1]

        if not username or not password:
            print("\n✗ ОШИБКА: Не удалось прочитать credentials из ~/.netrc")
            return False

        print(f"\n✓ Credentials найдены для пользователя: {username}")

    except Exception as e:
        print(f"\n✗ ОШИБКА чтения ~/.netrc: {e}")
        return False

    # Создаем HTTP session с аутентификацией
    session = requests.Session()
    session.auth = (username, password)

    # Использование глобальных параметров
    if years is None:
        years = DOWNLOAD_YEARS
    if seasons is None:
        seasons = SEASONS_TO_DOWNLOAD
    if time_slices is None:
        time_slices = TIME_SLICES

    if day_step < 1:
        print(f"ПРЕДУПРЕЖДЕНИЕ: day_step={day_step} некорректен. Установлен day_step=1")
        day_step = 1

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Формирование списка месяцев
    months_to_download = []
    for season in seasons:
        if season in SEASONAL_MONTHS:
            months_to_download.extend(SEASONAL_MONTHS[season])
        else:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Неизвестный сезон '{season}', пропускается")

    months_to_download = sorted(list(set(months_to_download)))

    # Конвертация TIME_SLICES в часы для MERRA2 (MERRA2 использует часы UTC: 0,3,6,9,12,15,18,21)
    merra2_hours = []
    for ts in time_slices:
        hour = int(ts.split(':')[0])
        # MERRA2 3-часовые данные: выбираем ближайший доступный час
        available_hours = [0, 3, 6, 9, 12, 15, 18, 21]
        closest_hour = min(available_hours, key=lambda x: abs(x - hour))
        if closest_hour not in merra2_hours:
            merra2_hours.append(closest_hour)

    print(f"\nГоды:      {years[0]}-{years[-1]} ({len(years)} лет)")
    print(f"Сезоны:    {', '.join(seasons)}")
    print(f"Месяцы:    {', '.join(months_to_download)}")
    print(f"Шаг по дням: {day_step}")
    print(f"Переменные: {len(VARIABLES_MERRA2)} ({', '.join(VARIABLES_MERRA2.keys())})")
    print(f"Уровни:    {len(PRESSURE_LEVELS_MERRA2)} изобарических (до 0.1 гПа)")
    print(f"Временные срезы: {merra2_hours} UTC")
    print(f"Выходная директория: {output_dir}")
    print("="*80)

    total_files = 0
    downloaded_files = 0
    skipped_files = 0
    error_files = 0

    # Итерация по годам и месяцам
    for year in years:
        for month in months_to_download:
            month_int = int(month)

            # Определение количества дней в месяце
            if month_int in [1, 3, 5, 7, 8, 10, 12]:
                max_days = 31
            elif month_int in [4, 6, 9, 11]:
                max_days = 30
            elif month_int == 2:
                max_days = 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
            else:
                max_days = 31

            if days_per_month is not None:
                num_days = min(days_per_month, max_days)
            else:
                num_days = max_days

            days = list(range(1, num_days + 1, day_step))

            print(f"\n{year}-{month}: загрузка дней {days[:5]}{'...' if len(days) > 5 else ''}")

            for day in days:
                total_files += 1
                output_file = f'{output_dir}/merra2_pl_{year}{month}{day:02d}.nc'

                if skip_existing and os.path.exists(output_file):
                    skipped_files += 1
                    if total_files % 10 == 0:
                        print(f"[{total_files}] Существует: {year}-{month}-{day:02d}")
                    continue

                print(f"[{total_files}] Загрузка: {year}-{month}-{day:02d}...")

                try:
                    # Формирование URL для HTTPS скачивания
                    # Формат: https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2I3NPASM.5.12.4/YEAR/MONTH/FILENAME.nc4
                    date_str = f"{year}{month}{day:02d}"
                    filename = f"MERRA2_{MERRA2_CONFIG['stream']}.inst3_3d_asm_Np.{date_str}.nc4"
                    url = f"https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2I3NPASM.5.12.4/{year}/{month}/{filename}"

                    # Временный файл для скачивания
                    temp_file = f"{output_file}.tmp"

                    # Скачивание через requests с аутентификацией
                    print(f"  Скачивание {filename}...")
                    response = session.get(url, stream=True, allow_redirects=True, timeout=300)

                    if response.status_code != 200:
                        error_files += 1
                        print(f"  ✗ ОШИБКА HTTP {response.status_code}: {response.reason}")
                        continue

                    # Получаем размер файла
                    total_size = int(response.headers.get('content-length', 0))
                    print(f"  Размер: {total_size / (1024*1024):.2f} MB")

                    # Скачиваем с прогресс-баром
                    downloaded = 0
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:  # Каждые 10 MB
                                    progress = (downloaded / total_size) * 100
                                    print(f"  Прогресс: {progress:.1f}%", end='\r')

                    print(f"  Скачано: 100%         ")

                    # Открыть скачанный файл и выполнить субсетирование
                    try:
                        ds = xr.open_dataset(
                            temp_file, 
                            decode_times=False,
                            engine='h5netcdf',     # Для HDF5 файлов MERRA-2
                            invalid_netcdf=True    # Разрешить нестандартные файлы
                        )
                    except Exception as e_h5:
                        # Fallback на netcdf4
                        try:
                            ds = xr.open_dataset(
                                temp_file, 
                                decode_times=False,
                                engine='netcdf4'
                            )
                        except Exception as e_nc4:
                            raise RuntimeError(f"Не удалось открыть файл ни h5netcdf, ни netcdf4. Ошибки: h5={str(e_h5)[:100]}, nc4={str(e_nc4)[:100]}")

                    # Выбор нужных переменных и уровней
                    var_list = list(VARIABLES_MERRA2.keys())

                    # Определение имени вертикальной координаты
                    vert_coord = 'lev' if 'lev' in ds.dims else 'level'

                    # Выбор временных срезов (индексы для merra2_hours)
                    time_indices = []
                    for hour in merra2_hours:
                        # MERRA2 3-часовые данные: 8 временных срезов в день
                        time_idx = hour // 3
                        if time_idx < len(ds.time):
                            time_indices.append(time_idx)

                    # Субсетирование данных
                    ds_subset = ds[var_list].isel(time=time_indices)
                    # Используем method='nearest' для работы с float32 уровнями MERRA2
                    ds_subset = ds_subset.sel({vert_coord: PRESSURE_LEVELS_MERRA2}, method='nearest')

                    # Загрузка в память
                    ds_subset.load()

                    # Переименование переменных для соответствия ERA5
                    rename_dict = {k: v for k, v in VARIABLES_MERRA2.items() if k in ds_subset}
                    ds_subset = ds_subset.rename(rename_dict)

                    # Преобразование геопотенциальной высоты (H в метрах) в геопотенциал (умножить на g)
                    if 'geopotential' in ds_subset:
                        ds_subset['geopotential'] = ds_subset['geopotential'] * 9.80665
                        ds_subset['geopotential'].attrs['units'] = 'm**2 s**-2'
                        ds_subset['geopotential'].attrs['long_name'] = 'Geopotential'

                    # Сохранение обработанного файла
                    ds_subset.to_netcdf(output_file)
                    downloaded_files += 1
                    print(f"  ✓ Загружено успешно: {output_file}")

                    # Закрытие и удаление временного файла
                    ds.close()
                    ds_subset.close()
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

                except requests.exceptions.Timeout:
                    error_files += 1
                    print(f"  ✗ ОШИБКА: Таймаут при загрузке")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    continue
                except requests.exceptions.RequestException as e:
                    error_files += 1
                    print(f"  ✗ ОШИБКА HTTP запроса: {str(e)[:200]}")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    continue
                except Exception as e:
                    error_files += 1
                    print(f"  ✗ ОШИБКА при обработке: {str(e)[:200]}")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    continue

    print("\n" + "="*80)
    print("ЗАГРУЗКА MERRA-2 ЗАВЕРШЕНА")
    print("="*80)
    print(f"Всего файлов:          {total_files}")
    print(f"Загружено новых:       {downloaded_files}")
    print(f"Пропущено (существ.):  {skipped_files}")
    print(f"Ошибок:                {error_files}")
    print("="*80)

    return True


# ============================================================================
# Остальной код остается без изменений
# ============================================================================

class AtmosphericDatasetPerVarNorm(Dataset):
    """
    Dataset with PER-VARIABLE normalization.
    Supports both ERA5 and MERRA2 data sources with extension to 0.1 hPa.
    """

    def __init__(self, data_files, input_levels, output_levels, stats=None, data_source='ERA5'):
        """
        Parameters
        ----------
        data_files : list
            List of NetCDF file paths
        input_levels : list
            Pressure levels for input (hPa)
        output_levels : list
            Pressure levels for output/target (hPa)
        stats : dict, optional
            Precomputed normalization statistics
        data_source : str
            Data source: 'ERA5' or 'MERRA2'
        """
        self.data_source = data_source
        self.input_levels = input_levels
        self.output_levels = output_levels
        self.n_input = len(input_levels)
        self.n_output = len(output_levels)
        self.var_names = ['t', 'r', 'z', 'u', 'v']
        self.profiles = []

        self._load_data(data_files)

        if stats is None:
            self.stats = self._compute_per_variable_stats()
        else:
            self.stats = stats

        self._normalize_all()

    def _load_data(self, data_files):
        """
        УСТОЙЧИВАЯ ВЕРСИЯ с обработкой исключений и принудительной очисткой ресурсов.
        """
        import gc
        print(f"Загрузка {len(data_files)} файлов {self.data_source}...")
        print("УСКОРЕННАЯ загрузка с защитой от сбоев файловой системы\n")
        
        var_mapping = {
            't': 'temperature',
            'r': 'relative_humidity',
            'z': 'geopotential',
            'u': 'u_component_of_wind',
            'v': 'v_component_of_wind'
        }
        
        all_levels = sorted(list(set(self.input_levels + self.output_levels)))
        n_input_levels = len(self.input_levels)
        rng = np.random.default_rng(42)
        
        # Счетчики для статистики
        successful_files = 0
        failed_files = 0
        corrupted_files = []
        
        for file_idx, file_path in enumerate(data_files):
            ds = None  # Гарантируем начальное состояние
            
            try:
                # ============================================================
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ #1: Проверка файла перед открытием
                # ============================================================
                if not os.path.exists(file_path):
                    print(f"  ⚠ Файл {file_idx+1}: не существует, пропускаем")
                    failed_files += 1
                    continue
                
                # Проверка размера (пустые/поврежденные файлы)
                file_size = os.path.getsize(file_path)
                if file_size < 1000:  # Минимальный размер NetCDF ~1KB
                    print(f"  ⚠ Файл {file_idx+1}: слишком мал ({file_size} bytes), удаляем")
                    os.remove(file_path)
                    corrupted_files.append(file_path)
                    failed_files += 1
                    continue
                
                # ============================================================
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ #2: Явное управление контекстом
                # ============================================================
                try:
                    ds = xr.open_dataset(
                        file_path,
                        decode_times=False,
                        engine='h5netcdf',
                        mask_and_scale=True,
                        phony_dims='sort',
                        # НОВОЕ: отключаем кэширование для экономии дескрипторов
                        cache=False
                    )
                except (OSError, IOError) as e:
                    # Errno 107 или другие ошибки ФС
                    if 'errno = 107' in str(e) or 'Transport endpoint' in str(e):
                        print(f"  ⚠ Файл {file_idx+1}: ошибка ФС (errno 107), перезапуск через 2с...")
                        # Принудительная очистка + пауза для восстановления ФС
                        gc.collect()
                        import time
                        time.sleep(2)
                        
                        # Повторная попытка ОДИН раз
                        try:
                            ds = xr.open_dataset(
                                file_path,
                                decode_times=False,
                                engine='h5netcdf',
                                cache=False
                            )
                        except Exception as retry_err:
                            print(f"  ✗ Файл {file_idx+1}: повтор неудачен - {str(retry_err)[:100]}")
                            corrupted_files.append(file_path)
                            failed_files += 1
                            continue
                    else:
                        raise  # Другие ошибки пробрасываем дальше
                
                # ============================================================
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ #3: Идентификация измерений с fallback
                # ============================================================
                time_dim = next((c for c in ['valid_time', 'time', 't'] if c in ds.dims), None)
                level_dim = next((c for c in ['pressure_level', 'level', 'plev', 'lev'] if c in ds.dims), None)
                lat_dim = 'latitude' if 'latitude' in ds.dims else 'lat'
                lon_dim = 'longitude' if 'longitude' in ds.dims else 'lon'
                
                if not time_dim or not level_dim:
                    print(f"  ⚠ Файл {file_idx+1}: нет измерений (time={time_dim}, level={level_dim})")
                    failed_files += 1
                    # Принудительное закрытие перед continue
                    if ds is not None:
                        ds.close()
                        ds = None
                    continue
                
                # ============================================================
                # ОПТИМИЗАЦИЯ #1: Однократный sel для всех уровней
                # ============================================================
                ds_subset = ds.sel({level_dim: all_levels}, method='nearest')
                
                # НОВОЕ: Явная загрузка в память + закрытие файла
                ds_subset = ds_subset.load()
                
                # КРИТИЧНО: Закрываем исходный dataset СРАЗУ после load()
                ds.close()
                ds = None  # Обнуляем ссылку
                
                n_times = min(2, len(ds_subset[time_dim]))
                
                for time_idx in range(n_times):
                    try:
                        # ============================================================
                        # ОПТИМИЗАЦИЯ #2: Стек всех переменных
                        # ============================================================
                        var_arrays = []
                        for var_dataset in var_mapping.values():
                            if var_dataset not in ds_subset:
                                raise KeyError(f"Переменная {var_dataset} отсутствует")
                            var_arrays.append(ds_subset[var_dataset].isel({time_dim: time_idx}).values)
                        
                        all_vars_stack = np.stack(var_arrays, axis=0)
                        valid_mask = np.all(np.isfinite(all_vars_stack), axis=(0, 1))
                        
                        if not np.any(valid_mask):
                            continue
                        
                        # ============================================================
                        # ОПТИМИЗАЦИЯ #3: Прямая случайная выборка
                        # ============================================================
                        lat_indices, lon_indices = np.where(valid_mask)
                        n_valid = len(lat_indices)
                        n_samples = min(7000, n_valid)
                        selected = rng.choice(n_valid, n_samples, replace=False)
                        lat_sel = lat_indices[selected]
                        lon_sel = lon_indices[selected]
                        
                        if file_idx == 0 and time_idx == 0:
                            print(f"  Файл 1, срез 0: {n_valid} валидных → выбрано {n_samples}")
                        
                        # ============================================================
                        # ОПТИМИЗАЦИЯ #4: Векторизованная экстракция
                        # ============================================================
                        profiles_data = {}
                        for var_internal, var_dataset in var_mapping.items():
                            var_full = all_vars_stack[list(var_mapping.values()).index(var_dataset)]
                            profiles_var = var_full[:, lat_sel, lon_sel]
                            profiles_data[f'{var_internal}_input'] = profiles_var[:n_input_levels].T
                            profiles_data[f'{var_internal}_output'] = profiles_var[n_input_levels:].T
                        
                        for i in range(n_samples):
                            profile = {
                                key: arr[i].astype(np.float32)
                                for key, arr in profiles_data.items()
                            }
                            self.profiles.append(profile)
                    
                    except (KeyError, ValueError, IndexError) as e:
                        print(f"  ⚠ Файл {file_idx+1}, срез {time_idx}: ошибка данных - {str(e)[:80]}")
                        continue
                
                # Успешная обработка
                successful_files += 1
                if (file_idx + 1) % 10 == 0 or file_idx < 5:
                    print(f"  Файл {file_idx+1}/{len(data_files)}: {len(self.profiles)} профилей всего")
            
            except Exception as e:
                # Универсальный обработчик для непредвиденных ошибок
                error_msg = str(e)[:200]
                print(f"  ✗ ОШИБКА файла {file_idx+1}: {error_msg}")
                corrupted_files.append(file_path)
                failed_files += 1
            
            finally:
                # ============================================================
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ #4: Гарантированная очистка
                # ============================================================
                if ds is not None:
                    try:
                        ds.close()
                    except:
                        pass  # Игнорируем ошибки при закрытии
                    finally:
                        ds = None
                
                # Принудительная сборка мусора каждые 20 файлов
                if (file_idx + 1) % 20 == 0:
                    gc.collect()
        
        # ============================================================
        # Итоговая статистика
        # ============================================================
        print(f"\n{'='*80}")
        print(f"ИТОГИ ЗАГРУЗКИ:")
        print(f"  ✓ Успешно обработано: {successful_files}/{len(data_files)}")
        print(f"  ✗ Ошибок: {failed_files}")
        print(f"  📊 Всего профилей: {len(self.profiles)}")
        
        if corrupted_files:
            print(f"\n⚠ Поврежденные файлы ({len(corrupted_files)}):")
            for cf in corrupted_files[:10]:  # Показываем первые 10
                print(f"    - {os.path.basename(cf)}")
            if len(corrupted_files) > 10:
                print(f"    ... и еще {len(corrupted_files) - 10}")
        print(f"{'='*80}\n")
        
        # Проверка минимального количества данных
        if len(self.profiles) < 10000:
            raise RuntimeError(
                f"Недостаточно данных для обучения: {len(self.profiles)} профилей "
                f"(минимум 10,000). Проверьте целостность файлов."
            )
`



    def _compute_per_variable_stats(self):
        print("\nВычисление статистики ПО ПЕРЕМЕННЫМ...")

        stats = {}

        for var in self.var_names:
            # input_data = np.concatenate([p[f'{var}_input'] for p in self.profiles])
            # output_data = np.concatenate([p[f'{var}_output'] for p in self.profiles])
            # ДЛЯ ТЕМПЕРАТУРЫ: log-space нормализация
            if var == 't':
                input_data = np.log(np.concatenate([p[f'{var}_input'] for p in self.profiles]))
                output_data = np.log(np.concatenate([p[f'{var}_output'] for p in self.profiles]))
            else:
                input_data = np.concatenate([p[f'{var}_input'] for p in self.profiles])
                output_data = np.concatenate([p[f'{var}_output'] for p in self.profiles])

            stats[var] = {
                'input_mean': float(input_data.mean()),
                'input_std': float(input_data.std()),
                'output_mean': float(output_data.mean()),
                'output_std': float(output_data.std())
            }

            print(f"  {var.upper()}: вх_среднее={stats[var]['input_mean']:.2f}, вых_среднее={stats[var]['output_mean']:.2f}")

        return stats

    def _normalize_all(self):
        print("Нормализация с использованием статистики по переменным...")

        for profile in self.profiles:
            input_norm = []
            output_norm = []

            for var in self.var_names:
                var_input = profile[f'{var}_input']
                var_output = profile[f'{var}_output']

                var_input_norm = (var_input - self.stats[var]['input_mean']) / (self.stats[var]['input_std'] + 1e-6)
                var_output_norm = (var_output - self.stats[var]['output_mean']) / (self.stats[var]['output_std'] + 1e-6)

                input_norm.extend(var_input_norm)
                output_norm.extend(var_output_norm)

            profile['input_norm'] = np.array(input_norm, dtype=np.float32)
            profile['output_norm'] = np.array(output_norm, dtype=np.float32)

        print(f"Все {len(self.profiles)} профилей нормализованы\n")

    def __len__(self):
        return len(self.profiles)

    def __getitem__(self, idx):
        profile = self.profiles[idx]
        return (
            torch.from_numpy(profile['input_norm']).float(),
            torch.from_numpy(profile['output_norm']).float()
        )


def train_model(model, train_loader, val_loader, device, max_epochs, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # ИСПРАВЛЕНИЕ #1: уменьшаем learning rate для стабильности
    optimizer = optim.AdamW(model.parameters(), 
                        lr=3e-4,  # Базовая ставка выше в 6 раз
                        betas=(0.9, 0.95),  # beta2 снижен для стабильности
                        weight_decay=0.01)  # Регуляризация
    from torch.optim.lr_scheduler import OneCycleLR
    total_steps = max_epochs * len(train_loader)
    scheduler = OneCycleLR(
        optimizer,
        max_lr=3e-4,
        total_steps=total_steps,
        pct_start=0.1,  # 10% эпох на warm-up
        anneal_strategy='cos',
        div_factor=25.0,  # Начальный LR = max_lr/25 = 1.2e-5
        final_div_factor=1000.0  # Финальный LR = max_lr/1000 = 3e-7
    )
    
    criterion = PhysicsInformedLoss(
        n_output_levels=len(OUTPUT_LEVELS),
        thermal_wind_weight=0.5,  # Увеличен с 0.1 до 0.5
        wind_component_weight=2.0,
        hydrostatic_weight=0.3  # НОВЫЙ параметр
    ).to(device)
    
    use_amp = (device.type == 'cuda')
    scaler = GradScaler(enabled=use_amp)
    accumulation_steps = 1
    
    history = {
        'train_loss': [], 'val_loss': [], 'learning_rate': [],
        'train_mse_T': [], 'train_mse_U': [], 'train_mse_V': [],
        'val_mse_T': [], 'val_mse_U': [], 'val_mse_V': []
    }
    best_val_loss = float('inf')
    best_epoch = 0
    patience = 20  # Early stopping
    patience_counter = 0
    
    print(f"\nНачало обучения...")
    print(f"Learning Rate: {optimizer.param_groups[0]['lr']:.2e} (с warm-up)")
    print(f"Эффективный batch size: {BATCH_SIZE * accumulation_steps}")
    print(f"Физические веса: thermal_wind={criterion.tw_weight.item():.2f}, "
          f"hydrostatic={criterion.hs_weight.item():.2f}")
    print(f"Mixed Precision: {'Enabled' if use_amp else 'Disabled'}")
    print(f"Early Stopping: patience={patience}")
    print(f"{'='*80}\n")
    
    for epoch in range(1, max_epochs + 1):
        # ========== TRAINING ==========
        model.train()
        train_loss = 0.0
        train_metrics = {'mse_T': 0.0, 'mse_U': 0.0, 'mse_V': 0.0}
        optimizer.zero_grad(set_to_none=True)
        num_train_batches = 0
        
        for batch_idx, (inputs, targets) in enumerate(train_loader):
            num_train_batches += 1
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            
            # Проверка на NaN
            if torch.isnan(inputs).any() or torch.isnan(targets).any():
                print(f"  WARNING: NaN в данных батча {batch_idx}, пропуск")
                continue
            
            with autocast(enabled=use_amp):
                outputs = model(inputs)
                loss, loss_dict = criterion(outputs, targets)
                loss = loss / accumulation_steps
            
            # Проверка на NaN/Inf в loss
            if torch.isnan(loss) or torch.isinf(loss):
                print(f"  WARNING: NaN/Inf loss в батче {batch_idx}, пропуск")
                optimizer.zero_grad(set_to_none=True)
                continue
            
            scaler.scale(loss).backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % accumulation_steps == 0:
                scaler.unscale_(optimizer)
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                if torch.isnan(grad_norm) or torch.isinf(grad_norm):
                    print(f"  WARNING: NaN/Inf градиенты в батче {batch_idx}, пропуск")
                    optimizer.zero_grad(set_to_none=True)
                    scaler.update()
                    continue
                
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()  # ВАЖНО: шаг после каждого обновления весов
                optimizer.zero_grad(set_to_none=True)
            
            train_loss += loss.item() * accumulation_steps
            train_metrics['mse_T'] += loss_dict.get('mse_T', 0.0)
            train_metrics['mse_U'] += loss_dict.get('mse_U', 0.0)
            train_metrics['mse_V'] += loss_dict.get('mse_V', 0.0)
        
        # Обработка остатка gradient accumulation
        if num_train_batches % accumulation_steps != 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
        
        if num_train_batches > 0:
            train_loss /= num_train_batches
            for key in train_metrics:
                train_metrics[key] /= num_train_batches
        
        # ========== VALIDATION ==========
        model.eval()
        val_loss = 0.0
        val_metrics = {'mse_T': 0.0, 'mse_U': 0.0, 'mse_V': 0.0}
        num_val_batches = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                num_val_batches += 1
                inputs = inputs.to(device, non_blocking=True)
                targets = targets.to(device, non_blocking=True)
                
                if torch.isnan(inputs).any() or torch.isnan(targets).any():
                    continue
                
                with autocast(enabled=use_amp):
                    outputs = model(inputs)
                    loss, loss_dict = criterion(outputs, targets)
                
                if not torch.isnan(loss):
                    val_loss += loss.item()
                    val_metrics['mse_T'] += loss_dict.get('mse_T', 0.0)
                    val_metrics['mse_U'] += loss_dict.get('mse_U', 0.0)
                    val_metrics['mse_V'] += loss_dict.get('mse_V', 0.0)
        
        if num_val_batches > 0:
            val_loss /= num_val_batches
            for key in val_metrics:
                val_metrics[key] /= num_val_batches
        
        # Сохранение истории
        current_lr = optimizer.param_groups[0]['lr']
        history['train_loss'].append(float(train_loss))
        history['val_loss'].append(float(val_loss))
        history['learning_rate'].append(float(current_lr))
        history['train_mse_T'].append(train_metrics['mse_T'])
        history['train_mse_U'].append(train_metrics['mse_U'])
        history['train_mse_V'].append(train_metrics['mse_V'])
        history['val_mse_T'].append(val_metrics['mse_T'])
        history['val_mse_U'].append(val_metrics['mse_U'])
        history['val_mse_V'].append(val_metrics['mse_V'])
        
        # Логирование
        if epoch % 5 == 0 or epoch == 1:
            print(f"Эпоха {epoch:3d}/{max_epochs} | "
                  f"Train: {train_loss:.6f} | Val: {val_loss:.6f} | "
                  f"LR: {current_lr:.2e} | "
                  f"ValMSE[T/U/V]: {val_metrics['mse_T']:.4f}/{val_metrics['mse_U']:.4f}/{val_metrics['mse_V']:.4f}")
        
        # Сохранение лучшей модели
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0
            
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'scaler_state_dict': scaler.state_dict(),
                'val_loss': val_loss,
                'train_loss': train_loss,
                'val_metrics': val_metrics
            }, os.path.join(output_dir, 'best_model.pth'))
            
            print(f"  ✓ Лучшая модель сохранена (эпоха {epoch})")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\nEarly stopping на эпохе {epoch} (patience={patience})")
            break
    
    # Финальная модель
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict()
    }, os.path.join(output_dir, 'final_model.pth'))
    
    # Сохранение истории
    with open(os.path.join(output_dir, 'training_history.json'), 'w') as f:
        json.dump({
            'metadata': {
                'best_epoch': best_epoch,
                'best_val_loss': float(best_val_loss),
                'final_epoch': epoch,
                'mixed_precision': use_amp,
                'accumulation_steps': accumulation_steps,
                'effective_batch_size': BATCH_SIZE * accumulation_steps
            },
            'history': history
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print(f"Лучшая эпоха: {best_epoch} | Лучший Val Loss: {best_val_loss:.6f}")
    print(f"{'='*80}\n")
    
    return history



def main():

    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (min(4096, hard), hard))
        print(f"✓ Лимит файловых дескрипторов: {soft} → {min(4096, hard)}")
    except Exception as e:
        print(f"⚠ Не удалось увеличить лимит дескрипторов: {e}")

    # Configuration based on DATA_SOURCE
    if DATA_SOURCE == 'ERA5':
        DATA_DIR = './data/era5'
        PRESSURE_LEVELS = PRESSURE_LEVELS_ERA5
        VARIABLES = VARIABLES_ERA5
    elif DATA_SOURCE == 'MERRA2':
        DATA_DIR = './data/merra2'
        PRESSURE_LEVELS = PRESSURE_LEVELS_MERRA2
        VARIABLES = list(VARIABLES_MERRA2.keys())
    else:
        raise ValueError(f"Unknown DATA_SOURCE: {DATA_SOURCE}. Must be 'ERA5' or 'MERRA2'")

    OUTPUT_DIR = f'./training_{DATA_SOURCE.lower()}_extended'

    n_variables = 5  # t, r, z, u, v
    input_dim = len(INPUT_LEVELS) * n_variables
    output_dim = len(OUTPUT_LEVELS) * n_variables

    torch.manual_seed(42)
    np.random.seed(42)

    # ==========================================================
    # GPU / Multi-GPU / DDP настройки
    # ==========================================================
    use_cuda = torch.cuda.is_available()
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    distributed = (world_size > 1) and use_cuda

    if use_cuda:
        cudnn.benchmark = True
        cudnn.deterministic = False

    if distributed:
        # torchrun задаёт LOCAL_RANK, RANK, WORLD_SIZE
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        device = torch.device("cuda", local_rank)

        torch.distributed.init_process_group(backend="nccl", init_method="env://")
        rank = torch.distributed.get_rank()

        if rank == 0:
            print(f"DDP: world_size={world_size}, local_rank={local_rank}")
    else:
        device = torch.device('cuda' if use_cuda else 'cpu')
        print(f"Устройство вычислений: {device}")
        if use_cuda:
            print(f"GPU(0): {torch.cuda.get_device_name(0)}")
            print(f"Всего GPU: {torch.cuda.device_count()}")

    print(f"\nИсточник данных: {DATA_SOURCE}")
    print(f"Входные уровни: {len(INPUT_LEVELS)} (от {INPUT_LEVELS[0]} до {INPUT_LEVELS[-1]} гПа)")
    print(f"Выходные уровни: {len(OUTPUT_LEVELS)} (от {OUTPUT_LEVELS[0]} до {OUTPUT_LEVELS[-1]} гПа)")
    print(f"Размерность входа: {input_dim}")
    print(f"Размерность выхода: {output_dim}\n")

    # Проверка наличия данных
    print(f"Проверка данных {DATA_SOURCE}...\n")
    required_files = len(DOWNLOAD_YEARS) * len([m for s in SEASONS_TO_DOWNLOAD for m in SEASONAL_MONTHS[s]]) * 10
    existing_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.nc')] if os.path.exists(DATA_DIR) else []

    if len(existing_files) < required_files * 0.5:
        print(f"Недостаточно данных. Начинается загрузка {DATA_SOURCE}...")
        print(f"Будет загружено ~{required_files} файлов для периода {DOWNLOAD_YEARS[0]}-{DOWNLOAD_YEARS[-1]}\n")
        
        download_merra2_https(
            output_dir=DATA_DIR,
            years=DOWNLOAD_YEARS,
            seasons=SEASONS_TO_DOWNLOAD,
            time_slices=TIME_SLICES,
            day_step=10,
            # days_per_month=1,
            skip_existing=True
        )
    else:
        print(f"✓ Обнаружено {len(existing_files)} файлов {DATA_SOURCE}\n")

    data_files = sorted([os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.nc')])
    if len(data_files) == 0:
        print("ОШИБКА: Файлы данных не найдены!")
        return

    full_dataset = AtmosphericDatasetPerVarNorm(
        data_files, INPUT_LEVELS, OUTPUT_LEVELS,
        stats=None, data_source=DATA_SOURCE
    )

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # hidden_dims
    if input_dim >= 145:
        hidden_dims = [768, 512, 384, 256, 384, 512, 768]
    else:
        hidden_dims = [512, 384, 256, 256, 384, 512]

    # Конфиг и статы
    config = {
        'data_source': DATA_SOURCE,
        'input_levels': INPUT_LEVELS,
        'output_levels': OUTPUT_LEVELS,
        'input_dim': input_dim,
        'output_dim': output_dim,
        'n_variables': n_variables,
        'hidden_dims': hidden_dims
    }
    with open(os.path.join(OUTPUT_DIR, 'config.json'), 'w') as f:
        json.dump(config, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, 'normalization_stats.json'), 'w') as f:
        json.dump(full_dataset.stats, f, indent=2)

    # Трен/валид сплит
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    # Если DDP — используем DistributedSampler
    if distributed:
        train_sampler = torch.utils.data.distributed.DistributedSampler(
            train_dataset,
            num_replicas=world_size,
            rank=torch.distributed.get_rank(),
            shuffle=True,
            drop_last=True
        )
        val_sampler = torch.utils.data.distributed.DistributedSampler(
            val_dataset,
            num_replicas=world_size,
            rank=torch.distributed.get_rank(),
            shuffle=False,
            drop_last=False
        )
        shuffle_train = False
        shuffle_val = False
    else:
        train_sampler = None
        val_sampler = None
        shuffle_train = True
        shuffle_val = False

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=shuffle_train,
        sampler=train_sampler,
        drop_last=True,
        num_workers=4,
        pin_memory=use_cuda,
        persistent_workers=False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=shuffle_val,
        sampler=val_sampler,
        num_workers=2,
        pin_memory=use_cuda,
        persistent_workers=False
    )

    # Модель
    model = create_model(
        input_dim=input_dim,
        output_dim=output_dim,
        n_input_levels=len(INPUT_LEVELS),
        n_output_levels=len(OUTPUT_LEVELS),
        device=device,
        output_pressure_levels=OUTPUT_LEVELS  # НОВЫЙ параметр
    )

    model = model.to(device)

    # Если много GPU, но не DDP — DataParallel
    if (not distributed) and use_cuda and torch.cuda.device_count() > 1:
        print(f"Используется DataParallel на {torch.cuda.device_count()} GPU")
        model = torch.nn.DataParallel(model)

    # Если DDP, оборачиваем в DistributedDataParallel
    if distributed:
        model = torch.nn.parallel.DistributedDataParallel(
            model,
            device_ids=[device.index],
            output_device=device.index,
            find_unused_parameters=False
        )

    print(f"Параметров модели: {sum(p.numel() for p in model.parameters()):,}\n")

    # В DDP `train_model` вызывается на каждом процессе, но сохранять модели/логи имеет смысл только на rank 0.
    if (not distributed) or (torch.distributed.get_rank() == 0):
        history = train_model(model, train_loader, val_loader, device, MAX_EPOCHS, OUTPUT_DIR)
        print(f"\nФайлы сохранены: {OUTPUT_DIR}/best_model.pth, normalization_stats.json, config.json")
    else:
        # Для остальных ранков просто тренируем без сохранения файлов
        _ = train_model(model, train_loader, val_loader, device, MAX_EPOCHS, OUTPUT_DIR)

    if distributed:
        torch.distributed.destroy_process_group()


if __name__ == '__main__':
    main()
