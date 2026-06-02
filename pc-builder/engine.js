// ============================================================
// 推荐引擎 — 配置生成、兼容性校验、性能估算
// ============================================================

const PCBuilder = (() => {
  'use strict';

  // ---- 兼容性校验 ----
  function isCompatible(cpu, mobo) {
    const spec = SOCKET_COMPAT[cpu.socket];
    if (!spec) return false;
    return spec.compatibleChipsets.some(c => mobo.name.startsWith(c));
  }

  function isFormFactorMatch(component, targetFF) {
    if (component.formFactor) return component.formFactor === targetFF;
    return true;
  }

  function ramTypeMatch(mobo, ram) {
    return mobo.ramType === ram.type;
  }

  function psuWattageOk(psu, cpu, gpu) {
    const totalTDP = (cpu.tdp || 65) + (gpu.tdp || 150) + 80;
    return psu.wattage >= totalTDP * 1.2;
  }

  function isITXCase(caseItem) {
    return caseItem.formFactor === 'ITX';
  }

  function needsSFXPSU(caseItem) {
    return isITXCase(caseItem);
  }

  // ---- 性能估算 ----
  function estimateGameFPS(cpu, gpu, game, resolution, quality) {
    const gameData = GAME_BENCHMARKS[game];
    if (!gameData) return 0;

    const baseFPSMap = gameData.baseFPS[resolution]?.[quality];
    if (!baseFPSMap) return 0;

    const gpuTier = gpu.tier;
    const baseFPS = baseFPSMap[gpuTier] || baseFPSMap[1];

    // CPU 加成：高端 CPU 对电竞游戏影响更大
    const cpuBonus = cpu.score > 80 ? 1.08 : cpu.score > 65 ? 1.03 : 1.0;
    const result = Math.round(baseFPS * cpuBonus);

    // 帧率上限
    if (gameData.fpsCap && result > gameData.fpsCap) return gameData.fpsCap;
    return result;
  }

  // ---- 价格计算 ----
  function calcPlatformPrice(totalPrice, platformKey) {
    const deal = PLATFORM_DEALS[platformKey];
    if (!deal) return totalPrice;
    return Math.round(totalPrice * (1 - deal.baseDiscount));
  }

  // ---- 配置组装 ----
  function buildConfig(cpu, gpu, mobo, ram, storage, psu, cooler, caseItem, platform) {
    const components = { cpu, gpu, mobo, ram, storage, psu, cooler, case: caseItem };
    const basePrice = Object.values(components).reduce((sum, c) => sum + c.price, 0);
    const platformPrice = calcPlatformPrice(basePrice, platform);

    return {
      components,
      basePrice,
      platformPrice,
      platform,
      discount: basePrice - platformPrice,
    };
  }

  // ---- 主推荐算法 ----
  function recommend(options) {
    const { budget, useCase, formFactor, platform, upgradePlan } = options;
    const profile = USE_CASE_PROFILES[useCase];
    if (!profile) return [];

    const cpuBudget = Math.round(budget * profile.cpuBudgetRatio);
    const gpuBudget = Math.round(budget * profile.gpuBudgetRatio);

    // 筛选兼容硬件
    const validCPUs = HARDWARE.cpu.filter(c => c.price <= cpuBudget * 1.3);
    const validGPUs = HARDWARE.gpu.filter(g => g.price <= gpuBudget * 1.3 && g.tier >= profile.minGPUTier);
    const validMobos = HARDWARE.motherboard.filter(m => m.formFactor === formFactor);
    const validCases = HARDWARE.case.filter(c => c.formFactor === formFactor);

    // 按价格区间生成三套配置
    const configs = [];
    const tiers = [
      { name: '性价比方案', budgetRatio: 0.85, cpuBias: -0.1, gpuBias: -0.1 },
      { name: '均衡推荐', budgetRatio: 1.0, cpuBias: 0, gpuBias: 0 },
      { name: '性能优先', budgetRatio: 1.15, cpuBias: 0.1, gpuBias: 0.15 },
    ];

    for (const tier of tiers) {
      const tierBudget = Math.round(budget * tier.budgetRatio);
      const config = generateTierConfig(
        tierBudget, profile, validCPUs, validGPUs, validMobos,
        validCases, formFactor, platform, tier, upgradePlan
      );
      if (config) {
        config.tierName = tier.name;
        configs.push(config);
      }
    }

    return configs;
  }

  function generateTierConfig(budget, profile, validCPUs, validGPUs, validMobos, validCases, formFactor, platform, tier, upgradePlan) {
    const cpuTarget = Math.round(budget * profile.cpuBudgetRatio * (1 + tier.cpuBias));
    const gpuTarget = Math.round(budget * profile.gpuBudgetRatio * (1 + tier.gpuBias));

    // 选择最接近目标价格的 CPU 和 GPU
    const cpu = pickClosest(validCPUs, cpuTarget);
    const gpu = pickClosest(validGPUs, gpuTarget);

    if (!cpu || !gpu) return null;

    // 选主板
    const validMoboList = validMobos.filter(m => isCompatible(cpu, m));
    const mobo = pickClosest(validMoboList, Math.round(budget * 0.15));
    if (!mobo) return null;

    // 选内存
    const validRams = HARDWARE.ram.filter(r => ramTypeMatch(mobo, r));
    const ram = pickBestRam(validRams, profile, upgradePlan);

    // 选硬盘
    const storage = pickClosest(HARDWARE.storage, Math.round(budget * 0.10));

    // 选电源（ITX 需要 SFX）
    const needsSFX = needsSFXPSU(validCases[0]);
    const validPSUs = HARDWARE.psu.filter(p => {
      if (needsSFX && !p.sfx) return false;
      return true;
    });
    const psu = pickPSU(validPSUs, cpu, gpu, Math.round(budget * 0.10));

    // 选散热
    const cooler = pickCooler(cpu, Math.round(budget * 0.06));

    // 选机箱
    const caseItem = pickClosest(validCases, Math.round(budget * 0.08));

    if (!ram || !storage || !psu || !cooler || !caseItem) return null;

    // 校验电源功率
    if (!psuWattageOk(psu, cpu, gpu)) {
      const biggerPSU = validPSUs.find(p => psuWattageOk(p, cpu, gpu));
      if (biggerPSU) {
        return buildConfig(cpu, gpu, mobo, ram, storage, biggerPSU, cooler, caseItem, platform);
      }
      return null;
    }

    return buildConfig(cpu, gpu, mobo, ram, storage, psu, cooler, caseItem, platform);
  }

  // ---- 辅助函数 ----
  function pickClosest(list, targetPrice) {
    if (!list || list.length === 0) return null;
    return list.reduce((best, item) => {
      const diff = Math.abs(item.price - targetPrice);
      const bestDiff = Math.abs(best.price - targetPrice);
      return diff < bestDiff ? item : best;
    });
  }

  function pickBestRam(rams, profile, upgradePlan) {
    if (!rams || rams.length === 0) return null;
    // 创作/游戏优先 32GB
    if (profile.name === '内容创作' || upgradePlan === 'futureProof') {
      return rams.find(r => r.capacity >= 32) || rams[rams.length - 1];
    }
    // 默认选 16GB 或 32GB 看预算
    return rams.find(r => r.capacity === 16) || rams[0];
  }

  function pickPSU(psus, cpu, gpu, targetPrice) {
    if (!psus || psus.length === 0) return null;
    const needed = Math.round(((cpu.tdp || 65) + (gpu.tdp || 150) + 80) * 1.2);
    const valid = psus.filter(p => p.wattage >= needed);
    if (valid.length === 0) return psus[psus.length - 1];
    return pickClosest(valid, targetPrice);
  }

  function pickCooler(cpu, targetPrice) {
    const needed = cpu.tdp || 65;
    const valid = HARDWARE.cooler.filter(c => c.tdpSupport >= needed);
    return pickClosest(valid, targetPrice) || HARDWARE.cooler[0];
  }

  // ---- 性能对比数据 ----
  function calcPerformanceData(configs) {
    const games = Object.keys(GAME_BENCHMARKS);
    const resolutions = ['1080p', '1440p'];
    const qualities = ['medium', 'high'];

    return configs.map((config, idx) => {
      const { cpu, gpu } = config.components;
      const fps = {};

      for (const game of games) {
        fps[game] = {};
        for (const res of resolutions) {
          fps[game][res] = {};
          for (const q of qualities) {
            fps[game][res][q] = estimateGameFPS(cpu, gpu, game, res, q);
          }
        }
      }

      return {
        name: config.tierName,
        price: config.platformPrice,
        basePrice: config.basePrice,
        fps,
      };
    });
  }

  // ---- 升级建议 ----
  function generateUpgradeSuggestions(config, budget) {
    const suggestions = [];
    const { cpu, gpu, ram, storage, psu } = config.components;

    // GPU 升级
    const nextGPU = HARDWARE.gpu.find(g => g.tier === gpu.tier + 1 && g.price <= budget * 0.6);
    if (nextGPU) {
      suggestions.push({
        component: '显卡',
        current: gpu.name,
        upgrade: nextGPU.name,
        cost: nextGPU.price - gpu.price,
        benefit: '游戏帧率提升 20-40%',
        priority: 'high',
      });
    }

    // 内存升级
    if (ram.capacity < 32) {
      const biggerRam = HARDWARE.ram.find(r => r.type === ram.type && r.capacity >= 32);
      if (biggerRam) {
        suggestions.push({
          component: '内存',
          current: ram.name,
          upgrade: biggerRam.name,
          cost: biggerRam.price - ram.price,
          benefit: '多任务/创作更流畅',
          priority: 'medium',
        });
      }
    }

    // CPU 升级（同平台）
    const nextCPU = HARDWARE.cpu.find(c =>
      c.socket === cpu.socket && c.score > cpu.score && c.price <= budget * 0.4
    );
    if (nextCPU) {
      suggestions.push({
        component: '处理器',
        current: cpu.name,
        upgrade: nextCPU.name,
        cost: nextCPU.price - cpu.price,
        benefit: 'CPU 密集型任务提升 15-25%',
        priority: cpu.tier <= 2 ? 'high' : 'low',
      });
    }

    // 存储升级
    if (storage.capacity < 2000) {
      const biggerStorage = HARDWARE.storage.find(s => s.capacity >= 2000);
      if (biggerStorage) {
        suggestions.push({
          component: '硬盘',
          current: storage.name,
          upgrade: biggerStorage.name,
          cost: biggerStorage.price - storage.price,
          benefit: '存储空间翻倍',
          priority: 'low',
        });
      }
    }

    // 电源升级（如果功率不够未来升级）
    if (psu.wattage < 750) {
      const biggerPSU = HARDWARE.psu.find(p => p.wattage >= 750 && !p.sfx);
      if (biggerPSU) {
        suggestions.push({
          component: '电源',
          current: psu.name,
          upgrade: biggerPSU.name,
          cost: biggerPSU.price - psu.price,
          benefit: '为未来显卡升级预留功率',
          priority: 'medium',
        });
      }
    }

    return suggestions.sort((a, b) => {
      const pri = { high: 3, medium: 2, low: 1 };
      return pri[b.priority] - pri[a.priority];
    });
  }

  // ---- 公开接口 ----
  return {
    recommend,
    calcPerformanceData,
    generateUpgradeSuggestions,
    calcPlatformPrice,
    estimateGameFPS,
  };
})();
