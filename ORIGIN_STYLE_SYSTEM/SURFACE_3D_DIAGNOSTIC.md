# SURFACE 3D DIAGNOSTIC

## 结论

当前 3D Surface 中的大面积白色区域不是缺失数据，也不是有效高值或低值被 Z 轴、色阶或图层裁掉。它来自当前透视投影与 45° 相机倾角下，抬高的曲面边界和底部三维框架之间露出的白色页面背景。该现象容易被误读为曲面破洞，因此当前版本不得冻结，必须进行视角与渲染重构。

## 只读证据

| 检查项 | 标准 Surface | Stress Surface | 判定 |
|---|---:|---:|---|
| 网格尺寸 | 41 × 41 | 61 × 61 | 规则网格 |
| 预期点数 | 1,681 | 3,721 | — |
| 实际点数 | 1,681 | 3,721 | 无缺点 |
| Objective 最小值 | 0.04 | 1.93 | 有效 |
| Objective 最大值 | 32.51 | 94.43 | 有效 |
| 当前显示 Z 范围 | 0–36 | 0–100 | 全覆盖 |
| 超出 Z 范围的数据 | 0 | 0 | 无 Z clipping |
| 当前色阶范围 | 0–36 | 0–100 | 全覆盖 |
| 超出色阶的数据 | 0 | 0 | 无 colormap clipping |
| `layer.clip` | 0 | 0 | 图层裁剪关闭 |
| 3D / OpenGL 状态 | 1 / 1 | 1 / 1 | 原生 3D OpenGL 图层 |
| 当前相机 | azimuth 138°, inclination 45° | 同左 | 透视感偏强 |

## 假设逐项判定

- **Z range clipping：否。** 两组数据的完整数值范围均位于当前 Z 轴上下限内。
- **Colormap clipping：否。** 色阶上下限与 Z 显示范围一致，且覆盖全部有效数值。
- **Layer clipping：否。** Origin 返回 `layer.clip=0`。
- **Missing data：否。** 两个规则网格的实际点数均等于笛卡尔网格的预期点数。
- **Surface rendering setting：是，属于主要原因。** 当前透视投影、较低的观察倾角和可见底框共同暴露页面背景；边界处的高 Z 值进一步放大了“白色缺口”的错觉。
- **Other：无数据层面的其他异常。** 标准面与强非对称压力面都能由其完整规则矩阵重建。

## 科学表达判定

没有真实有效数据因显示范围而未绘制，因此本次未发现数值截断型科学错误。但白区很像数据缺失，会造成错误的视觉推断，属于科学传播风险。旧版 `SCP_SURFACE_3D_AUXILIARY_v20_CANDIDATE` 保持未冻结状态，不应继续用于论文输出。

## 重构处方

新版本采用 **2.5D Scientific Surface**：

1. 使用接近正交的低透视投影和更高、较平缓的观察角，优先保证整个参数域连续可见。
2. 保持真实 Z 数值范围与可解释刻度，不通过压扁数值轴掩盖问题。
3. 使用冻结 Contour/Heatmap 同源的 19 级低饱和蓝—青—绿—浅黄色带。
4. Surface 仅保留少量克制的等值线，降低轴线、tick、光照高光和 colorbar 权重。
5. 暖橙最优点只做最小的防 Z-fighting 显示抬升，并在交付记录中披露。
6. 标准面与 boundary optimum + 强非对称压力面均重新审查完整性。

## 永久角色

3D Surface 定义为 **AUXILIARY FIGURE**。对于二参数目标函数，默认推荐顺序为：

`Contour > 3D Surface`

仅当 curvature、multimodality、saddle structure 或 local basin 等空间结构本身具有解释意义时，才建议附加 3D Surface。
