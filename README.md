# Silicon Eye 🔬

**AI-assisted analog circuit reverse engineering — from multi-layer die images to clean, human-readable SPICE netlists.**

> 🎯 **The Gap:** Every existing IC reverse engineering tool (Degate, ChipJuice, HAL) targets *digital* standard-cell designs. Nobody handles *analog* custom layout. Silicon Eye fills that void.

## Why This Exists

Reverse-engineering an analog chip today is a painful, manual process:

1. Take 10+ layer photographs of a decapped die
2. Manually trace every transistor, resistor, and capacitor across layers
3. Piece together a flat netlist — errors are common, especially when done by layout engineers who see geometry but not function
4. Analog designers then spend hours rebuilding a readable schematic from the mess

**Silicon Eye automates the first bottleneck: image → devices.** It uses modern computer vision (SAM3 for segmentation) and rule-based heuristics to extract transistors from die images, group matched pairs (current mirrors, diff pairs), filter dummy devices, and merge passive components — then exports a clean netlist.

## Comparison: What Exists vs Silicon Eye

| Capability | Degate | ChipJuice | HAL | **Silicon Eye** |
|---|---|---|---|---|
| Digital standard cells | ✅ | ✅ | ✅ (post-extraction) | — |
| Analog custom layout | ❌ | ❌ | ❌ | ✅ |
| Transistor-level extraction | ❌ | ❌ | ❌ | ✅ |
| Device segmentation (CV) | Template match only | ❌ | N/A | ✅ SAM3 + rule-based |
| Multi-layer die images | Manual align | Partial | N/A | ✅ Stitcher + aligner |
| Matched-pair grouping | ❌ | ❌ | ❌ | ✅ |
| Dummy device filtering | ❌ | ❌ | ❌ | ✅ |
| R/C passive merging | ❌ | ❌ | ❌ | ✅ |
| Human annotation support | ❌ | Limited | N/A | ✅ Color-block + YAML |
| Open source | ✅ | ❌ (€€€€) | ✅ | ✅ (MIT) |
| SPICE netlist output | ❌ | ❌ | ❌ | ✅ |
| Active development | ❌ (2011) | ✅ | ✅ | ✅ |

## Architecture

```
Multi-layer die images + sparse human annotations (color blocks)
  │
  ▼
┌─────────────────────────────────────────────┐
│ Phase 1: Image → Devices                    │
│  Stitcher → Segmenter → Layer Matcher       │
│  → DeviceList (JSON)                        │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Phase 2: Devices → Clean Netlist            │
│  Grouper → Dummy Filter → Passive Merger    │
│  → CleanNetlist (JSON + SPICE)              │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Phase 3: Netlist → Schematic (future)       │
│  Topology Cluster → Exporter                │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install silicon-eye

# Or from source
git clone https://github.com/your-org/silicon-eye
cd silicon-eye
pip install -e .

# Annotate a die image (paint color blocks in any image editor)
# 🔴 NMOS  🔵 PMOS  🟢 Resistor  🟡 MIM  🟣 MOM  ⚫ DUMMY

# Parse annotations
silicon-eye annotate parse -i chip_annotated.png -o chip_config.yaml

# Run the pipeline
silicon-eye run -c chip_config.yaml -o results/

# Output: results/phase1_devices.json, results/phase2_netlist.spice
```

## Annotation Guide

Use any image editor to paint colored rectangles on a copy of your die image:

| Color | Hex | Meaning |
|---|---|---|
| 🔴 Red | `#FF0000` | NMOS transistor |
| 🔵 Blue | `#0000FF` | PMOS transistor |
| 🟢 Green | `#00FF00` | Resistor |
| 🟡 Yellow | `#FFFF00` | MIM capacitor |
| 🟣 Purple | `#800080` | MOM capacitor |
| ⚫ Gray | `#808080` | DUMMY (ignore) |

The parser (`silicon-eye annotate parse`) extracts bounding boxes and labels from the colored regions. Additional metadata (net labels, region types) goes in the YAML config.

## Supported Devices (v0.1)

| Device | Extraction Method |
|---|---|
| NMOS | poly ∩ p-diffusion |
| PMOS | poly ∩ n-diffusion (in n-well) |
| Poly Resistor | poly strip + contact holes |
| N-well Resistor | n-well strip + contacts |
| MIM Capacitor | parallel metal plates (CTM/MTM layer) |
| MOM Capacitor | interdigitated finger pattern |

## Project Status

**Pre-alpha.** Phase 1 and Phase 2 skeletons exist. SAM3 integration and real-die-image tuning in progress.

## License

MIT — see LICENSE file.

## 本机开发入口

```bash
cd /home/zuoky/project_siliconeyes/silicon-eye
source .venv/bin/activate
silicon-eye --help
silicon-eye info -c configs/test_chip.yaml
```

- [CURRENT_TASK.md](CURRENT_TASK.md)：唯一实时任务入口。
- [AGENTS.md](AGENTS.md)：项目约定与验证边界。
- [开发计划](docs/development-plan.md)：阶段顺序及验收。
- [初始基线](docs/baseline.md)：环境及已复现问题。
- [AI/脚本分工与验证设计](docs/ai-script-validation.md)：职责、判断接口及独立验收。
- [配准修复验证](docs/registration-validation.md)：合成图测试结果及接口变化。
- [八层照片验收入口](docs/registration-audit.md)：重跑命令、证据包与真实照片结果。

当前先推进配准验证。上文 Quick Start 的 `run -o` 尚未由 CLI 实现，输出目前在 `runs/`。自动分割与连接提取尚未完成，空网表不代表芯片逆向成功。

- [结构约束重验收](docs/registration-constrained-review.md)：新版点、冻结预算、约束拟合和真实结果。

- [定位缺陷修复与同源性审查](docs/registration-localization-review.md)：2026-10-14 量测可靠性、固定预算重验收与所需来源依据。

局部环配准试验入口与结果：[两层局部环试验](docs/registration-local-ring.md)。

固化的两层局部候选案例与 `register-local` 命令：[案例入口](benchmarks/local-ring-aa-poly-v1/README.md)。

主流程的局部配准阶段、阻塞语义与运行命令：[Pipeline 接入说明](docs/pipeline-local-registration.md)。

局部像素标注草案、层语义确认和 `annotate review` 入口：[像素标注合同](docs/pixel-annotation-baseline.md)。

两处内部区域的像素轮廓候选及 `annotate contours`：[材料边界候选](docs/material-contour-candidates.md)。
