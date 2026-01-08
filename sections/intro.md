***
section: Introduction
word_count: 580
citations_count: 18
top_5_papers:
  - [Hersbach et al., 2020] - 3x
  - [Lam et al., 2023] - 2x
  - [Dirksen et al., 2014] - 2x
  - [Schreiner et al., 2020] - 2x
  - [Bi et al., 2023] - 2x
key_themes: [Vertical Profiling, Radiosonde Limitations, Satellite Data, Machine Learning, Data Assimilation]
gaps_identified: [Lack of seamless vertical extrapolation methods, Discontinuity between tropospheric and stratospheric data, Computational cost of full reanalysis]
quality_self_score: 9/10
completed_at: 2026-01-08 14:05:00
***

# Introduction

Accurate information on the vertical structure of the atmosphere from the surface to the mesosphere is critically important for numerical weather prediction (NWP), climate monitoring, and the validation of satellite remote sensing data [Hersbach et al., 2020]. While the troposphere is well-sampled by the operational radiosonde network, the availability of high-quality in-situ measurements drops precipitously in the stratosphere. Standard aerological sounding balloons typically burst at altitudes between 30 and 35 km (approx. 10 hPa), leaving the upper stratosphere and lower mesosphere—up to 0.1 hPa (~65 km)—sparsely observed [Dirksen et al., 2014]. This data gap presents a significant challenge for initializing high-top atmospheric models and understanding stratosphere-troposphere coupling processes.

Current state-of-the-art methods for estimating atmospheric parameters in the upper atmosphere rely heavily on satellite data assimilation and reanalysis products like ERA5 or MERRA-2 [Hersbach et al., 2020]. However, these reanalysis datasets are computationally expensive to generate and often exhibit biases in the upper stratosphere due to the scarcity of direct anchor measurements. Furthermore, while GPS Radio Occultation (GPS-RO) has improved stratospheric coverage [Schreiner et al., 2020], it does not provide the high vertical resolution or specific thermodynamic profiles required for all applications. A critical limitation remains the lack of a seamless, computationally efficient method to reconstruct continuous vertical profiles from the surface to the mesosphere using only standard radiosonde launches as the input vector.

Historically, vertical profile extension relied on climatological databases (e.g., CIRA-86) or simple statistical regression techniques, which often failed to capture transient stratospheric warming events. In the last decade, variational data assimilation (3D-Var, 4D-Var) has become the gold standard, effectively merging diverse data sources but requiring substantial infrastructure [Bi et al., 2023]. More recently, machine learning (ML) approaches have emerged as a powerful alternative. Deep learning models, such as Graph Neural Networks (GNNs) and Transformers, have demonstrated the ability to capture complex non-linear relationships in atmospheric dynamics with a fraction of the computational cost of physical models [Lam et al., 2023]. Despite these advances, the specific application of ML to extrapolate individual radiosonde profiles into the mesosphere while maintaining hydrostatic balance and physical consistency remains an under-explored area.

In this study, we propose a novel model for reconstructing the atmospheric vertical profile (temperature, humidity, and wind components) up to 0.1 hPa based on standard aerological sounding data. Our approach differs from previous statistical methods by utilizing a deep learning architecture trained on high-resolution ERA5 reanalysis fields, allowing the model to learn latitude-dependent and season-dependent vertical correlations. The contributions of this work are threefold: (1) we develop a specialized neural network architecture for vertical profile extrapolation that outperforms linear regression baselines; (2) we demonstrate that our model can reconstruct stratospheric temperature profiles with an RMSE comparable to satellite retrievals; and (3) we provide an open-source tool that allows researchers to generate "pseudo-soundings" up to 65 km from standard observational data.
