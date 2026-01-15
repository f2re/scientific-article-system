"""
Построение графиков вертикального зондирования атмосферы для России 
с использованием библиотеки sounderpy за те же даты, что используются 
для обучения модели атмосферных профилей.

ТОЛЬКО СОХРАНЕНИЕ В ФАЙЛЫ - БЕЗ РАДАРА И КАРТЫ
"""
import warnings
warnings.filterwarnings('ignore')

import sounderpy as spy
import os
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # ВАЖНО: Бэкенд без GUI
import matplotlib.pyplot as plt

# Отключение интерактивного режима
plt.ioff()

# ============================================================================
# ПАРАМЕТРЫ ИЗ ОСНОВНОГО КОДА (синхронизация с обучением модели)
# ============================================================================

YEARS = list(range(2015, 2017))  # 2015-2016

SEASONAL_MONTHS = {
    'winter': ['12', '02'],
    'spring': ['03', '05'],
    'summer': ['06', '08'],
    'autumn': ['09', '11']
}

SEASONS_TO_DOWNLOAD = ['winter', 'summer']
TIME_HOURS = ['00', '12']  # UTC часы
DAY_STEP = 10

# ============================================================================
# РОССИЙСКИЕ СТАНЦИИ РАДИОЗОНДИРОВАНИЯ
# ============================================================================

RUSSIAN_STATIONS = {
    '27612': ('Москва (Долгопрудный)', 55.72, 37.87),
    '26063': ('Санкт-Петербург', 59.97, 30.30),
    '34172': ('Екатеринбург', 56.80, 60.63),
    '26298': ('Архангельск', 64.57, 40.50),
    '27730': ('Нижний Новгород', 56.22, 43.82),
    '28698': ('Оренбург', 51.70, 55.10),
    '30230': ('Новосибирск', 55.03, 82.90),
    '31168': ('Иркутск', 52.27, 104.32),
    '31253': ('Чита', 52.03, 113.50),
    '31960': ('Владивосток', 43.12, 131.93),
    '23205': ('Мурманск', 68.97, 33.05),
}

BEST_STATION = '27612'


import csv
import numpy as np

def calculate_rh_from_dewpoint(temp_celsius, dewpoint_celsius):
    """
    Расчет относительной влажности (%) из температуры и точки росы.
    Формула Магнуса (Bolton 1980).
    
    Parameters:
    -----------
    temp_celsius : array-like
        Температура воздуха в °C
    dewpoint_celsius : array-like
        Точка росы в °C
    
    Returns:
    --------
    rh_percent : array-like
        Относительная влажность в %
    """
    def saturation_vapor_pressure(t_c):
        """Давление насыщения (гПа) по формуле Магнуса"""
        return 6.112 * np.exp(17.67 * t_c / (t_c + 243.5))
    
    e_actual = saturation_vapor_pressure(dewpoint_celsius)
    e_sat = saturation_vapor_pressure(temp_celsius)
    rh = 100.0 * e_actual / e_sat
    
    return np.clip(rh, 0, 100)



def save_sounding_to_csv(clean_data, csv_path):
    """
    Сохранение профиля в CSV:
    columns: pressure, height, temp, dewpoint, rh, wspd, wdir, u, v
    """
    # Достаем базовые поля
    p  = np.array(getattr(clean_data.get('p'),  'magnitude', clean_data.get('p',  [])))
    z  = np.array(getattr(clean_data.get('z'),  'magnitude', clean_data.get('z',  [])))
    T  = np.array(getattr(clean_data.get('T'),  'magnitude', clean_data.get('T',  [])))
    Td = np.array(getattr(clean_data.get('Td'), 'magnitude', clean_data.get('Td', [])))
    u  = np.array(getattr(clean_data.get('u'),  'magnitude', clean_data.get('u',  [])))
    v  = np.array(getattr(clean_data.get('v'),  'magnitude', clean_data.get('v',  [])))

    # Конвертация температур из K в °C (если в Кельвинах)
    T_celsius = T - 273.15 if T.size > 0 and T.mean() > 200 else T
    Td_celsius = Td - 273.15 if Td.size > 0 and Td.mean() > 200 else Td
    
    # Расчет относительной влажности
    if T_celsius.size > 0 and Td_celsius.size > 0 and T_celsius.size == Td_celsius.size:
        rh = calculate_rh_from_dewpoint(T_celsius, Td_celsius)
    else:
        rh = np.array([])
    
    # Восстановление скорости и направления из u,v
    if u.size > 0 and v.size > 0:
        wspd = np.sqrt(u**2 + v**2)
        wdir_rad = np.arctan2(-u, -v)
        wdir = (np.degrees(wdir_rad) + 360) % 360
    else:
        wspd = np.array([])
        wdir = np.array([])

    # Выравнивание длины
    arrays = [p, z, T, Td, rh, wspd, wdir, u, v]
    max_len = max(a.size for a in arrays if a.size > 0)
    
    def pad(a):
        if a.size == 0:
            return np.full(max_len, np.nan)
        if a.size == max_len:
            return a
        return np.pad(a, (0, max_len - a.size), constant_values=np.nan)
    
    p, z, T, Td, rh, wspd, wdir, u, v = [pad(a) for a in arrays]

    # Запись в CSV
    header = ['pressure_hPa', 'height_m', 'temp_K', 'dewpoint_K', 'rh_percent',
              'wspd_ms', 'wdir_deg', 'u_ms', 'v_ms']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(max_len):
            writer.writerow([
                p[i], z[i], T[i], Td[i], rh[i],
                wspd[i], wdir[i], u[i], v[i]
            ])


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ ГРАФИКОВ
# ============================================================================

def plot_soundings_for_training_dates(
    station_code=BEST_STATION,
    output_dir='./soundings_russia',
    years=None,
    seasons=None,
    time_hours=None,
    day_step=10,
    max_plots=None,
    skip_errors=True,
    dark_mode=False,
    color_blind=False
):
    """
    Построение графиков вертикального зондирования для российских станций.
    
    Parameters
    ----------
    station_code : str
        WMO код станции
    output_dir : str
        Директория для сохранения графиков
    years : list, optional
        Годы для построения
    seasons : list, optional
        Сезоны для построения
    time_hours : list, optional
        Часы наблюдений (UTC)
    day_step : int
        Шаг по дням месяца
    max_plots : int, optional
        Максимальное количество графиков
    skip_errors : bool
        Пропускать ошибки и продолжать работу
    dark_mode : bool
        Темная тема графиков
    color_blind : bool
        Режим для дальтоников
    """
    
    if years is None:
        years = YEARS
    if seasons is None:
        seasons = SEASONS_TO_DOWNLOAD
    if time_hours is None:
        time_hours = TIME_HOURS
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    station_name = RUSSIAN_STATIONS.get(station_code, ('Неизвестная станция', 0, 0))[0]
    
    print("\n" + "="*80)
    print(f"ПОСТРОЕНИЕ ГРАФИКОВ ЗОНДИРОВАНИЯ: {station_name} ({station_code})")
    print("="*80)
    print(f"Годы:      {years[0]}-{years[-1]}")
    print(f"Сезоны:    {', '.join(seasons)}")
    print(f"Часы (UTC): {', '.join(time_hours)}")
    print(f"Шаг дней:  {day_step}")
    print(f"Выходная директория: {output_dir}")
    print("="*80 + "\n")
    
    # Формирование списка месяцев
    months_to_plot = []
    for season in seasons:
        if season in SEASONAL_MONTHS:
            months_to_plot.extend(SEASONAL_MONTHS[season])
    months_to_plot = sorted(list(set(months_to_plot)))
    
    plot_count = 0
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for year in years:
        for month in months_to_plot:
            month_int = int(month)
            
            # Определение дней в месяце
            if month_int in [1, 3, 5, 7, 8, 10, 12]:
                max_days = 31
            elif month_int in [4, 6, 9, 11]:
                max_days = 30
            elif month_int == 2:
                max_days = 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
            else:
                max_days = 31
            
            days = list(range(1, max_days + 1, day_step))
            
            for day in days:
                for hour in time_hours:
                    if max_plots is not None and plot_count >= max_plots:
                        print(f"\n⚠ Достигнут лимит: {max_plots}")
                        print(f"✓ Успешно: {success_count} | ✗ Ошибок: {error_count}")
                        return
                    
                    plot_count += 1
                    
                    date_str = f"{year}-{month:0>2}-{day:02d}T{hour}:00"
                    filename = f"sounding_{station_code}_{year}{month:0>2}{day:02d}_{hour}z.png"
                    output_path = os.path.join(output_dir, filename)
                    
                    # Пропуск существующих
                    if os.path.exists(output_path):
                        skip_count += 1
                        if plot_count % 10 == 0:
                            print(f"[{plot_count}] ⊘ {date_str}")
                        continue
                    
                    print(f"[{plot_count}] {date_str}...", end=' ', flush=True)
                    
                    try:
                        # Получение данных с подавлением вывода
                        clean_data = spy.get_obs_data(
                            station_code, 
                            str(year), 
                            month, 
                            str(day), 
                            hour,
                            hush=True
                        )
                        
                        # ПРАВИЛЬНЫЕ ПАРАМЕТРЫ для build_sounding:
                        # - save=True - сохранить файл
                        # - filename - полный путь к файлу
                        # - show_radar=False - отключить радар
                        # - map_zoom=0 - скрыть карту
                        # - dark_mode - темная тема
                        # - color_blind - для дальтоников
                        spy.build_sounding(
                            clean_data,
                            save=True,              # Сохранить в файл
                            filename=output_path,   # Полный путь
                            radar=None,       # БЕЗ радара
                            map_zoom=0
                        )
                        csv_filename = f"sounding_{station_code}_{year}{month:0>2}{day:02d}_{hour}z.csv"
                        csv_path = os.path.join(output_dir, csv_filename)

                        save_sounding_to_csv(clean_data, csv_path)

                        # Закрытие всех фигур
                        plt.close('all')
                        
                        success_count += 1
                        print(f"✓")
                        
                    except KeyboardInterrupt:
                        print("\n\n⚠ Прервано (Ctrl+C)")
                        print(f"✓ {success_count} | ✗ {error_count} | ⊘ {skip_count}")
                        return
                        
                    except Exception as e:
                        error_count += 1
                        error_msg = str(e).lower()
                        
                        # Определение типа ошибки
                        if 'connection' in error_msg or 'failed' in error_msg:
                            error_type = "связь"
                        elif 'timeout' in error_msg:
                            error_type = "таймаут"
                        elif 'not found' in error_msg or 'no data' in error_msg:
                            error_type = "нет данных"
                        else:
                            error_type = str(e)[:40]
                        
                        print(f"✗ {error_type}")
                        
                        if not skip_errors:
                            raise
                        
                        continue
                    
                    # Периодический вывод прогресса
                    if plot_count % 20 == 0:
                        total_attempts = plot_count - skip_count
                        success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0
                        print(f"    └─ [{success_count}/{total_attempts}] = {success_rate:.0f}% успешно")
    
    # Итоговая статистика
    print("\n" + "="*80)
    print("ПОСТРОЕНИЕ ЗАВЕРШЕНО")
    print("="*80)
    print(f"Всего попыток:    {plot_count}")
    print(f"Успешно:          {success_count}")
    print(f"Ошибок:           {error_count}")
    print(f"Пропущено:        {skip_count}")
    total_attempts = plot_count - skip_count
    if total_attempts > 0:
        success_rate = success_count / total_attempts * 100
        print(f"Успешность:       {success_rate:.1f}%")
    print(f"Директория:       {output_dir}")
    print("="*80 + "\n")



# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

if __name__ == '__main__':
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║     ПОСТРОЕНИЕ ГРАФИКОВ ЗОНДИРОВАНИЯ ДЛЯ РОССИЙСКИХ СТАНЦИЙ         ║
    ║         С ИСПОЛЬЗОВАНИЕМ SOUNDERPY (БЕЗ РАДАРА И КАРТЫ)              ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # ────────────────────────────────────────────────────────────────────
    # ВАРИАНТ 1: Москва - основная станция
    # ────────────────────────────────────────────────────────────────────
    
    print("\n📊 Москва (Долгопрудный) - WMO 27612")
    print("─" * 70)
    
    plot_soundings_for_training_dates(
        station_code='27612',
        output_dir='./soundings_moscow',
        years=[2015, 2016],
        seasons=['winter', 'summer'],
        time_hours=['00', '12'],
        day_step=10,
        max_plots=None,      # Без ограничений
        skip_errors=True,    # Пропускать ошибки
        dark_mode=False,     # Светлая тема
        color_blind=False    # Обычные цвета
    )
    
    # ────────────────────────────────────────────────────────────────────
    # ВАРИАНТ 2: Дополнительные станции (раскомментируйте при необходимости)
    # ────────────────────────────────────────────────────────────────────
    
    # # Санкт-Петербург
    # print("\n📊 Санкт-Петербург - WMO 26063")
    # print("─" * 70)
    # plot_soundings_for_training_dates(
    #     station_code='26063',
    #     output_dir='./soundings_spb',
    #     max_plots=50
    # )
    
    # # Новосибирск
    # print("\n📊 Новосибирск - WMO 30230")
    # print("─" * 70)
    # plot_soundings_for_training_dates(
    #     station_code='30230',
    #     output_dir='./soundings_novosibirsk',
    #     max_plots=50
    # )
    
    # ────────────────────────────────────────────────────────────────────
    # ВАРИАНТ 3: Сравнение станций для конкретных дат
    # ────────────────────────────────────────────────────────────────────
    
    
    print("\n" + "="*80)
    print("✓ ВСЕ ЗАДАЧИ ВЫПОЛНЕНЫ")
    print("="*80)
    print("""
    📂 РЕЗУЛЬТАТЫ:
       • ./soundings_moscow/ - графики для Москвы
    """)
