"""
Validation with PER-VARIABLE denormalization.
This matches the per-variable normalization used in training.
Uses RELATIVE HUMIDITY (r) instead of specific humidity (q).
Supports both ERA5 and MERRA2 with extended levels to 0.1 hPa.
"""
import os
import json
import numpy as np
import xarray as xr
import torch

# from model_architecture import AtmosphericProfileResNet
from model_architecture import MultiHeadAtmosphericResNet


def load_model_and_stats(model_path, stats_path, config_path, device):
    """Load model, per-variable normalization statistics, and configuration"""
    print(f"Loading model from {model_path}")
    print(f"Loading normalization stats from {stats_path}")
    print(f"Loading configuration from {config_path}")

    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load statistics
    with open(stats_path, 'r') as f:
        stats = json.load(f)

    # Extract dimensions from config
    input_dim = config['input_dim']
    output_dim = config['output_dim']
    data_source = config.get('data_source', 'ERA5')
    n_input_levels = len(config['input_levels'])
    n_output_levels = len(config['output_levels'])

    print(f"\nConfiguration:")
    print(f"  Data source: {data_source}")
    print(f"  Input dimension: {input_dim}")
    print(f"  Output dimension: {output_dim}")
    print(f"  Input levels: {n_input_levels}")
    print(f"  Output levels: {n_output_levels}")

    # Load model with correct dimensions
    model = MultiHeadAtmosphericResNet(
        input_dim=input_dim,
        output_dim=output_dim,
        n_input_levels=n_input_levels,
        n_output_levels=n_output_levels,
        dropout_rate=0.2
    )

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.train(False)

    print(f"\nModel loaded (epoch {checkpoint['epoch']})")
    print(f"Per-variable normalization statistics:")
    for var in ['t', 'r', 'z', 'u', 'v']:
        print(f"  {var.upper()}: in_mean={stats[var]['input_mean']:.2f}, out_mean={stats[var]['output_mean']:.2f}")

    return model, stats, config, checkpoint


def validate_model(model_dir='./training_era5_extended',
                   data_dir=None):
    """
    Validate model with per-variable denormalization.

    Args:
        model_dir: Directory containing best_model.pth, normalization_stats.json, and config.json
        data_dir: Directory with validation data (auto-detected from config if None)
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}\n")

    # Construct file paths
    model_path = os.path.join(model_dir, 'best_model.pth')
    stats_path = os.path.join(model_dir, 'normalization_stats.json')
    config_path = os.path.join(model_dir, 'config.json')

    # Load model, stats, and config
    model, stats, config, checkpoint = load_model_and_stats(model_path, stats_path, config_path, device)

    # Extract configuration
    INPUT_LEVELS = config['input_levels']
    OUTPUT_LEVELS = config['output_levels']
    DATA_SOURCE = config.get('data_source', 'ERA5')
    VAR_NAMES = ['t', 'r', 'z', 'u', 'v']

    # Auto-detect data directory if not specified
    if data_dir is None:
        data_dir = f'./data/{DATA_SOURCE.lower()}'

    print(f"\nValidation configuration:")
    print(f"  Data source: {DATA_SOURCE}")
    print(f"  Data directory: {data_dir}")
    print(f"  Input levels: {INPUT_LEVELS[0]} to {INPUT_LEVELS[-1]} hPa ({len(INPUT_LEVELS)} levels)")
    print(f"  Output levels: {OUTPUT_LEVELS[0]} to {OUTPUT_LEVELS[-1]} hPa ({len(OUTPUT_LEVELS)} levels)")

    # Test on one file
    data_files = sorted([
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith('.nc')
    ])

    if len(data_files) == 0:
        print(f"ERROR: No data files found in {data_dir}")
        return None, None

    print(f"\nTesting on file: {data_files[0]}\n")

    ds = xr.open_dataset(data_files[0])

    # Detect coordinates
    time_dim = 'valid_time' if 'valid_time' in ds.dims else 'time'
    level_dim = 'pressure_level' if 'pressure_level' in ds.dims else ('lev' if 'lev' in ds.dims else 'level')
    lat_dim = 'latitude' if 'latitude' in ds.dims else 'lat'
    lon_dim = 'longitude' if 'longitude' in ds.dims else 'lon'

    # Variable name mapping (MERRA2 variables are renamed in download to match ERA5)
    var_mapping = {
        't': 'temperature',
        'r': 'relative_humidity',
        'z': 'geopotential',
        'u': 'u_component_of_wind',
        'v': 'v_component_of_wind'
    }

    # Test predictions
    predictions = []
    targets = []
    inputs_raw = []

    print("Running predictions...")

    # Get dataset dimensions for sampling
    n_lat = len(ds[lat_dim])
    n_lon = len(ds[lon_dim])

    # Sample points - use smaller stride and more attempts to find valid profiles
    samples_collected = 0
    max_samples = 50  # Target number of samples

    for lat_idx in range(0, n_lat, max(1, n_lat // 30)):  # Sample more points
        for lon_idx in range(0, n_lon, max(1, n_lon // 40)):
            if samples_collected >= max_samples:
                break
            # Extract input PER VARIABLE
            input_data_per_var = {}
            for var_internal in VAR_NAMES:
                var_dataset = var_mapping[var_internal]
                if var_dataset not in ds:
                    print(f"WARNING: Variable {var_dataset} not found in dataset, skipping...")
                    continue

                var_input = []
                for level in INPUT_LEVELS:
                    try:
                        # Use sel() with method='nearest' for pressure level (float32 precision)
                        # Use isel() for time/lat/lon indices
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
                    except (ValueError, KeyError) as e:
                        print(f"WARNING: Level {level} not found, skipping profile...")
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
                for level in OUTPUT_LEVELS:
                    try:
                        # Use sel() with method='nearest' for pressure level (float32 precision)
                        # Use isel() for time/lat/lon indices
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
                    except (ValueError, KeyError) as e:
                        print(f"WARNING: Output level {level} not found, skipping profile...")
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
                n_levels = len(OUTPUT_LEVELS)
                var_pred_norm = output_pred_norm[idx:idx+n_levels]
                var_pred = var_pred_norm * (stats[var]['output_std'] + 1e-8) + stats[var]['output_mean']
                output_pred_per_var[var] = var_pred
                idx += n_levels

            # Flatten for comparison
            output_pred_flat = np.concatenate([output_pred_per_var[var] for var in VAR_NAMES])
            output_target_flat = np.concatenate([output_data_per_var[var] for var in VAR_NAMES])
            input_raw_flat = np.concatenate([input_data_per_var[var] for var in VAR_NAMES])

            predictions.append(output_pred_flat)
            targets.append(output_target_flat)
            inputs_raw.append(input_raw_flat)
            samples_collected += 1

        if samples_collected >= max_samples:
            break

    predictions = np.array(predictions)
    targets = np.array(targets)
    inputs_raw = np.array(inputs_raw)

    ds.close()

    # Compute PHYSICAL metrics
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS (PHYSICAL UNITS)")
    print(f"{'='*70}")
    print(f"Test samples: {len(predictions)}")

    # Overall RMSE
    overall_rmse = np.sqrt(np.mean((predictions - targets) ** 2))
    overall_mae = np.mean(np.abs(predictions - targets))
    print(f"\nOverall RMSE: {overall_rmse:.4f}")
    print(f"Overall MAE: {overall_mae:.4f}")

    # Temperature RMSE (first 10 elements per sample)
    n_levels = len(OUTPUT_LEVELS)
    temp_pred = predictions[:, :n_levels]
    temp_target = targets[:, :n_levels]

    temp_rmse = np.sqrt(np.mean((temp_pred - temp_target) ** 2))
    temp_mae = np.mean(np.abs(temp_pred - temp_target))

    print(f"\nTemperature (T):")
    print(f"  RMSE: {temp_rmse:.2f} K  <- MUST BE < 5 K!")
    print(f"  MAE:  {temp_mae:.2f} K")
    print(f"  Min prediction: {temp_pred.min():.2f} K")
    print(f"  Max prediction: {temp_pred.max():.2f} K")
    print(f"  Min target: {temp_target.min():.2f} K")
    print(f"  Max target: {temp_target.max():.2f} K")

    # RMSE by level
    print(f"\nTemperature RMSE by pressure level:")
    for i, level in enumerate(OUTPUT_LEVELS):
        level_rmse = np.sqrt(np.mean((temp_pred[:, i] - temp_target[:, i]) ** 2))
        print(f"  {level:>5.1f} hPa: {level_rmse:>6.2f} K")

    # Metrics for other variables
    var_idx = 0
    for var_name, var_label in [('r', 'Relative Humidity'), ('z', 'Geopotential'),
                                  ('u', 'Zonal Wind'), ('v', 'Meridional Wind')]:
        var_idx += 1  # Skip temperature (var_idx=0)
        var_pred = predictions[:, var_idx*n_levels:(var_idx+1)*n_levels]
        var_target = targets[:, var_idx*n_levels:(var_idx+1)*n_levels]

        var_rmse = np.sqrt(np.mean((var_pred - var_target) ** 2))
        var_mae = np.mean(np.abs(var_pred - var_target))

        print(f"\n{var_label} ({var_name.upper()}):")
        print(f"  RMSE: {var_rmse:.6f}")
        print(f"  MAE:  {var_mae:.6f}")

    print(f"\n{'='*70}")

    if temp_rmse < 5.0:
        print("✓ SUCCESS! Temperature RMSE < 5K - model works correctly!")
    elif temp_rmse < 20.0:
        print(f"⚠ WARNING! Temperature RMSE {temp_rmse:.2f}K - acceptable but can be improved")
    else:
        print(f"✗ ERROR! Temperature RMSE {temp_rmse:.2f}K - something is wrong!")

    print(f"{'='*70}\n")

    return predictions, targets


if __name__ == '__main__':
    validate_model(model_dir='./training_merra2_extended')
