# Polarization sky model (current implementation)

当前实现使用 Rayleigh clear-sky 近似来生成 DoLP/AoP LUT（后续可替换为 libRadtran 真实辐射传输输出）。

## Implemented equations

- Scattering angle:
  \[
  \cos\gamma = \cos\theta\cos\theta_s + \sin\theta\sin\theta_s\cos(\phi-\phi_s)
  \]
- Degree of linear polarization (DoLP):
  \[
  P(\gamma)=\frac{\sin^2\gamma}{1+\cos^2\gamma}
  \]
- AoP uses scattering-plane-normal approximation in local tangent frame.

## Notes

- LUT resolution: `zenith=180`, `azimuth=360`.
- Compositor assumes upward fisheye-like mapping (`r -> zenith`).
- This is a physics-inspired baseline for software integration; for publication-grade results, connect libRadtran and calibrate with sensor/FOV/intrinsics.

## References used for model direction

- Rayleigh sky polarization model overview: https://en.wikipedia.org/wiki/Rayleigh_sky_model
- Clear-sky polarization relations used in vision literature (fish-eye sunlight polarization estimation):  
  https://open-vision.sc.e.titech.ac.jp/~reikawa/publication/miyazaki-cva2009.pdf
