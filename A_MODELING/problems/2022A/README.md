# 2022A《波浪能最大输出功率设计》实战验收

本目录只存放 2022A 的题目专用动力学、稳态识别、功率计算、优化和交付逻辑。官方原始材料位于 `data/2022A/official/A/`，只读使用；正式结果统一写入 `results/2022A/`。除非出现经过回归测试证实的跨题缺陷，不修改 `core/`。

## 1. 坐标系与平衡点

- 采用右手坐标系；静水面内沿波浪传播方向为 `x`，铅直向上为 `z`，纵摇绕 `y` 轴。
- `z_f,z_o` 分别为浮子转轴/隔层中心和振子质心相对静平衡位置的垂荡位移，向上为正。
- `theta_f,theta_o` 分别为浮子和中轴—振子相对静平衡姿态的纵摇角，按右手定则为正，单位统一为 rad。
- 初值全部为零。重力、静浮力和弹簧预载在静平衡处相消，扰动方程不重复加入常量项。
- 问题 3/4 采用 8 状态非线性质量矩阵模型：保留振子沿转轴滑动时的半径变化、轴向力投影、离心项、科氏项和垂荡—纵摇惯性耦合；附件给出的水动力仍按线性周期微幅波形式使用。其一阶小角度极限必须退化为垂荡/纵摇分块模型。

## 2. 固定状态顺序

问题 1/2：

`y = [z_f, z_o, v_f, v_o]`。

问题 3/4：

`y = [x, z_f, theta_f, theta_o, x_dot, v_f, omega_f, omega_o]`，其中 `x` 是振子沿中轴相对静平衡位置的轴向位移。官方输出中的振子绝对垂荡量由几何关系计算，不直接占用状态槽位。

任何求解、导出和绘图均不得自行改变此顺序。

## 3. 垂荡模型

记浮子质量 `m_f`、振子质量 `m_o`、垂荡附加质量 `m_a`、兴波阻尼 `b_h`、水线面恢复刚度 `k_h=rho*g*pi*R^2`、PTO 弹簧刚度 `k_s`。定义

`delta_z = z_o-z_f`，`delta_v = v_o-v_f`。

PTO 对振子的轴向力为

`F_PTO,o = -k_s*delta_z - D(delta_v)`，

浮子所受反力相反。其中

- 常阻尼：`D(delta_v)=c_h*delta_v`；
- 速度幂阻尼：`c(delta_v)=lambda*|delta_v|^p`，`D(delta_v)=lambda*|delta_v|^p*delta_v`。

扰动方程为

`(m_f+m_a) z_f'' + b_h z_f' + k_h z_f + k_s(z_f-z_o) + D(v_f-v_o) = f cos(omega t)`，

`m_o z_o'' + k_s(z_o-z_f) + D(v_o-v_f) = 0`。

非线性 PTO 瞬时输出功率不是 `c|delta_v|`，而是

`P_h = D(delta_v)*delta_v = lambda*|delta_v|^(p+2) >= 0`。

常阻尼是 `p=0, lambda=c_h` 的特例。

## 4. 垂荡—纵摇耦合模型

记浮子关于隔层中心横轴的物理转动惯量 `J_f`、附件给出的附加转动惯量 `J_a`、纵摇兴波阻尼 `b_r`、静水恢复力矩系数 `k_r`、扭转弹簧刚度 `k_t`、旋转阻尼 `c_r`、振子质心横轴惯量 `J_c`。定义

`delta_theta=theta_o-theta_f`，`delta_omega=omega_o-omega_f`。

振子质心到转轴的瞬时距离 `r=d_eq+x`。其绝对垂荡位移和速度为

`z_o=z_f+r*cos(theta_o)-d_eq`，

`v_o=v_f+x_dot*cos(theta_o)-r*sin(theta_o)*omega_o`。

令广义加速度 `a=[x_ddot,z_f_ddot,theta_f_ddot,theta_o_ddot]^T`，则正式模型写成 `M(q)a=b(t,q,q_dot)`：

```text
M = [[m_o, m_o cos(theta_o), 0, 0],
     [m_o cos(theta_o), m_f+m_a+m_o, 0, -m_o r sin(theta_o)],
     [0,   0,                J_f+J_a, 0],
     [0,  -m_o r sin(theta_o), 0, J_c+m_o r^2]]
```

右端四项依次为

```text
b_x = m_o g(1-cos(theta_o)) + m_o r omega_o^2 - k_s x - c_h x_dot
b_z = f cos(omega t) - b_h v_f - k_h z_f
      + 2 m_o sin(theta_o) x_dot omega_o
      + m_o r cos(theta_o) omega_o^2
b_f = k_t(theta_o-theta_f)+c_r(omega_o-omega_f)
      + L cos(omega t)-b_r omega_f-k_r theta_f
b_o = m_o g[r sin(theta_o)-d_eq theta_o]
      -2 m_o r x_dot omega_o-k_t(theta_o-theta_f)-c_r(omega_o-omega_f)
```

该质量矩阵来自同一个拉格朗日系统，故保持对称。第二行是“浮子与振子总竖向广义动量”方程，不能再叠加振子的重力或 PTO 轴向力投影；这些内力已由第一行和耦合惯性项体现。若把第二行改写成单独浮子受力方程，却仍保留本质量矩阵，会破坏对称性和周期能量闭合。

最后一式中的 `-2 m_o r x_dot omega_o` 含完整力臂，量纲为 N·m。重力矩写成 `m_o g[r sin(theta_o)-d_eq theta_o]`：第一项是几何重力矩，第二项扣除已经包含在题面静平衡微幅恢复参数中的一阶线性化，避免重复计入而把零姿态错误变成不稳定平衡。

一阶小角度极限为独立验证用的分块方程：

`(J_f+J_a) theta_f'' + b_r theta_f' + k_r theta_f + k_t(theta_f-theta_o) + c_r(omega_f-omega_o) = L cos(omega t)`，

`(J_c+m_o d_eq^2) theta_o'' + k_t(theta_o-theta_f) + c_r(omega_o-omega_f) = 0`。

旋转 PTO 瞬时功率为

`P_r=c_r*(omega_o-omega_f)^2 >= 0`，总输出功率 `P=P_h+P_r`。

### 转动惯量的几何约定

浮子按题面“质量均匀分布的圆柱壳体和圆锥壳体”解释为等面密度薄壳：圆柱侧壁、圆柱顶盖和圆锥侧壁按面积分配总质量；参考轴为隔层中心横轴。各项采用解析面积积分，并在代码中保留分项值。

振子自身关于质心横轴的转动惯量为 `m_o(3r_o^2+h_o^2)/12`。静平衡时弹簧受压量为 `m_o*g/k_s`，故振子质心到转轴距离

`d_eq = h_o/2 + (l_0-m_o*g/k_s)`，

并用平行轴定理得到线性基线 `J_o=J_c+m_o*d_eq^2`；正式非线性模型使用随 `x` 变化的 `J_c+m_o(d_eq+x)^2`。这一轴距假设在敏感性和独立审查中单列，不能成为未说明的神秘常数。

## 5. 力与力矩方向复核

| 作用项 | 作用对象 | 正方向表达式 | 方向检查 |
|---|---|---:|---|
| 波浪激励力 | 浮子 | `+f cos(omega t)` | `t=0` 向上 |
| 兴波阻尼力 | 浮子 | `-b_h v_f` | 永远反向于浮子速度 |
| 静水恢复力 | 浮子 | `-k_h z_f` | 离开平衡点即指回零点 |
| PTO 弹簧力 | 振子 | `-k_s x`（Q3/4） | 相对伸长时拉回 |
| PTO 阻尼力 | 振子 | `-c_h x_dot`（Q3/4） | `F*x_dot <= 0` |
| 波浪激励力矩 | 浮子 | `+L cos(omega t)` | 与正纵摇约定一致 |
| 兴波阻尼矩 | 浮子 | `-b_r omega_f` | 永远耗散 |
| 静水恢复力矩 | 浮子 | `-k_r theta_f` | 指回零姿态 |
| 扭转弹簧矩 | 振子 | `-k_t(theta_o-theta_f)` | 减小相对角位移 |
| 旋转阻尼矩 | 振子 | `-c_r(omega_o-omega_f)` | 相对运动功率非负 |

PTO 内力/内力矩在两物体方程中大小相等、方向相反。零相对速度时阻尼力严格为零；将相对速度反号时阻尼力反号、瞬时输出功率不变。

## 6. 求解与验收顺序

`problem_data.py -> physics.py -> steady_state.py/power.py -> q1.py -> q2.py -> q3.py -> q4.py -> deliverables.py -> validation_2022a.py -> audit_2022a.py`。

逐问均执行小算例、正式计算、三档 ODE 容差、解析/频域交叉验证、稳态整周期窗口收敛和性能记录。优化阶段先粗定位，后确定性精化，最终用更严 ODE 设置重算并检查邻域。Excel 由官方模板复制后填充并重新读取验收。
