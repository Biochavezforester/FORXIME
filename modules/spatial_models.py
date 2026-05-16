import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.spatial.distance import cdist

def estimate_spatial_royle_nichols(detection_histories, coordinates, buffer_m=1200, grid_res_m=100, p0_fixed=0.15):
    """
    Estima la densidad poblacional usando el modelo Spatial Royle-Nichols (Bernoulli MLE).
    Usa el valor p0 (r) calibrado por el usuario.
    """
    try:
        # 1. Validación de Identificabilidad
        y = np.any(detection_histories, axis=1).astype(int)
        K = detection_histories.shape[1]
        n_sites_det = np.sum(y)
        
        if n_sites_det < 2:
            return {'success': False, 'message': 'Información espacial insuficiente (min 2 sitios con registros).'}
        
        X = coordinates
        n_sites = X.shape[0]
        
        # 2. Espacio de estado
        x_min, x_max = X[:, 0].min() - buffer_m, X[:, 0].max() + buffer_m
        y_min, y_max = X[:, 1].min() - buffer_m, X[:, 1].max() + buffer_m
        grid_res = max(50, buffer_m / 25)
        gx = np.arange(x_min, x_max, grid_res)
        gy = np.arange(y_min, y_max, grid_res)
        grid_s = np.array(np.meshgrid(gx, gy)).T.reshape(-1, 2)
        pixel_area_ha = (grid_res**2) / 10000.0
        dist_matrix = cdist(X, grid_s)
        
        # 3. MLE Royle-Nichols (Bernoulli)
        def nll(params):
            D = np.exp(params[0])  # ind/ha
            sigma = np.exp(params[1])  # m
            p0 = p0_fixed
            
            p_j_s = p0 * np.exp(-np.clip(dist_matrix**2 / (2 * sigma**2), 0, 50))
            integral_j = np.sum(1 - (1 - p_j_s)**K, axis=1) * pixel_area_ha
            lambda_j = np.clip(D * integral_j, 1e-10, 50)
            
            prob_det_j = 1 - np.exp(-lambda_j)
            ll = np.sum(y * np.log(np.clip(prob_det_j, 1e-12, 1-1e-12)) + (1-y) * np.log(np.clip(1-prob_det_j, 1e-12, 1-1e-12)))
            return -ll

        # 4. Optimización Multi-start
        best_res = None
        # Probar dos escalas: una local (sigma pequeña) y una de paisaje (sigma grande)
        for s_init in [buffer_m/10, buffer_m/3]:
            d_init = n_sites_det / (n_sites * (np.pi * (s_init)**2 / 10000))
            res = minimize(nll, [np.log(max(d_init, 1e-5)), np.log(s_init)],
                          method='L-BFGS-B', bounds=[(-20, 5), (1, 9)])
            if best_res is None or (res.success and res.fun < best_res.fun):
                best_res = res

        if not best_res.success:
            return {'success': False, 'message': 'El modelo no logró estabilizarse.'}
            
        D_hat = np.exp(best_res.x[0])
        sigma_hat = np.exp(best_res.x[1])
        
        # Validación biológica simple
        if sigma_hat > buffer_m * 0.95:
             return {'success': False, 'message': 'Escala de movimiento no identificable (muy grande).'}

        return {
            'success': True,
            'density_ha': round(D_hat, 6),
            'sigma': round(sigma_hat, 2),
            'p0': round(p0_fixed, 4),
            'method': 'sRN'
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}
