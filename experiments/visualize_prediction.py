#!/usr/bin/env python3
"""
Visualization tool for Atmospheric Profile Prediction (0.1 hPa).
Loads a real sounding, predicts the upper atmosphere using the trained model,
and plots the combined Skew-T diagram.
"""

import sys
import os
import json
import torch
import numpy as np
import pandas as pd
import sounderpy as spy
import metpy.calc as mpcalc
from metpy.units import units
from metpy.plots import SkewT
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import argparse
from datetime import datetime

# Add current directory to path to import model_architecture
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # from model_architecture import AtmosphericProfileResNet
    from model_architecture import MultiHeadAtmosphericResNet
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.getcwd(), 'experiments'))
    # from model_architecture import AtmosphericProfileResNet
    from model_architecture import MultiHeadAtmosphericResNet

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_PATH = 'experiments/training_merra2_extended/config.json'
STATS_PATH = 'experiments/training_merra2_extended/normalization_stats.json'
MODEL_PATH = 'experiments/training_merra2_extended/best_model.pth'
STATION_CODE = '27612' # Moscow
DEFAULT_DATE = '2016-01-15 12:00'

# ============================================================================
# UTILS
# ============================================================================

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def load_stats():
    with open(STATS_PATH, 'r') as f:
        return json.load(f)

def calculate_rh(T_k, Td_k):
    """Calculate Relative Humidity (0-1) from Temperature and Dewpoint (Kelvin)."""
    # Magnus formula
    T_c = T_k - 273.15
    Td_c = Td_k - 273.15
    
    es = 6.112 * np.exp(17.67 * T_c / (T_c + 243.5))
    e = 6.112 * np.exp(17.67 * Td_c / (Td_c + 243.5))
    rh = e / es
    return np.clip(rh, 0, 1)

def dewpoint_from_rh(T_k, rh):
    """Calculate Dewpoint (Kelvin) from Temperature (K) and RH (0-1)."""
    T_c = T_k - 273.15
    rh = np.clip(rh, 0.001, 1.0) # Avoid log(0)
    
    # Magnus formula inversion
    # ln(RH/100) = ln(e/es)
    # es = 6.112 * exp(...)
    # e = es * RH
    # Td = ...
    
    # Using metpy if available is easier, but let's stick to numpy for speed/compat
    # approximation
    b = 17.67
    c = 243.5
    
    gamma = np.log(rh) + (b * T_c) / (c + T_c)
    Td_c = (c * gamma) / (b - gamma)
    return Td_c + 273.15

# ============================================================================
# DATA PROCESSING
# ============================================================================

def get_real_sounding(station, date_str):
    """Download sounding data using sounderpy."""
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    print(f"Downloading sounding for {station} at {dt}...")
    
    try:
        clean_data = spy.get_obs_data(station, dt.year, dt.month, dt.day, dt.hour, hush=True)
        return clean_data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def preprocess_sounding(clean_data, config, stats):
    """Interpolate sounding to input levels and normalize."""
    
    # Extract data
    p = clean_data['p'].magnitude # hPa
    z = clean_data['z'].magnitude # meters
    T = clean_data['T'].magnitude # Kelvin
    Td = clean_data['Td'].magnitude # Kelvin
    u = clean_data['u'].magnitude # m/s
    v = clean_data['v'].magnitude # m/s
    
    # Calculate RH
    rh = calculate_rh(T, Td)
    
    # Target input levels
    input_levels = np.array(config['input_levels'])
    
    # Interpolation functions
    # Use log-p for interpolation
    log_p = np.log(p)
    log_target_p = np.log(input_levels)
    
    def interp(values):
        f = interp1d(log_p, values, kind='linear', bounds_error=False, fill_value='extrapolate')
        return f(log_target_p)
    
    T_interp = interp(T)
    rh_interp = interp(rh)
    z_interp = interp(z)
    u_interp = interp(u)
    v_interp = interp(v)
    
    # Convert Z to Geopotential (m^2/s^2)
    z_geo = z_interp * 9.80665
    
    # Normalize
    input_features = []
    
    # Order: T, R, Z, U, V per level? Or all T, then all R?
    # Usually models take [batch, features].
    # Need to check model expectation. 
    # Based on config "input_dim": 145 and "n_variables": 5 -> 29 levels * 5.
    # Usually it's flattened: level1_vars, level2_vars... OR var1_all_levels...
    # Let's assume (based on typical ML) it's likely flattened per level or per var.
    # Looking at architecture: input_dim=120. Linear(120, ...).
    # I'll assume the order is: T(all), R(all), Z(all), U(all), V(all) OR interleaved.
    # Re-reading model_architecture.py... it doesn't specify.
    # But usually creating datasets involves flattening. 
    # Let's assume `T[level1], T[level2]... R[level1]...` (Channel first-ish) OR `T[l1], R[l1]...` (Level first).
    #
    # Wait, `AtmosphericProfileResNet` takes [batch, 120].
    # Let's check `config.json` again. input_dim 145. 29 levels.
    #
    # Let's check `normalization_stats`. keys are "t", "r", "z", "u", "v".
    # I will assume the standard concatenation order: T, R, Z, U, V (all levels concatenated for each).
    # i.e. [T_1...T_29, R_1...R_29, ...]
    
    norm_data = []
    
    # T
    t_mean, t_std = stats['t']['input_mean'], stats['t']['input_std']
    norm_data.extend((T_interp - t_mean) / t_std)
    
    # R
    r_mean, r_std = stats['r']['input_mean'], stats['r']['input_std']
    norm_data.extend((rh_interp - r_mean) / r_std)
    
    # Z
    z_mean, z_std = stats['z']['input_mean'], stats['z']['input_std']
    norm_data.extend((z_geo - z_mean) / z_std)
    
    # U
    u_mean, u_std = stats['u']['input_mean'], stats['u']['input_std']
    norm_data.extend((u_interp - u_mean) / u_std)
    
    # V
    v_mean, v_std = stats['v']['input_mean'], stats['v']['input_std']
    norm_data.extend((v_interp - v_mean) / v_std)
    
    return np.array(norm_data, dtype=np.float32)

def postprocess_prediction(pred_tensor, config, stats):
    """Denormalize prediction and reshape."""
    pred = pred_tensor.cpu().numpy().flatten()
    n_levels = len(config['output_levels'])
    
    # Split by variable
    # Output dim 55 = 11 levels * 5 vars.
    # Assumed order: T, R, Z, U, V
    
    chunk_size = n_levels
    
    t_norm = pred[0:chunk_size]
    r_norm = pred[chunk_size:2*chunk_size]
    z_norm = pred[2*chunk_size:3*chunk_size]
    u_norm = pred[3*chunk_size:4*chunk_size]
    v_norm = pred[4*chunk_size:5*chunk_size]
    
    # Denormalize
    T = t_norm * stats['t']['output_std'] + stats['t']['output_mean']
    R = r_norm * stats['r']['output_std'] + stats['r']['output_mean']
    Z_geo = z_norm * stats['z']['output_std'] + stats['z']['output_mean']
    U = u_norm * stats['u']['output_std'] + stats['u']['output_mean']
    V = v_norm * stats['v']['output_std'] + stats['v']['output_mean']
    
    # Z geo to Z meters
    Z = Z_geo / 9.80665
    
    # R to Td
    Td = dewpoint_from_rh(T, R)
    
    return {
        'p': np.array(config['output_levels']),
        'T': T,
        'Td': Td,
        'z': Z,
        'u': U,
        'v': V
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Visualize Atmospheric Profile Prediction')
    parser.add_argument('--date', type=str, default=DEFAULT_DATE, help='Date YYYY-MM-DD HH:MM')
    parser.add_argument('--station', type=str, default=STATION_CODE, help='WMO Station Code')
    args = parser.parse_args()

    print(f"Loading config from {CONFIG_PATH}...")
    if not os.path.exists(CONFIG_PATH):
        print("❌ Config not found.")
        return
        
    config = load_config()
    stats = load_stats()
    
    # Load Model
    print(f"Loading model from {MODEL_PATH}...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = MultiHeadAtmosphericResNet(
        input_dim=config['input_dim'],
        output_dim=config['output_dim'],
        hidden_dims=config['hidden_dims']
    )
    
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
            
        model.to(device)
        model.eval()
    else:
        print("❌ Model weights not found.")
        return

    # Get Data
    clean_data = get_real_sounding(args.station, args.date)
    if clean_data is None:
        return

    # Preprocess
    print("Preprocessing data...")
    input_vector = preprocess_sounding(clean_data, config, stats)
    input_tensor = torch.tensor(input_vector).unsqueeze(0).to(device)
    
    # Predict
    print("Running model prediction...")
    with torch.no_grad():
        prediction = model(input_tensor)
    
    # Postprocess
    pred_data = postprocess_prediction(prediction, config, stats)
    
    # Combine Data (Original + Predicted)
    # We want to plot the original sounding up to its top, and then the prediction above it.
    # Original data
    orig_p = clean_data['p'].magnitude
    orig_T = clean_data['T'].magnitude
    orig_Td = clean_data['Td'].magnitude
    orig_z = clean_data['z'].magnitude
    orig_u = clean_data['u'].magnitude
    orig_v = clean_data['v'].magnitude
    
    # Predicted data (sorted by pressure descending just in case, but config order is 7 -> 0.1)
    # We need to sort all arrays by pressure descending (high P to low P)
    pred_p = pred_data['p']
    pred_T = pred_data['T']
    pred_Td = pred_data['Td']
    pred_z = pred_data['z']
    pred_u = pred_data['u']
    pred_v = pred_data['v']
    
    # Concatenate
    # Filter original to include everything > max(pred_p) to avoid overlap/double counting?
    # Or just concatenate and let sounderpy handle it (might look messy if overlap).
    # The input levels went up to 10 hPa. The output starts at 7 hPa.
    # So we can just concatenate.
    
    full_p = np.concatenate([orig_p, pred_p])
    full_T = np.concatenate([orig_T, pred_T])
    full_Td = np.concatenate([orig_Td, pred_Td])
    full_z = np.concatenate([orig_z, pred_z])
    full_u = np.concatenate([orig_u, pred_u])
    full_v = np.concatenate([orig_v, pred_v])
    
    # Sort by pressure descending
    sort_idx = np.argsort(full_p)[::-1]
    
    # Initialize with original metadata
    combined_data = clean_data.copy()
    
    # Overwrite data with combined profiles
    combined_data['p'] = full_p[sort_idx] * units.hPa
    combined_data['T'] = full_T[sort_idx] * units.K
    combined_data['Td'] = full_Td[sort_idx] * units.K
    combined_data['z'] = full_z[sort_idx] * units.m
    combined_data['u'] = full_u[sort_idx] * units.m/units.s
    combined_data['v'] = full_v[sort_idx] * units.m/units.s
    
    # Ensure site_info is correct (it should be if we copied)
    if 'site_info' not in combined_data:
        combined_data['site_info'] = clean_data.get('site_info', {})
    
    # Plotting
    print("Generating Skew-T plot...")
    output_filename = f"experiments/prediction_{args.station}_{args.date.replace(' ', '_').replace(':', '')}.png"
    
    try:
        # Use sounderpy to build sounding
        # It handles layout, hodograph, indices etc.
        spy.build_sounding(
            combined_data,
            save=True,
            filename=output_filename,
            radar=None,
            map_zoom=0
        )
        print(f"✅ Plot saved to {output_filename}")
        
    except Exception as e:
        print(f"Error plotting with sounderpy: {e}")
        print("Trying simple MetPy plot...")
        # Fallback to simple plot if sounderpy fails on high altitude data
        try:
            fig = plt.figure(figsize=(9, 9))
            skew = SkewT(fig, rotation=45)
            skew.plot(combined_data['p'], combined_data['T'], 'r')
            skew.plot(combined_data['p'], combined_data['Td'], 'g')
            skew.plot_barbs(combined_data['p'], combined_data['u'], combined_data['v'])
            skew.ax.set_ylim(1050, 0.1)
            plt.savefig(output_filename)
            print(f"✅ Fallback plot saved to {output_filename}")
        except Exception as e2:
             print(f"Error plotting with MetPy: {e2}")

if __name__ == '__main__':
    main()
