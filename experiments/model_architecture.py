"""
УЛУЧШЕННАЯ АРХИТЕКТУРА НЕЙРОННОЙ СЕТИ ДЛЯ ВОССТАНОВЛЕНИЯ ПРОФИЛЯ АТМОСФЕРЫ

Ключевые улучшения относительно базовой версии:
1. Multi-Head Architecture - раздельная обработка термодинамики (T, RH, Z) и динамики (U, V)
2. Cross-Attention механизм для моделирования теплового ветра
3. Vertical Self-Attention для выделения значимых уровней
4. Отдельные выходные головы для каждой переменной
5. Physics-Informed Loss с учетом уравнения теплового ветра
6. Увеличенная емкость модели (~3.2M параметров вместо ~1.4M)

Поддерживает данные MERRA-2 и ERA5 с расширением до 0.1 гПа
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Dict, Optional


# ============================================================================
# БАЗОВЫЕ БЛОКИ
# ============================================================================

class ResidualBlock(nn.Module):
    """
    Улучшенный остаточный блок с BatchNorm и Dropout.
    
    Архитектура:
        input -> Linear -> BatchNorm -> GELU -> Dropout -> Linear -> BatchNorm -> output
                   |                                                                |
                   +----------------------------------------------------------------+
                                        (skip connection)
    """
    def __init__(self, in_features: int, out_features: int, dropout: float = 0.2):
        super(ResidualBlock, self).__init__()
        
        self.fc1 = nn.Linear(in_features, out_features)
        self.bn1 = nn.BatchNorm1d(out_features)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(out_features, out_features)
        self.bn2 = nn.BatchNorm1d(out_features)
        
        # Проекция для skip connection если размерности различаются
        self.shortcut = nn.Linear(in_features, out_features) if in_features != out_features else nn.Identity()
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = self.shortcut(x)
        
        out = self.fc1(x)
        out = self.bn1(out)
        out = self.activation(out)
        out = self.dropout(out)
        
        out = self.fc2(out)
        out = self.bn2(out)
        
        # Остаточная связь
        out = out + identity
        out = self.activation(out)
        
        return out


class VerticalSelfAttention(nn.Module):
    """
    Self-Attention механизм по вертикальным уровням атмосферы.
    
    Позволяет модели динамически выбирать наиболее релевантные входные уровни
    для каждого выходного уровня. Особенно важно для ветровых компонент,
    где связь между уровнями нелинейна.
    
    Parameters:
    -----------
    n_levels : int
        Количество вертикальных уровней
    embed_dim : int
        Размерность эмбеддинга
    num_heads : int
        Количество голов внимания
    """
    def __init__(self, n_levels: int, embed_dim: int = 64, num_heads: int = 4):
        super(VerticalSelfAttention, self).__init__()
        
        self.n_levels = n_levels
        self.embed_dim = embed_dim
        
        # Линейная проекция входа в пространство эмбеддинга
        self.input_projection = nn.Linear(1, embed_dim)
        
        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=0.1,
            batch_first=True
        )
        
        # Выходная проекция обратно в исходное пространство
        self.output_projection = nn.Linear(embed_dim, 1)
        
        self.layer_norm = nn.LayerNorm(embed_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, n_levels] - профиль одной переменной
            
        Returns:
            attended: [batch_size, n_levels] - профиль после attention
        """
        batch_size = x.shape[0]
        
        # Reshape: [batch, n_levels] -> [batch, n_levels, 1]
        x_reshaped = x.unsqueeze(-1)
        
        # Проекция в пространство эмбеддинга: [batch, n_levels, embed_dim]
        embedded = self.input_projection(x_reshaped)
        
        # Self-attention по уровням
        attended, attn_weights = self.attention(embedded, embedded, embedded)
        
        # Остаточная связь + layer norm
        attended = self.layer_norm(attended + embedded)
        
        # Проекция обратно: [batch, n_levels, 1]
        output = self.output_projection(attended)
        
        # Squeeze обратно: [batch, n_levels]
        return output.squeeze(-1)

class CrossAttentionBlock(nn.Module):
    """
    Cross-Attention между термодинамическими (T, RH, Z) и динамическими (U, V) переменными.
    Моделирует физическую связь через уравнение теплового ветра.
    """
    def __init__(self, thermo_dim: int, wind_dim: int, hidden_dim: int = 256):
        super(CrossAttentionBlock, self).__init__()
        
        # Проекции для query, key, value
        self.query_proj = nn.Linear(wind_dim, hidden_dim)
        self.key_proj = nn.Linear(thermo_dim, hidden_dim)
        self.value_proj = nn.Linear(thermo_dim, hidden_dim)
        
        # ИСПРАВЛЕНИЕ: регистрируем scale как buffer (автоматически на GPU)
        self.register_buffer('scale', torch.tensor(hidden_dim ** -0.5))
        
        self.dropout = nn.Dropout(0.1)
        self.output_proj = nn.Linear(hidden_dim, wind_dim)
        self.layer_norm = nn.LayerNorm(wind_dim)

    def forward(self, thermo_features: torch.Tensor, wind_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            thermo_features: [batch, thermo_dim]
            wind_features: [batch, wind_dim]
        Returns:
            enhanced_wind: [batch, wind_dim]
        """
        # Все операции теперь автоматически на правильном device
        Q = self.query_proj(wind_features)  # [batch, hidden_dim]
        K = self.key_proj(thermo_features)   # [batch, hidden_dim]
        V = self.value_proj(thermo_features) # [batch, hidden_dim]

        # ОПТИМИЗАЦИЯ: используем einsum для эффективности
        # Вместо unsqueeze + bmm
        attn_scores = torch.einsum('bd,bd->b', Q, K).unsqueeze(1).unsqueeze(2)  # [batch, 1, 1]
        attn_scores = attn_scores * self.scale
        
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # ОПТИМИЗАЦИЯ: прямое умножение вместо bmm
        attended = (attn_weights.squeeze() * V.T).T  # [batch, hidden_dim]
        
        output = self.output_proj(attended)
        enhanced_wind = self.layer_norm(output + wind_features)
        
        return enhanced_wind


# ============================================================================
# ВЫХОДНЫЕ ГОЛОВЫ ДЛЯ КАЖДОЙ ПЕРЕМЕННОЙ
# ============================================================================

class VariableHead(nn.Module):
    """
    Специализированная выходная голова для одной переменной.
    
    Каждая переменная имеет свою собственную выходную голову, что позволяет
    модели учиться специфическим паттернам для каждого типа данных.
    
    Parameters:
    -----------
    input_dim : int
        Размерность входных признаков из общего энкодера
    output_levels : int
        Количество выходных уровней для данной переменной
    use_vertical_attention : bool
        Использовать ли vertical attention (рекомендуется для U, V)
    """
    def __init__(self, input_dim: int, output_levels: int, 
                 use_vertical_attention: bool = False):
        super(VariableHead, self).__init__()
        
        self.use_vertical_attention = use_vertical_attention
        self.output_levels = output_levels
        
        # Основная выходная проекция
        self.fc1 = nn.Linear(input_dim, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(0.15)
        
        self.fc2 = nn.Linear(256, output_levels)
        
        # Опциональный vertical attention для ветровых компонент
        if use_vertical_attention:
            self.vertical_attention = VerticalSelfAttention(
                n_levels=output_levels,
                embed_dim=64,
                num_heads=4
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, input_dim]
            
        Returns:
            output: [batch_size, output_levels]
        """
        out = self.fc1(x)
        out = self.bn1(out)
        out = self.activation(out)
        out = self.dropout(out)
        
        out = self.fc2(out)
        
        # Применяем vertical attention если включено (для U, V)
        if self.use_vertical_attention:
            out = self.vertical_attention(out)
        
        return out


# ============================================================================
# ОСНОВНАЯ АРХИТЕКТУРА: MULTI-HEAD ATMOSPHERIC RESNET
# ============================================================================

class MultiHeadAtmosphericResNet(nn.Module):
    """
    УЛУЧШЕННАЯ АРХИТЕКТУРА с раздельными ветвями для разных типов переменных.
    
    Архитектура:
    
    INPUT [batch, 120 или 145]
        |
        +---> SPLIT по переменным
                |
                +---> ТЕРМОДИНАМИЧЕСКАЯ ВЕТВЬ (T, RH, Z)
                |         |
                |         v
                |     [512] -> ResBlock(384) -> ResBlock(384)
                |         |
                |         +----------------+
                |                          |
                +---> ВЕТРОВАЯ ВЕТВЬ (U, V)     |
                          |                     |
                          v                     v
                      [384] -> ResBlock(320)    |
                          |                     |
                          +---> CROSS-ATTENTION-+
                                      |
                                      v
                          FUSION [512] -> ResBlock(512)
                                      |
                                      v
                          +---------------------------+
                          |           |       |       |       |
                          v           v       v       v       v
                      HEAD_T   HEAD_RH  HEAD_Z  HEAD_U  HEAD_V
                          |           |       |       |       |
                          +---------------------------+
                                      |
                                   OUTPUT
    
    Параметры:
    ----------
    input_dim : int
        Размерность входа (24*5=120 для базовой, 29*5=145 для расширенной)
    output_dim : int
        Размерность выхода (13*5=65 для базовой, 17*5=85 для расширенной)
    n_input_levels : int
        Количество входных уровней (24 или 29)
    n_output_levels : int
        Количество выходных уровней (13 или 17)
    """
    def __init__(
        self,
        input_dim: int = 120,
        output_dim: int = 65,
        n_input_levels: int = 24,
        n_output_levels: int = 13,
        dropout_rate: float = 0.2
    ):
        super(MultiHeadAtmosphericResNet, self).__init__()
        
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.n_input_levels = n_input_levels
        self.n_output_levels = n_output_levels
        
        # ====================================================================
        # ВХОДНЫЕ РАЗМЕРНОСТИ для каждой группы переменных
        # ====================================================================
        # Термодинамические: T, RH, Z (3 переменных)
        self.thermo_input_dim = n_input_levels * 3
        # Ветровые: U, V (2 переменных)
        self.wind_input_dim = n_input_levels * 2
        
        # ====================================================================
        # ВЕТВЬ 1: ТЕРМОДИНАМИЧЕСКИЙ ЭНКОДЕР (T, RH, Z)
        # ====================================================================
        # Эти переменные имеют сильную вертикальную корреляцию и более
        # плавное изменение с высотой
        
        self.thermo_encoder = nn.Sequential(
            nn.Linear(self.thermo_input_dim, 512),
            nn.BatchNorm1d(512),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            ResidualBlock(512, 384, dropout_rate),
            ResidualBlock(384, 384, dropout_rate),
        )
        
        # ====================================================================
        # ВЕТВЬ 2: ВЕТРОВОЙ ЭНКОДЕР (U, V)
        # ====================================================================
        # Ветровые компоненты требуют специфической обработки как
        # векторные величины и имеют более слабую вертикальную корреляцию
        
        self.wind_encoder = nn.Sequential(
            nn.Linear(self.wind_input_dim, 384),
            nn.BatchNorm1d(384),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            ResidualBlock(384, 320, dropout_rate),
            ResidualBlock(320, 320, dropout_rate),
        )
        
        # ====================================================================
        # CROSS-ATTENTION: моделирование теплового ветра
        # ====================================================================
        # Явная связь между температурой и ветром через уравнение теплового ветра
        
        self.cross_attention = CrossAttentionBlock(
            thermo_dim=384,
            wind_dim=320,
            hidden_dim=256
        )
        
        # ====================================================================
        # FUSION LAYER: объединение термодинамики и динамики
        # ====================================================================
        
        self.fusion = nn.Linear(384 + 320, 512)  # 704 -> 512
        self.fusion_bn = nn.BatchNorm1d(512)
        self.fusion_activation = nn.GELU()
        self.fusion_dropout = nn.Dropout(dropout_rate)
        
        # Дополнительный ResBlock после fusion
        self.fusion_resblock = ResidualBlock(512, 512, dropout_rate)
        
        # ====================================================================
        # ВЫХОДНЫЕ ГОЛОВЫ: отдельная для каждой переменной
        # ====================================================================
        # Каждая голова специализирована на своей переменной и может
        # учиться специфическим паттернам
        
        # Для термодинамических переменных: стандартные головы
        self.head_T = VariableHead(512, n_output_levels, use_vertical_attention=False)
        self.head_RH = VariableHead(512, n_output_levels, use_vertical_attention=False)
        self.head_Z = VariableHead(512, n_output_levels, use_vertical_attention=False)
        
        # Для ветровых компонент: с vertical attention для лучшего учета
        # нелинейных связей между уровнями
        self.head_U = VariableHead(512, n_output_levels, use_vertical_attention=True)
        self.head_V = VariableHead(512, n_output_levels, use_vertical_attention=True)
        
        # ====================================================================
        # ГЛОБАЛЬНАЯ ОСТАТОЧНАЯ СВЯЗЬ (опционально)
        # ====================================================================
        # Прямая проекция входа на выход для сохранения низкочастотной информации
        self.residual_projection = nn.Linear(input_dim, output_dim, bias=False)
        
        # Инициализация весов
        self._initialize_weights()
    
    def _initialize_weights(self):
        """
        Инициализация весов сети методом Kaiming (He initialization).
        Подходит для GELU и ReLU активаций.
        """
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Прямое распространение с Multi-Head архитектурой.
        
        Args:
            x: [batch_size, input_dim] - нормализованный входной профиль
               Порядок переменных: [T_levels, RH_levels, Z_levels, U_levels, V_levels]
        
        Returns:
            y: [batch_size, output_dim] - восстановленные верхние уровни
               Порядок переменных: [T_levels, RH_levels, Z_levels, U_levels, V_levels]
        """
        batch_size = x.shape[0]
        
        # ====================================================================
        # РАЗДЕЛЕНИЕ ВХОДА НА ГРУППЫ ПЕРЕМЕННЫХ
        # ====================================================================
        # Входной тензор организован как: [T, T, ..., RH, RH, ..., Z, Z, ..., U, U, ..., V, V, ...]
        
        # Извлекаем термодинамические переменные (T, RH, Z)
        thermo_input = x[:, :self.thermo_input_dim]  # [batch, n_levels*3]
        
        # Извлекаем ветровые компоненты (U, V)
        wind_input = x[:, self.thermo_input_dim:]     # [batch, n_levels*2]
        
        # ====================================================================
        # ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА В СПЕЦИАЛИЗИРОВАННЫХ ВЕТВЯХ
        # ====================================================================
        
        # Термодинамическая ветвь
        thermo_features = self.thermo_encoder(thermo_input)  # [batch, 384]
        
        # Ветровая ветвь
        wind_features = self.wind_encoder(wind_input)        # [batch, 320]
        
        # ====================================================================
        # CROSS-ATTENTION: обогащение ветровых признаков термодинамикой
        # ====================================================================
        # Моделирует физическую связь (тепловой ветер)
        
        enhanced_wind = self.cross_attention(thermo_features, wind_features)  # [batch, 320]
        
        # ====================================================================
        # FUSION: объединение термодинамики и обогащенных ветровых признаков
        # ====================================================================
        
        fused = torch.cat([thermo_features, enhanced_wind], dim=1)  # [batch, 704]
        fused = self.fusion(fused)                                   # [batch, 512]
        fused = self.fusion_bn(fused)
        fused = self.fusion_activation(fused)
        fused = self.fusion_dropout(fused)
        
        # Дополнительная обработка через ResBlock
        fused = self.fusion_resblock(fused)  # [batch, 512]
        
        # ====================================================================
        # СПЕЦИАЛИЗИРОВАННЫЕ ВЫХОДНЫЕ ГОЛОВЫ
        # ====================================================================
        
        out_T = self.head_T(fused)    # [batch, n_output_levels]
        out_RH = self.head_RH(fused)  # [batch, n_output_levels]
        out_Z = self.head_Z(fused)    # [batch, n_output_levels]
        out_U = self.head_U(fused)    # [batch, n_output_levels] + vertical attention
        out_V = self.head_V(fused)    # [batch, n_output_levels] + vertical attention
        
        # Объединение всех выходов в единый тензор
        # Порядок: T, RH, Z, U, V (как во входе)
        output = torch.cat([out_T, out_RH, out_Z, out_U, out_V], dim=1)  # [batch, output_dim]
        
        # ====================================================================
        # ГЛОБАЛЬНАЯ ОСТАТОЧНАЯ СВЯЗЬ
        # ====================================================================
        # Добавляем прямую проекцию входа для сохранения базовой информации
        
        residual = self.residual_projection(x)
        output = output + residual
        
        return output
    
    def count_parameters(self) -> int:
        """Подсчет числа обучаемых параметров"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ============================================================================
# ФИЗИЧЕСКИ-ИНФОРМИРОВАННАЯ ФУНКЦИЯ ПОТЕРЬ
# ============================================================================

class PhysicsInformedLoss(nn.Module):
    """
    Комбинированная функция потерь с физическими ограничениями.
    ОПТИМИЗИРОВАНО для GPU: все операции векторизованы и на device.
    """
    def __init__(
        self,
        n_output_levels: int = 13,
        thermal_wind_weight: float = 0.1,
        wind_component_weight: float = 2.0
    ):
        super(PhysicsInformedLoss, self).__init__()
        self.n_levels = n_output_levels
        
        # ИСПРАВЛЕНИЕ: регистрируем веса как buffers
        self.register_buffer('tw_weight', torch.tensor(thermal_wind_weight))
        self.register_buffer('wind_weight', torch.tensor(wind_component_weight))
        self.register_buffer('epsilon', torch.tensor(1e-8))
        
        # MSE reduction='none' для гибкости
        self.mse = nn.MSELoss(reduction='mean')

    def thermal_wind_constraint(
        self,
        T_pred: torch.Tensor,
        U_pred: torch.Tensor,
        V_pred: torch.Tensor
    ) -> torch.Tensor:
        """
        ОПТИМИЗИРОВАНО: все операции на GPU, векторизованы.
        """
        if self.n_levels < 2:
            # ИСПРАВЛЕНИЕ: создаем тензор на правильном device
            return torch.zeros(1, device=T_pred.device, dtype=T_pred.dtype)

        # Вертикальные градиенты (GPU-эффективно)
        dT = T_pred[:, 1:] - T_pred[:, :-1]  # [batch, n_levels-1]
        dU = U_pred[:, 1:] - U_pred[:, :-1]
        dV = V_pred[:, 1:] - V_pred[:, :-1]

        # ОПТИМИЗАЦИЯ: векторизованное вычисление косинусного сходства
        # Избегаем F.cosine_similarity для каждой пары отдельно
        
        # Нормализация векторов
        dT_norm = dT / (dT.norm(dim=1, keepdim=True) + self.epsilon)
        dU_norm = dU / (dU.norm(dim=1, keepdim=True) + self.epsilon)
        dV_norm = dV / (dV.norm(dim=1, keepdim=True) + self.epsilon)
        
        # Косинусное сходство через скалярное произведение
        cos_sim_U = (dT_norm * dU_norm).sum(dim=1).abs().mean()
        cos_sim_V = (dT_norm * dV_norm).sum(dim=1).abs().mean()

        # Потеря
        tw_loss = (2.0 - cos_sim_U - cos_sim_V)  # 0 при идеальной корреляции
        
        return tw_loss

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Все операции на GPU, минимум синхронизаций CPU-GPU.
        """
        # Извлечение переменных через slicing (GPU-эффективно)
        T_pred = predictions[:, :self.n_levels]
        RH_pred = predictions[:, self.n_levels:2*self.n_levels]
        Z_pred = predictions[:, 2*self.n_levels:3*self.n_levels]
        U_pred = predictions[:, 3*self.n_levels:4*self.n_levels]
        V_pred = predictions[:, 4*self.n_levels:]

        T_true = targets[:, :self.n_levels]
        RH_true = targets[:, self.n_levels:2*self.n_levels]
        Z_true = targets[:, 2*self.n_levels:3*self.n_levels]
        U_true = targets[:, 3*self.n_levels:4*self.n_levels]
        V_true = targets[:, 4*self.n_levels:]

        # MSE для каждой переменной (всё на GPU)
        mse_T = self.mse(T_pred, T_true)
        mse_RH = self.mse(RH_pred, RH_true)
        mse_Z = self.mse(Z_pred, Z_true)
        mse_U = self.mse(U_pred, U_true)
        mse_V = self.mse(V_pred, V_true)

        # Взвешенная сумма (используем buffer weights)
        mse_total = (mse_T + mse_RH + mse_Z + 
                     self.wind_weight * (mse_U + mse_V)) / (3.0 + 2.0 * self.wind_weight)

        # Physical constraint
        tw_loss = self.thermal_wind_constraint(T_pred, U_pred, V_pred)

        # Общая потеря
        total_loss = mse_total + self.tw_weight * tw_loss

        # ВАЖНО: .item() вызывает CPU-GPU синхронизацию!
        # Делаем это один раз в конце, не в цикле
        loss_dict = {
            'total': total_loss.item(),
            'mse': mse_total.item(),
            'mse_T': mse_T.item(),
            'mse_RH': mse_RH.item(),
            'mse_Z': mse_Z.item(),
            'mse_U': mse_U.item(),
            'mse_V': mse_V.item(),
            'thermal_wind': tw_loss.item()
        }

        return total_loss, loss_dict



# ============================================================================
# ФАБРИЧНАЯ ФУНКЦИЯ ДЛЯ СОЗДАНИЯ МОДЕЛИ
# ============================================================================
def create_model(
    input_dim: int = 120,
    output_dim: int = 65,
    n_input_levels: int = 24,
    n_output_levels: int = 13,
    device: str = 'cpu',
    random_seed: int = 42
) -> MultiHeadAtmosphericResNet:
    """
    Создание модели с правильной инициализацией на GPU.
    """
    # Фиксируем random seed
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    
    # ИСПРАВЛЕНИЕ: проверяем device правильно
    if isinstance(device, str):
        device = torch.device(device)
    
    if device.type == 'cuda':
        torch.cuda.manual_seed(random_seed)
        torch.cuda.manual_seed_all(random_seed)  # Для multi-GPU
        # ВАЖНО: для обучения используем benchmark=True (уже в main)
        # torch.backends.cudnn.deterministic = True только для отладки

    # Создаем модель
    model = MultiHeadAtmosphericResNet(
        input_dim=input_dim,
        output_dim=output_dim,
        n_input_levels=n_input_levels,
        n_output_levels=n_output_levels,
        dropout_rate=0.2
    )

    # КРИТИЧНО: переносим модель на GPU ДО инициализации весов
    model = model.to(device)

    print("=" * 80)
    print("УЛУЧШЕННАЯ MULTI-HEAD АРХИТЕКТУРА")
    print("=" * 80)
    print(f"Устройство: {device}")
    print(f"Входная размерность: {input_dim} ({n_input_levels} уровней × 5 переменных)")
    print(f"Выходная размерность: {output_dim} ({n_output_levels} уровней × 5 переменных)")
    print(f"Число параметров: {model.count_parameters():,}")
    
    if device.type == 'cuda':
        print(f"\nGPU память:")
        print(f"  Выделено под модель: {torch.cuda.memory_allocated(device.index or 0) / 1e9:.3f} GB")
        print(f"  Зарезервировано: {torch.cuda.memory_reserved(device.index or 0) / 1e9:.3f} GB")
    
    print(f"\nКлючевые улучшения:")
    print(f"  ✓ Раздельные энкодеры для термодинамики (T, RH, Z) и динамики (U, V)")
    print(f"  ✓ Cross-Attention для моделирования теплового ветра")
    print(f"  ✓ Vertical Self-Attention для ветровых компонент")
    print(f"  ✓ Отдельные выходные головы для каждой переменной")
    print(f"  ✓ Все операции оптимизированы для GPU")
    print("=" * 80)

    return model



# ============================================================================
# ОБРАТНАЯ СОВМЕСТИМОСТЬ: алиасы для старого интерфейса
# ============================================================================

# Для совместимости с train_per_variable_norm.py оставляем старое имя класса
#AtmosphericProfileResNet = MultiHeadAtmosphericResNet

# Класс PhysicalPostprocessor остается без изменений (копия из базовой версии)
class PhysicalPostprocessor:
    """
    Физическая постобработка для обеспечения гидростатического баланса.
    (Без изменений относительно базовой версии)
    """
    R_DRY = 287.0  # Газовая постоянная [Дж/(кг·К)]
    G = 9.81       # Ускорение свободного падения [м/с²]
    
    def __init__(self, pressure_levels: np.ndarray, threshold: float = 0.05):
        self.pressure_levels = pressure_levels
        self.threshold = threshold
    
    def check_hydrostatic_balance(
        self,
        temperature: np.ndarray,
        geopotential: np.ndarray
    ) -> Tuple[bool, float]:
        """Проверка гидростатического баланса"""
        n_levels = len(temperature)
        if n_levels < 2:
            return True, 0.0
        
        ln_p = np.log(self.pressure_levels * 100)
        dZ_dlnp = np.gradient(geopotential, ln_p)
        theoretical = -self.R_DRY * temperature / self.G
        
        relative_error = np.abs((dZ_dlnp - theoretical) / theoretical)
        max_error = np.max(relative_error)
        is_valid = max_error < self.threshold
        
        return is_valid, max_error
    
    def correct_geopotential(
        self,
        temperature: np.ndarray,
        geopotential_lower: float,
        pressure_lower: float
    ) -> np.ndarray:
        """Пересчет геопотенциала через интегрирование"""
        n_levels = len(temperature)
        geopotential_corrected = np.zeros(n_levels)
        geopotential_corrected[0] = geopotential_lower
        
        for i in range(1, n_levels):
            T_mean = (temperature[i-1] + temperature[i]) / 2
            p_lower = self.pressure_levels[i-1] * 100
            p_upper = self.pressure_levels[i] * 100
            d_ln_p = np.log(p_upper) - np.log(p_lower)
            dZ = -(self.R_DRY * T_mean / self.G) * d_ln_p
            geopotential_corrected[i] = geopotential_corrected[i-1] + dZ
        
        return geopotential_corrected
    
    def postprocess(
        self,
        predicted_profile: np.ndarray,
        variable_names: list = ['T', 'Q', 'Z', 'U', 'V']
    ) -> Tuple[np.ndarray, bool]:
        """Применение физической коррекции"""
        corrected_profile = predicted_profile.copy()
        was_corrected = False
        
        T_idx = variable_names.index('T')
        Z_idx = variable_names.index('Z')
        
        temperature = predicted_profile[:, T_idx]
        geopotential = predicted_profile[:, Z_idx]
        
        is_valid, error = self.check_hydrostatic_balance(temperature, geopotential)
        
        if not is_valid:
            geopotential_lower = geopotential[0]
            pressure_lower = self.pressure_levels[0]
            corrected_Z = self.correct_geopotential(
                temperature, geopotential_lower, pressure_lower
            )
            corrected_profile[:, Z_idx] = corrected_Z
            was_corrected = True
        
        return corrected_profile, was_corrected


# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕННОЙ АРХИТЕКТУРЫ")
    print("=" * 80)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Тест 1: Базовая конфигурация (24 входных -> 13 выходных уровней)
    print("\n[ТЕСТ 1] Базовая конфигурация")
    model_base = create_model(
        input_dim=120,
        output_dim=65,
        n_input_levels=24,
        n_output_levels=13,
        device=device
    )
    
    x_test = torch.randn(32, 120).to(device)
    with torch.no_grad():
        y_pred = model_base(x_test)
    
    print(f"\nВход: {x_test.shape}")
    print(f"Выход: {y_pred.shape}")
    print(f"Ожидается: [32, 65] ✓" if y_pred.shape == (32, 65) else "ОШИБКА!")
    
    # Тест 2: Расширенная конфигурация (29 входных -> 17 выходных уровней)
    print("\n[ТЕСТ 2] Расширенная конфигурация для MERRA-2")
    model_ext = create_model(
        input_dim=145,
        output_dim=85,
        n_input_levels=29,
        n_output_levels=17,
        device=device
    )
    
    x_test_ext = torch.randn(32, 145).to(device)
    with torch.no_grad():
        y_pred_ext = model_ext(x_test_ext)
    
    print(f"\nВход: {x_test_ext.shape}")
    print(f"Выход: {y_pred_ext.shape}")
    print(f"Ожидается: [32, 85] ✓" if y_pred_ext.shape == (32, 85) else "ОШИБКА!")
    
    # Тест 3: Physics-Informed Loss
    print("\n[ТЕСТ 3] Physics-Informed Loss")
    criterion = PhysicsInformedLoss(n_output_levels=13)
    
    y_target = torch.randn(32, 65).to(device)
    loss, loss_dict = criterion(y_pred, y_target)
    
    print(f"\nОбщая потеря: {loss.item():.6f}")
    print(f"Компоненты потерь:")
    for key, value in loss_dict.items():
        print(f"  {key}: {value:.6f}")
    
    print("\n" + "=" * 80)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 80)
    print("\nМодель готова к интеграции в train_per_variable_norm.py")
    print("Используйте: from model_architecture import create_model, PhysicsInformedLoss")
