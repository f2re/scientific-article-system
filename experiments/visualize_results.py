"""
Визуализация результатов модели с относительной влажностью.
Все подписи на русском языке.
Поддержка ERA5 и MERRA2 с расширением до 0.1 гПа.
"""
import os
import json
import numpy as np
import xarray as xr
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# from model_architecture import AtmosphericProfileResNet
from model_architecture import MultiHeadAtmosphericResNet

# Настройка шрифтов для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_model_and_stats(model_path, stats_path, config_path, device):
    """Загрузка модели, статистики нормализации и конфигурации"""
    print(f"Загрузка модели из {model_path}")
    print(f"Загрузка статистики из {stats_path}")
    print(f"Загрузка конфигурации из {config_path}")
    
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    input_dim = config['input_dim']
    output_dim = config['output_dim']
    n_input_levels = config['n_variables']  # Будет 5
    n_output_levels = config.get('n_output_levels', len(config['output_levels']))
    
    # ИСПРАВЛЕНИЕ: правильные параметры для MultiHeadAtmosphericResNet
    n_input_levels = len(config['input_levels'])
    n_output_levels = len(config['output_levels'])
    
    print(f"Конфигурация:")
    print(f"  input_dim={input_dim}, output_dim={output_dim}")
    print(f"  n_input_levels={n_input_levels}, n_output_levels={n_output_levels}")
    
    # Создаем модель с правильными параметрами
    model = MultiHeadAtmosphericResNet(
        input_dim=input_dim,
        output_dim=output_dim,
        n_input_levels=n_input_levels,
        n_output_levels=n_output_levels,
        dropout_rate=0.2  # Используется в MultiHeadAtmosphericResNet
    )
    
    # Загружаем веса
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()  # Переводим в режим inference (вместо model.train(False))
    
    print(f"Модель загружена (эпоха {checkpoint['epoch']})")
    print(f"  Val Loss: {checkpoint.get('val_loss', 'N/A')}")
    print(f"  Параметров: {sum(p.numel() for p in model.parameters()):,}")
    
    return model, stats, config, checkpoint


def collect_predictions(model, stats, data_file, input_levels, output_levels, device, max_samples=50):
    """Сбор предсказаний модели"""
    VAR_NAMES = ['t', 'r', 'z', 'u', 'v']

    # Variable name mapping
    var_mapping = {
        't': 'temperature',
        'r': 'relative_humidity',
        'z': 'geopotential',
        'u': 'u_component_of_wind',
        'v': 'v_component_of_wind'
    }

    ds = xr.open_dataset(data_file)

    # Detect coordinates
    time_dim = 'valid_time' if 'valid_time' in ds.dims else 'time'
    level_dim = 'pressure_level' if 'pressure_level' in ds.dims else ('lev' if 'lev' in ds.dims else 'level')
    lat_dim = 'latitude' if 'latitude' in ds.dims else 'lat'
    lon_dim = 'longitude' if 'longitude' in ds.dims else 'lon'

    predictions = []
    targets = []
    inputs = []
    metadata = []  # Store time, lat, lon for each sample

    print(f"Сбор данных из {data_file}...")

    # Get dataset dimensions
    n_lat = len(ds[lat_dim])
    n_lon = len(ds[lon_dim])

    sample_count = 0
    # Sample more points to find valid profiles
    for lat_idx in range(0, n_lat, max(1, n_lat // 30)):
        for lon_idx in range(0, n_lon, max(1, n_lon // 40)):
            if sample_count >= max_samples:
                break

            # Extract input PER VARIABLE
            input_data_per_var = {}
            for var_internal in VAR_NAMES:
                var_dataset = var_mapping[var_internal]
                if var_dataset not in ds:
                    continue

                var_input = []
                for level in input_levels:
                    try:
                        # Use sel() with method='nearest' for pressure level (float32 precision)
                        value = float(ds[var_dataset].isel({
                            time_dim: 0,
                            lat_dim: lat_idx,
                            lon_dim: lon_idx
                        }).sel({
                            level_dim: level
                        }, method='nearest').values)
                        # Skip profile if value is NaN (below surface)
                        if np.isnan(value):
                            var_input = None
                            break
                        var_input.append(value)
                    except (ValueError, KeyError):
                        var_input = None
                        break

                if var_input is None:
                    break
                input_data_per_var[var_internal] = np.array(var_input, dtype=np.float32)

            if len(input_data_per_var) != len(VAR_NAMES):
                continue  # Skip this profile if incomplete

            # Extract target PER VARIABLE
            output_data_per_var = {}
            for var_internal in VAR_NAMES:
                var_dataset = var_mapping[var_internal]
                var_output = []
                for level in output_levels:
                    try:
                        value = float(ds[var_dataset].isel({
                            time_dim: 0,
                            lat_dim: lat_idx,
                            lon_dim: lon_idx
                        }).sel({
                            level_dim: level
                        }, method='nearest').values)
                        # Skip profile if value is NaN
                        if np.isnan(value):
                            var_output = None
                            break
                        var_output.append(value)
                    except (ValueError, KeyError):
                        var_output = None
                        break

                if var_output is None:
                    break
                output_data_per_var[var_internal] = np.array(var_output, dtype=np.float32)

            if len(output_data_per_var) != len(VAR_NAMES):
                continue  # Skip this profile if incomplete

            # Normalize input PER VARIABLE
            input_norm = []
            for var in VAR_NAMES:
                var_data = input_data_per_var[var]
                var_norm = (var_data - stats[var]['input_mean']) / (stats[var]['input_std'] + 1e-8)
                input_norm.extend(var_norm)

            input_norm = np.array(input_norm, dtype=np.float32)

            # Predict
            input_tensor = torch.from_numpy(input_norm).float().unsqueeze(0).to(device)
            with torch.no_grad():
                output_pred_norm = model(input_tensor).cpu().numpy()[0]

            # Denormalize prediction PER VARIABLE
            output_pred_per_var = {}
            idx = 0
            for var in VAR_NAMES:
                n_levels = len(output_levels)
                var_pred_norm = output_pred_norm[idx:idx+n_levels]
                var_pred = var_pred_norm * (stats[var]['output_std'] + 1e-8) + stats[var]['output_mean']
                output_pred_per_var[var] = var_pred
                idx += n_levels

            # Flatten for storage
            output_pred_flat = np.concatenate([output_pred_per_var[var] for var in VAR_NAMES])
            output_target_flat = np.concatenate([output_data_per_var[var] for var in VAR_NAMES])
            input_raw_flat = np.concatenate([input_data_per_var[var] for var in VAR_NAMES])

            predictions.append(output_pred_flat)
            targets.append(output_target_flat)
            inputs.append(input_raw_flat)

            # Save metadata
            time_value = ds[time_dim].isel({time_dim: 0}).values
            lat_value = float(ds[lat_dim].isel({lat_dim: lat_idx}).values)
            lon_value = float(ds[lon_dim].isel({lon_dim: lon_idx}).values)
            metadata.append({
                'time': str(time_value),
                'lat': lat_value,
                'lon': lon_value,
                'lat_idx': lat_idx,
                'lon_idx': lon_idx
            })

            sample_count += 1

        if sample_count >= max_samples:
            break

    ds.close()

    return np.array(predictions), np.array(targets), np.array(inputs), metadata


def create_scatter_plots(predictions, targets, output_levels, output_dir):
    """Создание графиков рассеяния для каждой переменной"""
    print("\nСоздание графиков рассеяния...")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    n_levels = len(output_levels)
    var_names = ['T', 'R', 'Z', 'U', 'V']
    var_labels = ['Температура', 'Отн. влажность', 'Геопотенциал', 'Зональный ветер', 'Меридиональный ветер']
    var_units = ['K', '%', 'м²/с²', 'м/с', 'м/с']

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    for i, (var_name, var_label, var_unit) in enumerate(zip(var_names, var_labels, var_units)):
        var_pred = predictions[:, i*n_levels:(i+1)*n_levels].flatten()
        var_target = targets[:, i*n_levels:(i+1)*n_levels].flatten()

        axes[i].scatter(var_target, var_pred, alpha=0.4, s=10, color='blue', edgecolors='none')
        axes[i].plot([var_target.min(), var_target.max()],
                     [var_target.min(), var_target.max()],
                     'r--', linewidth=2, label='Идеальное соответствие')

        r2 = 1 - np.sum((var_pred - var_target) ** 2) / np.sum((var_target - np.mean(var_target)) ** 2)
        rmse = np.sqrt(np.mean((var_pred - var_target) ** 2))

        axes[i].set_title(f'{var_label} ({var_name})\nR² = {r2:.4f}, RMSE = {rmse:.2f} {var_unit}',
                         fontsize=13, fontweight='bold')
        axes[i].set_xlabel(f'Фактические значения ({var_unit})', fontsize=11)
        axes[i].set_ylabel(f'Предсказания ({var_unit})', fontsize=11)
        axes[i].legend(fontsize=10)
        axes[i].grid(True, alpha=0.3)

    axes[5].axis('off')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/scatter_variables_ru.png', dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Сохранено: {output_dir}/scatter_variables_ru.png")


def create_rmse_by_level(predictions, targets, output_levels, output_dir):
    """График RMSE температуры по уровням давления"""
    print("Создание графика RMSE по уровням...")

    n_levels = len(output_levels)

    fig, ax = plt.subplots(figsize=(10, 7))

    rmse_by_level = []
    for level_idx in range(n_levels):
        t_pred = predictions[:, level_idx]
        t_target = targets[:, level_idx]
        rmse = np.sqrt(np.mean((t_pred - t_target) ** 2))
        rmse_by_level.append(rmse)

    ax.plot(output_levels, rmse_by_level, 'o-', linewidth=2.5, markersize=10, color='darkblue')
    ax.axhline(y=5.0, color='red', linestyle='--', linewidth=2, label='Целевой порог (5K)')
    ax.set_xlabel('Уровень давления (гПа)', fontsize=13, fontweight='bold')
    ax.set_ylabel('RMSE температуры (K)', fontsize=13, fontweight='bold')
    ax.set_title('Среднеквадратичная ошибка температуры по уровням атмосферы',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.invert_xaxis()
    ax.legend(fontsize=11)

    # Аннотации со значениями
    for level, rmse in zip(output_levels, rmse_by_level):
        ax.annotate(f'{rmse:.2f}K', xy=(level, rmse), xytext=(0, 8),
                   textcoords='offset points', ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/rmse_by_level_ru.png', dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Сохранено: {output_dir}/rmse_by_level_ru.png")


def create_vertical_profiles(predictions, targets, inputs, input_levels, output_levels, metadata, output_dir, n_samples=10):
    """Создание вертикальных профилей атмосферы от 100 гПа до 0.1 гПа"""
    print(f"Создание вертикальных профилей ({n_samples} примеров) от 100 гПа до 0.1 гПа...")

    n_levels_out = len(output_levels)
    n_levels_in = len(input_levels)

    var_names = ['T', 'R', 'Z', 'U', 'V']
    var_labels = ['Температура', 'Отн. влажность', 'Геопотенциал', 'Зональный ветер', 'Меридиональный ветер']
    var_units = ['K', '%', 'м²/с²', 'м/с', 'м/с']

    # Определить диапазон для визуализации: от 100 гПа до 0.1 гПа (показать стык на 100 гПа)
    # Найти индексы входных уровней <= 100 гПа (включая 100 гПа)
    input_levels_filtered_idx = [i for i, lev in enumerate(input_levels) if lev <= 100]
    input_levels_filtered = [input_levels[i] for i in input_levels_filtered_idx]

    # Все выходные уровни уже в нужном диапазоне
    display_levels = input_levels_filtered + output_levels

    # Выбрать случайные примеры
    sample_indices = np.random.choice(len(predictions), min(n_samples, len(predictions)), replace=False)

    for sample_idx in sample_indices:
        meta = metadata[sample_idx]

        fig, axes = plt.subplots(1, 5, figsize=(25, 8))

        # Заголовок с метаданными
        time_str = meta['time'][:19] if len(meta['time']) > 19 else meta['time']  # Обрезать доли секунд
        title = (f'Вертикальный профиль атмосферы (100-0.1 гПа)\n'
                f'Время: {time_str} UTC | '
                f'Координаты: {meta["lat"]:.2f}°N, {meta["lon"]:.2f}°E')
        fig.suptitle(title, fontsize=16, fontweight='bold')

        for var_idx, (var_name, var_label, var_unit) in enumerate(zip(var_names, var_labels, var_units)):
            ax = axes[var_idx]

            # Входные данные
            input_var_full = inputs[sample_idx, var_idx*n_levels_in:(var_idx+1)*n_levels_in]
            input_var = [input_var_full[i] for i in input_levels_filtered_idx]

            # Предсказания (верхние уровни)
            pred_var = predictions[sample_idx, var_idx*n_levels_out:(var_idx+1)*n_levels_out]

            # Реальные данные (верхние уровни)
            target_var = targets[sample_idx, var_idx*n_levels_out:(var_idx+1)*n_levels_out]

            # Построение профилей
            ax.plot(input_var, input_levels_filtered, 'ko-', linewidth=2.5, markersize=8,
                   label='Входные данные', zorder=3)
            ax.plot(target_var, output_levels, 'r^--', linewidth=2.5, markersize=9,
                   label='Реанализ', alpha=0.8, zorder=2)
            ax.plot(pred_var, output_levels, 'bs-', linewidth=2.5, markersize=8,
                   label='Предсказание ML', alpha=0.8, zorder=1)

            ax.set_xlabel(f'{var_label} ({var_unit})', fontsize=13, fontweight='bold')
            ax.set_ylabel('Давление (гПа) / Высота ↑', fontsize=13, fontweight='bold')
            ax.set_title(f'{var_name}', fontsize=15, fontweight='bold')
            ax.set_yscale('log')  # Логарифмическая шкала для давления

            # 0.1 гПа вверху (верхние слои), 100 гПа внизу (нижние слои)
            ax.set_ylim([0.08, 120])  # Меньшее давление = выше в атмосфере
            ax.invert_yaxis()  # Инверсия чтобы малые значения были вверху

            ax.grid(True, alpha=0.3, which='both')
            ax.legend(fontsize=10, loc='best')

            # Настроить метки оси Y (от 100 гПа до 0.1 гПа)
            yticks = [100, 70, 50, 30, 20, 10, 5, 3, 2, 1, 0.7, 0.5, 0.3, 0.1]
            ax.set_yticks(yticks)
            ax.set_yticklabels([str(y) for y in yticks])

            # Добавить разделительную линию на 100 гПа (граница входных/выходных)
            # Только если 100 гПа входит в диапазон визуализации
            if 100 in input_levels_filtered or min(output_levels) <= 100 <= max(output_levels):
                ax.axhline(y=100, color='gray', linestyle='--', linewidth=2, alpha=0.6)

            # Добавить метки слоев атмосферы
            if var_idx == 0:  # Только на первом графике
                ax.text(0.02, 0.95, 'Прогноз ML\n(< 100 гПа)',
                       transform=ax.transAxes, fontsize=9,
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
                ax.text(0.02, 0.05, 'Входные данные\n(100 гПа)',
                       transform=ax.transAxes, fontsize=9,
                       verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

        plt.tight_layout()
        plt.savefig(f'{output_dir}/vertical_profile_{sample_idx}_100-0.1hPa_ru.png', dpi=200, bbox_inches='tight')
        plt.close()

    print(f"  ✓ Сохранено: {n_samples} вертикальных профилей (100-0.1 гПа)")


def create_error_heatmap(predictions, targets, output_levels, output_dir):
    """Тепловая карта ошибок по переменным и уровням"""
    print("Создание тепловой карты ошибок...")

    n_levels = len(output_levels)
    var_names = ['T', 'R', 'Z', 'U', 'V']
    var_labels = ['Темп.', 'Влажн.', 'Геопот.', 'U-ветер', 'V-ветер']

    # Вычислить RMSE для каждой переменной и уровня
    rmse_matrix = np.zeros((len(var_names), n_levels))

    for var_idx in range(len(var_names)):
        for level_idx in range(n_levels):
            var_pred = predictions[:, var_idx*n_levels + level_idx]
            var_target = targets[:, var_idx*n_levels + level_idx]
            rmse_matrix[var_idx, level_idx] = np.sqrt(np.mean((var_pred - var_target) ** 2))

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(rmse_matrix, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(np.arange(n_levels))
    ax.set_yticks(np.arange(len(var_names)))
    ax.set_xticklabels([f'{level:.0f}' for level in output_levels], fontsize=10)
    ax.set_yticklabels(var_labels, fontsize=11, fontweight='bold')

    ax.set_xlabel('Уровень давления (гПа)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Переменная', fontsize=12, fontweight='bold')
    ax.set_title('Тепловая карта RMSE по переменным и уровням',
                fontsize=14, fontweight='bold')

    # Добавить значения в ячейки
    for i in range(len(var_names)):
        for j in range(n_levels):
            text = ax.text(j, i, f'{rmse_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=8)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('RMSE', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/error_heatmap_ru.png', dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Сохранено: {output_dir}/error_heatmap_ru.png")


def main(model_dir='./training_era5_extended', data_dir=None):
    """
    Создание визуализаций результатов модели.

    Args:
        model_dir: Директория с моделью (best_model.pth, normalization_stats.json, config.json)
        data_dir: Директория с данными (автоопределяется из конфигурации если None)
    """
    model_path = os.path.join(model_dir, 'best_model.pth')
    stats_path = os.path.join(model_dir, 'normalization_stats.json')
    config_path = os.path.join(model_dir, 'config.json')
    output_dir = os.path.join(model_dir, 'visualizations')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Устройство: {device}\n")

    # Загрузить модель и конфигурацию
    model, stats, config, checkpoint = load_model_and_stats(model_path, stats_path, config_path, device)

    # Извлечь параметры из конфигурации
    INPUT_LEVELS = config['input_levels']
    OUTPUT_LEVELS = config['output_levels']
    DATA_SOURCE = config.get('data_source', 'ERA5')

    # Автоопределение директории данных
    if data_dir is None:
        # Попробовать несколько возможных расположений
        possible_paths = [
            f'./data/{DATA_SOURCE.lower()}',
            f'./experiments/data/{DATA_SOURCE.lower()}',
            f'../data/{DATA_SOURCE.lower()}'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                data_dir = path
                break
        else:
            data_dir = f'./data/{DATA_SOURCE.lower()}'  # По умолчанию

    print(f"\nИсточник данных: {DATA_SOURCE}")
    print(f"Директория данных: {data_dir}")
    print(f"Входные уровни: {INPUT_LEVELS[0]} - {INPUT_LEVELS[-1]} гПа ({len(INPUT_LEVELS)} уровней)")
    print(f"Выходные уровни: {OUTPUT_LEVELS[0]} - {OUTPUT_LEVELS[-1]} гПа ({len(OUTPUT_LEVELS)} уровней)")

    # Найти тестовый файл
    data_files = sorted([
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith('.nc')
    ])

    if not data_files:
        print(f"ОШИБКА: Нет файлов данных в {data_dir}!")
        return

    print(f"\nИспользуется файл: {data_files[0]}\n")

    # Собрать предсказания
    predictions, targets, inputs, metadata = collect_predictions(
        model, stats, data_files[0], INPUT_LEVELS, OUTPUT_LEVELS, device, max_samples=50
    )

    print(f"\nСобрано {len(predictions)} примеров\n")
    print("="*70)

    # Создать директорию для визуализаций
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Создать базовые графики
    create_scatter_plots(predictions, targets, OUTPUT_LEVELS, output_dir)
    create_rmse_by_level(predictions, targets, OUTPUT_LEVELS, output_dir)
    create_vertical_profiles(predictions, targets, inputs, INPUT_LEVELS, OUTPUT_LEVELS, metadata, output_dir, n_samples=10)
    create_error_heatmap(predictions, targets, OUTPUT_LEVELS, output_dir)

    # Вычислить детальные метрики для научного анализа
    print("\n" + "="*70)
    print("РАСШИРЕННЫЙ НАУЧНЫЙ АНАЛИЗ ОШИБОК")
    print("="*70)

    metrics = compute_detailed_metrics(predictions, targets, len(OUTPUT_LEVELS))

    # Вывести сводку метрик
    print("\nСводка метрик на тестовой выборке:")
    print("-" * 70)
    for var_name in ['T', 'R', 'Z', 'U', 'V']:
        m = metrics[var_name]
        print(f"{var_name:5s} | RMSE: {m['rmse_global']:8.4f} | MAE: {m['mae_global']:8.4f} | "
              f"Bias: {m['bias_global']:8.4f} | R²: {m['r2_global']:7.4f} | "
              f"r: {m['corr_global']:7.4f}")
    print("-" * 70)

    # Создать научные визуализации
    create_scientific_error_profiles(metrics, OUTPUT_LEVELS, output_dir)
    create_metrics_table(metrics, output_dir)

    print("\n" + "="*70)
    print(f"✓ Все визуализации сохранены в: {output_dir}/")
    print(f"  - Scatter plots (temperature, RH, geopotential, winds)")
    print(f"  - RMSE по уровням давления (до {OUTPUT_LEVELS[-1]} гПа)")
    print(f"  - Вертикальные профили (10 примеров, диапазон 100-0.1 гПа)")
    print(f"  - Тепловая карта ошибок")
    print(f"  - Научные профили ошибок RMSE/MAE/Bias по высотам ⭐")
    print(f"  - Сводная таблица метрик (PNG + CSV) ⭐")
    print("="*70)


if __name__ == '__main__':
    main(model_dir='./training_merra2_extended')

# ============================================================================
# РАСШИРЕННЫЙ НАУЧНЫЙ АНАЛИЗ ОШИБОК (добавлено)
# ============================================================================

def compute_detailed_metrics(predictions, targets, n_levels):
    """Расчёт детальных метрик ошибок"""
    from scipy import stats as scipy_stats
    
    var_names = ['T', 'R', 'Z', 'U', 'V']
    metrics = {}
    
    for var_idx, var_name in enumerate(var_names):
        var_pred = predictions[:, var_idx*n_levels:(var_idx+1)*n_levels]
        var_target = targets[:, var_idx*n_levels:(var_idx+1)*n_levels]
        errors = var_pred - var_target
        
        # Глобальные метрики
        rmse_global = np.sqrt(np.mean(errors**2))
        mae_global = np.mean(np.abs(errors))
        bias_global = np.mean(errors)
        
        # R² и корреляция
        ss_res = np.sum(errors**2)
        ss_tot = np.sum((var_target - np.mean(var_target))**2)
        r2_global = 1 - (ss_res / (ss_tot + 1e-8))
        corr_global = np.corrcoef(var_target.flatten(), var_pred.flatten())[0, 1]
        
        # По уровням
        rmse_by_level = np.sqrt(np.mean((var_pred - var_target)**2, axis=0))
        mae_by_level = np.mean(np.abs(var_pred - var_target), axis=0)
        bias_by_level = np.mean(var_pred - var_target, axis=0)
        std_by_level = np.std(var_pred - var_target, axis=0)
        
        metrics[var_name] = {
            'rmse_global': rmse_global,
            'mae_global': mae_global,
            'bias_global': bias_global,
            'r2_global': r2_global,
            'corr_global': corr_global,
            'rmse_by_level': rmse_by_level,
            'mae_by_level': mae_by_level,
            'bias_by_level': bias_by_level,
            'std_by_level': std_by_level,
            'errors': errors
        }
    
    return metrics


def create_scientific_error_profiles(metrics, output_levels, output_dir):
    """Научные вертикальные профили ошибок"""
    from matplotlib.gridspec import GridSpec
    
    print("Создание научных профилей ошибок...")
    
    var_names = ['T', 'R', 'Z', 'U', 'V']
    var_labels = ['Температура', 'Отн. влажность', 'Геопотенциал', 'U-ветер', 'V-ветер']
    var_units = ['K', '%', 'м²/с²', 'м/с', 'м/с']
    
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 5, figure=fig, hspace=0.35, wspace=0.3)
    
    for var_idx, (var_name, var_label, var_unit) in enumerate(zip(var_names, var_labels, var_units)):
        m = metrics[var_name]
        
        # RMSE
        ax_rmse = fig.add_subplot(gs[0, var_idx])
        ax_rmse.plot(m['rmse_by_level'], output_levels, 'o-', linewidth=2.5, markersize=8, color='darkred')
        ax_rmse.set_xlabel(f'RMSE ({var_unit})', fontsize=11, fontweight='bold')
        ax_rmse.set_ylabel('Давление (гПа)', fontsize=11, fontweight='bold')
        ax_rmse.set_title(f'{var_label}\\nRMSE={m["rmse_global"]:.3f} {var_unit}', fontsize=12, fontweight='bold')
        ax_rmse.set_yscale('log')
        ax_rmse.set_ylim([0.08, 120])
        ax_rmse.invert_yaxis()
        ax_rmse.grid(True, alpha=0.3, which='both')
        ax_rmse.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)
        
        # MAE
        ax_mae = fig.add_subplot(gs[1, var_idx])
        ax_mae.plot(m['mae_by_level'], output_levels, 's-', linewidth=2.5, markersize=8, color='darkblue')
        ax_mae.set_xlabel(f'MAE ({var_unit})', fontsize=11, fontweight='bold')
        ax_mae.set_ylabel('Давление (гПа)', fontsize=11, fontweight='bold')
        ax_mae.set_title(f'MAE={m["mae_global"]:.3f} {var_unit}', fontsize=12, fontweight='bold')
        ax_mae.set_yscale('log')
        ax_mae.set_ylim([0.08, 120])
        ax_mae.invert_yaxis()
        ax_mae.grid(True, alpha=0.3, which='both')
        ax_mae.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)
        
        # Bias ± Std
        ax_bias = fig.add_subplot(gs[2, var_idx])
        ax_bias.plot(m['bias_by_level'], output_levels, '^-', linewidth=2.5, markersize=8, color='darkgreen')
        ax_bias.fill_betweenx(output_levels,
                              m['bias_by_level'] - m['std_by_level'],
                              m['bias_by_level'] + m['std_by_level'],
                              alpha=0.2, color='green', label='±1σ')
        ax_bias.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
        ax_bias.set_xlabel(f'Bias ({var_unit})', fontsize=11, fontweight='bold')
        ax_bias.set_ylabel('Давление (гПа)', fontsize=11, fontweight='bold')
        ax_bias.set_title(f'Bias={m["bias_global"]:.3f} {var_unit}', fontsize=12, fontweight='bold')
        ax_bias.set_yscale('log')
        ax_bias.set_ylim([0.08, 120])
        ax_bias.invert_yaxis()
        ax_bias.grid(True, alpha=0.3, which='both')
        ax_bias.axhline(y=100, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)
        ax_bias.legend(fontsize=9, loc='best')
    
    fig.suptitle('Вертикальные профили ошибок (RMSE, MAE, Bias) по высотам 100-0.1 гПа',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig(f'{output_dir}/scientific_error_profiles_ru.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Сохранено: {output_dir}/scientific_error_profiles_ru.png")


def create_metrics_table(metrics, output_dir):
    """Сводная таблица метрик"""
    import pandas as pd
    
    print("Создание сводной таблицы метрик...")
    
    var_names = ['T', 'R', 'Z', 'U', 'V']
    var_labels = ['Температура (K)', 'Отн. влажность (%)', 'Геопотенциал (м²/с²)',
                  'Зональный ветер (м/с)', 'Меридиональный ветер (м/с)']
    
    data = []
    for var_name, var_label in zip(var_names, var_labels):
        m = metrics[var_name]
        data.append([
            var_label,
            f"{m['rmse_global']:.4f}",
            f"{m['mae_global']:.4f}",
            f"{m['bias_global']:.4f}",
            f"{m['r2_global']:.4f}",
            f"{m['corr_global']:.4f}"
        ])
    
    columns = ['Переменная', 'RMSE', 'MAE', 'Bias', 'R²', 'Корреляция']
    df = pd.DataFrame(data, columns=columns)
    
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=df.values, colLabels=df.columns,
                    cellLoc='center', loc='center',
                    colWidths=[0.28, 0.14, 0.14, 0.14, 0.14, 0.16])
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    for i in range(len(columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#4472C4')
        cell.set_text_props(weight='bold', color='white', fontsize=12)
    
    for i in range(1, len(data) + 1):
        for j in range(len(columns)):
            cell = table[(i, j)]
            cell.set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
    
    plt.title('Сводная таблица метрик качества модели на тестовой выборке',
              fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig(f'{output_dir}/metrics_summary_table_ru.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    df.to_csv(f'{output_dir}/metrics_summary.csv', index=False, encoding='utf-8-sig')
    print(f"  ✓ Сохранено: {output_dir}/metrics_summary_table_ru.png")
    print(f"  ✓ Сохранено: {output_dir}/metrics_summary.csv")
