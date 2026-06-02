// ============================================================
// 硬件数据库 — 2026年6月 国内市场参考价
// ============================================================

const HARDWARE = {
  cpu: [
    { id: '12100F',  brand: 'Intel',  name: 'i3-12100F',  price: 450,  tier: 1, socket: 'LGA1700', cores: 4,  score: 45,  tdp: 58,  best: '入门办公/轻度游戏' },
    { id: '12400F',  brand: 'Intel',  name: 'i5-12400F',  price: 750,  tier: 2, socket: 'LGA1700', cores: 6,  score: 62,  tdp: 65,  best: '主流游戏/办公' },
    { id: '13400F',  brand: 'Intel',  name: 'i5-13400F',  price: 950,  tier: 2, socket: 'LGA1700', cores: 10, score: 70,  tdp: 65,  best: '主流游戏/多任务' },
    { id: '12600KF', brand: 'Intel',  name: 'i5-12600KF', price: 1050, tier: 2, socket: 'LGA1700', cores: 10, score: 72,  tdp: 125, best: '游戏/内容创作' },
    { id: '5600',    brand: 'AMD',    name: 'R5 5600',    price: 650,  tier: 2, socket: 'AM4',    cores: 6,  score: 58,  tdp: 65,  best: '主流游戏/性价比' },
    { id: '5700X',   brand: 'AMD',    name: 'R7 5700X',   price: 950,  tier: 2, socket: 'AM4',    cores: 8,  score: 66,  tdp: 65,  best: '游戏/多任务' },
    { id: '7500F',   brand: 'AMD',    name: 'R5 7500F',   price: 1050, tier: 2, socket: 'AM5',    cores: 6,  score: 70,  tdp: 65,  best: '主流游戏/新平台' },
    { id: '14600KF', brand: 'Intel',  name: 'i5-14600KF', price: 1450, tier: 3, socket: 'LGA1700', cores: 14, score: 80,  tdp: 125, best: '高性能游戏/创作' },
    { id: '14700KF', brand: 'Intel',  name: 'i7-14700KF', price: 2150, tier: 3, socket: 'LGA1700', cores: 20, score: 88,  tdp: 125, best: '游戏/专业创作' },
    { id: '7600X',   brand: 'AMD',    name: 'R5 7600X',   price: 1250, tier: 3, socket: 'AM5',    cores: 6,  score: 74,  tdp: 105, best: '游戏/新平台' },
    { id: '7700X',   brand: 'AMD',    name: 'R7 7700X',   price: 1650, tier: 3, socket: 'AM5',    cores: 8,  score: 80,  tdp: 105, best: '游戏/内容创作' },
    { id: '9700X',   brand: 'AMD',    name: 'R7 9700X',   price: 2150, tier: 3, socket: 'AM5',    cores: 8,  score: 86,  tdp: 65,  best: '高性能游戏/创作' },
    { id: '14900KF', brand: 'Intel',  name: 'i9-14900KF', price: 3250, tier: 4, socket: 'LGA1700', cores: 24, score: 96,  tdp: 125, best: '旗舰级全能' },
    { id: '9900X',   brand: 'AMD',    name: 'R9 9900X',   price: 2950, tier: 4, socket: 'AM5',    cores: 12, score: 92,  tdp: 120, best: '旗舰级游戏/创作' },
    { id: '9950X',   brand: 'AMD',    name: 'R9 9950X',   price: 3950, tier: 4, socket: 'AM5',    cores: 16, score: 98,  tdp: 170, best: '顶级全能旗舰' },
  ],

  gpu: [
    { id: 'rx6500xt',  brand: 'AMD',    name: 'RX 6500 XT',   price: 599,   tier: 1, vram: 4,  score: 25, tdp: 107, best: '入门网游/办公' },
    { id: 'rx6600',    brand: 'AMD',    name: 'RX 6600',      price: 1099,  tier: 2, vram: 8,  score: 48, tdp: 132, best: '1080p主流游戏' },
    { id: 'rtx3060',   brand: 'NVIDIA', name: 'RTX 3060',     price: 1599,  tier: 2, vram: 12, score: 50, tdp: 170, best: '1080p游戏/创作' },
    { id: 'rtx4060',   brand: 'NVIDIA', name: 'RTX 4060',     price: 2259,  tier: 3, vram: 8,  score: 60, tdp: 115, best: '1080p高帧/1440p入门' },
    { id: 'rx7600',    brand: 'AMD',    name: 'RX 7600',      price: 1799,  tier: 3, vram: 8,  score: 58, tdp: 150, best: '1080p高帧/性价比' },
    { id: 'rx7600xt',  brand: 'AMD',    name: 'RX 7600 XT',   price: 2299,  tier: 3, vram: 16, score: 62, tdp: 150, best: '1080p高帧/1440p' },
    { id: 'rtx4060ti', brand: 'NVIDIA', name: 'RTX 4060 Ti',  price: 2899,  tier: 3, vram: 8,  score: 68, tdp: 160, best: '1440p主流游戏' },
    { id: 'rtx5060',   brand: 'NVIDIA', name: 'RTX 5060',     price: 2699,  tier: 3, vram: 8,  score: 70, tdp: 140, best: '1440p主流/新架构' },
    { id: 'rtx4070',   brand: 'NVIDIA', name: 'RTX 4070',     price: 3599,  tier: 4, vram: 12, score: 76, tdp: 200, best: '1440p高帧游戏' },
    { id: 'rx7800xt',  brand: 'AMD',    name: 'RX 7800 XT',   price: 3299,  tier: 4, vram: 16, score: 74, tdp: 263, best: '1440p高帧/性价比' },
    { id: 'rtx4070s',  brand: 'NVIDIA', name: 'RTX 4070 SUPER', price: 4199, tier: 4, vram: 12, score: 80, tdp: 220, best: '1440p高帧/4K入门' },
    { id: 'rtx5070',   brand: 'NVIDIA', name: 'RTX 5070',     price: 5999,  tier: 5, vram: 12, score: 86, tdp: 250, best: '4K游戏/AI创作' },
    { id: 'rx9070xt',  brand: 'AMD',    name: 'RX 9070 XT',   price: 4999,  tier: 5, vram: 16, score: 82, tdp: 300, best: '4K游戏/高帧创作' },
  ],

  motherboard: [
    { id: 'b660m_d4',  name: 'B660M DDR4',        price: 499,  socket: 'LGA1700', ramType: 'DDR4',  formFactor: 'MATX', tier: 2 },
    { id: 'b760m_d5',  name: 'B760M DDR5',        price: 649,  socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'MATX', tier: 2 },
    { id: 'b760_d5',   name: 'B760 DDR5',         price: 749,  socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'ATX',  tier: 2 },
    { id: 'z690_d5',   name: 'Z690 DDR5',         price: 899,  socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'ATX',  tier: 3 },
    { id: 'z790_d5',   name: 'Z790 DDR5',         price: 1199, socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'ATX',  tier: 3 },
    { id: 'z790m_d5',  name: 'Z790M DDR5',        price: 999,  socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'MATX', tier: 3 },
    { id: 'z790i_d5',  name: 'Z790I DDR5',        price: 1299, socket: 'LGA1700', ramType: 'DDR5',  formFactor: 'ITX',  tier: 3 },
    { id: 'b550m',     name: 'B550M',             price: 449,  socket: 'AM4',    ramType: 'DDR4',  formFactor: 'MATX', tier: 2 },
    { id: 'b550',      name: 'B550',              price: 549,  socket: 'AM4',    ramType: 'DDR4',  formFactor: 'ATX',  tier: 2 },
    { id: 'b650m',     name: 'B650M DDR5',        price: 749,  socket: 'AM5',    ramType: 'DDR5',  formFactor: 'MATX', tier: 2 },
    { id: 'b650',      name: 'B650 DDR5',         price: 849,  socket: 'AM5',    ramType: 'DDR5',  formFactor: 'ATX',  tier: 2 },
    { id: 'x670e',     name: 'X670E DDR5',        price: 1399, socket: 'AM5',    ramType: 'DDR5',  formFactor: 'ATX',  tier: 3 },
    { id: 'b650i',     name: 'B650I DDR5',        price: 899,  socket: 'AM5',    ramType: 'DDR5',  formFactor: 'ITX',  tier: 2 },
    { id: 'x670ei',    name: 'X670E-I DDR5',      price: 1599, socket: 'AM5',    ramType: 'DDR5',  formFactor: 'ITX',  tier: 3 },
  ],

  ram: [
    { id: 'ddr4_16_3200', name: '16GB DDR4 3200MHz',  price: 189,  type: 'DDR4', capacity: 16, speed: 3200, tier: 1 },
    { id: 'ddr4_32_3200', name: '32GB DDR4 3200MHz',  price: 329,  type: 'DDR4', capacity: 32, speed: 3200, tier: 2 },
    { id: 'ddr5_16_5600', name: '16GB DDR5 5600MHz',  price: 269,  type: 'DDR5', capacity: 16, speed: 5600, tier: 2 },
    { id: 'ddr5_32_5600', name: '32GB DDR5 5600MHz',  price: 459,  type: 'DDR5', capacity: 32, speed: 5600, tier: 3 },
    { id: 'ddr5_32_6400', name: '32GB DDR5 6400MHz',  price: 549,  type: 'DDR5', capacity: 32, speed: 6400, tier: 3 },
    { id: 'ddr5_64_6000', name: '64GB DDR5 6000MHz',  price: 899,  type: 'DDR5', capacity: 64, speed: 6000, tier: 4 },
  ],

  storage: [
    { id: 'sata_500',   name: '500GB SATA SSD',        price: 159, type: 'SATA', capacity: 500,  speed: 550,  tier: 1 },
    { id: 'nvme_500',   name: '500GB NVMe SSD',        price: 199, type: 'NVMe', capacity: 500,  speed: 3500, tier: 2 },
    { id: 'nvme_1t',    name: '1TB NVMe SSD',          price: 349, type: 'NVMe', capacity: 1000, speed: 5000, tier: 2 },
    { id: 'nvme_1t_h',  name: '1TB NVMe SSD 高速',     price: 449, type: 'NVMe', capacity: 1000, speed: 7000, tier: 3 },
    { id: 'nvme_2t',    name: '2TB NVMe SSD',          price: 649, type: 'NVMe', capacity: 2000, speed: 5000, tier: 3 },
    { id: 'nvme_2t_h',  name: '2TB NVMe SSD 高速',     price: 899, type: 'NVMe', capacity: 2000, speed: 7000, tier: 4 },
  ],

  psu: [
    { id: 'psu_500b',  name: '500W 铜牌',  price: 199, wattage: 500,  efficiency: 'Bronze', tier: 1, sfx: false },
    { id: 'psu_550b',  name: '550W 铜牌',  price: 229, wattage: 550,  efficiency: 'Bronze', tier: 1, sfx: false },
    { id: 'psu_650b',  name: '650W 铜牌',  price: 279, wattage: 650,  efficiency: 'Bronze', tier: 2, sfx: false },
    { id: 'psu_650g',  name: '650W 金牌',  price: 379, wattage: 650,  efficiency: 'Gold',   tier: 2, sfx: false },
    { id: 'psu_750g',  name: '750W 金牌',  price: 479, wattage: 750,  efficiency: 'Gold',   tier: 3, sfx: false },
    { id: 'psu_850g',  name: '850W 金牌',  price: 579, wattage: 850,  efficiency: 'Gold',   tier: 3, sfx: false },
    { id: 'psu_1000g', name: '1000W 金牌', price: 749, wattage: 1000, efficiency: 'Gold',   tier: 4, sfx: false },
    { id: 'psu_600sfx', name: '600W SFX 金牌', price: 499, wattage: 600, efficiency: 'Gold', tier: 3, sfx: true },
    { id: 'psu_750sfx', name: '750W SFX 金牌', price: 649, wattage: 750, efficiency: 'Gold', tier: 4, sfx: true },
  ],

  cooler: [
    { id: 'air_basic',   name: '塔式风冷 基础',   price: 59,   type: 'air',  tdpSupport: 100, tier: 1 },
    { id: 'air_tower',   name: '双塔风冷',        price: 129,  type: 'air',  tdpSupport: 180, tier: 2 },
    { id: 'air_tower_h', name: '双塔风冷 高性能',  price: 199,  type: 'air',  tdpSupport: 250, tier: 3 },
    { id: 'aio_240',     name: '240mm 一体水冷',   price: 299,  type: 'aio',  tdpSupport: 250, tier: 3 },
    { id: 'aio_360',     name: '360mm 一体水冷',   price: 449,  type: 'aio',  tdpSupport: 350, tier: 4 },
  ],

  case: [
    { id: 'case_atx_basic',  name: 'ATX 中塔机箱 基础',     price: 149,  formFactor: 'ATX',  tier: 1, gpuMaxLen: 350 },
    { id: 'case_atx_mid',    name: 'ATX 中塔机箱',          price: 279,  formFactor: 'ATX',  tier: 2, gpuMaxLen: 380 },
    { id: 'case_atx_good',   name: 'ATX 中塔机箱 高散热',    price: 429,  formFactor: 'ATX',  tier: 3, gpuMaxLen: 400 },
    { id: 'case_matx_basic', name: 'M-ATX 机箱 基础',        price: 129,  formFactor: 'MATX', tier: 1, gpuMaxLen: 320 },
    { id: 'case_matx_mid',   name: 'M-ATX 机箱',            price: 229,  formFactor: 'MATX', tier: 2, gpuMaxLen: 350 },
    { id: 'case_matx_good',  name: 'M-ATX 机箱 高散热',      price: 379,  formFactor: 'MATX', tier: 3, gpuMaxLen: 380 },
    { id: 'case_itx_basic',  name: 'ITX 机箱',              price: 229,  formFactor: 'ITX',  tier: 2, gpuMaxLen: 300 },
    { id: 'case_itx_mid',    name: 'ITX 机箱 紧凑',          price: 349,  formFactor: 'ITX',  tier: 3, gpuMaxLen: 330 },
    { id: 'case_itx_good',   name: 'ITX 机箱 高散热',        price: 549,  formFactor: 'ITX',  tier: 3, gpuMaxLen: 340 },
  ],
};

// ============================================================
// 主板插槽兼容性矩阵
// ============================================================
const SOCKET_COMPAT = {
  LGA1700: {
    cpuGenerations: ['12100F','12400F','12600KF','13400F','14600KF','14700KF','14900KF'],
    compatibleChipsets: ['B660M','B760M','B760','Z690','Z790','Z790M','Z790I'],
  },
  AM4: {
    cpuGenerations: ['5600','5700X'],
    compatibleChipsets: ['B550M','B550'],
  },
  AM5: {
    cpuGenerations: ['7500F','7600X','7700X','9700X','9900X','9950X'],
    compatibleChipsets: ['B650M','B650','X670E','B650I','X670EI'],
  },
};

// ============================================================
// 游戏性能基准数据 — 1080p/1440p 各档画质 FPS
// ============================================================
const GAME_BENCHMARKS = {
  cs2: {
    name: 'Counter-Strike 2',
    genre: 'esports',
    cpuWeight: 0.45,
    gpuWeight: 0.55,
    baseFPS: {
      1080p: {
        medium: { 1: 90, 2: 160, 3: 220, 4: 280, 5: 340 },
        high:   { 1: 65, 2: 120, 3: 170, 4: 220, 5: 280 },
      },
      1440p: {
        medium: { 1: 55, 2: 100, 3: 150, 4: 200, 5: 250 },
        high:   { 1: 40, 2: 75,  3: 110, 4: 155, 5: 200 },
      },
    },
  },
  valorant: {
    name: '无畏契约 (Valorant)',
    genre: 'esports',
    cpuWeight: 0.50,
    gpuWeight: 0.50,
    baseFPS: {
      1080p: {
        medium: { 1: 120, 2: 220, 3: 300, 4: 380, 5: 450 },
        high:   { 1: 90,  2: 170, 3: 240, 4: 310, 5: 380 },
      },
      1440p: {
        medium: { 1: 80,  2: 150, 3: 220, 4: 290, 5: 360 },
        high:   { 1: 60,  2: 110, 3: 170, 4: 230, 5: 290 },
      },
    },
  },
  deltaForce: {
    name: '三角洲行动',
    genre: 'tactical',
    cpuWeight: 0.35,
    gpuWeight: 0.65,
    baseFPS: {
      1080p: {
        medium: { 1: 45, 2: 85,  3: 120, 4: 160, 5: 200 },
        high:   { 1: 30, 2: 60,  3: 90,  4: 125, 5: 160 },
      },
      1440p: {
        medium: { 1: 30, 2: 55,  3: 85,  4: 115, 5: 150 },
        high:   { 1: 20, 2: 40,  3: 65,  4: 90,  5: 120 },
      },
    },
  },
  pubg: {
    name: 'PUBG',
    genre: 'battle_royale',
    cpuWeight: 0.40,
    gpuWeight: 0.60,
    baseFPS: {
      1080p: {
        medium: { 1: 55, 2: 100, 3: 140, 4: 185, 5: 220 },
        high:   { 1: 40, 2: 75,  3: 105, 4: 140, 5: 175 },
      },
      1440p: {
        medium: { 1: 35, 2: 70,  3: 100, 4: 135, 5: 170 },
        high:   { 1: 25, 2: 50,  3: 75,  4: 100, 5: 130 },
      },
    },
  },
  genshin: {
    name: '原神',
    genre: 'action_rpg',
    cpuWeight: 0.30,
    gpuWeight: 0.70,
    baseFPS: {
      1080p: {
        medium: { 1: 45, 2: 58, 3: 60, 4: 60, 5: 60 },
        high:   { 1: 35, 2: 55, 3: 60, 4: 60, 5: 60 },
      },
      1440p: {
        medium: { 1: 35, 2: 55, 3: 60, 4: 60, 5: 60 },
        high:   { 1: 25, 2: 48, 3: 60, 4: 60, 5: 60 },
      },
    },
    fpsCap: 60,
  },
  blackmyth: {
    name: '黑神话：悟空',
    genre: 'action_rpg',
    cpuWeight: 0.25,
    gpuWeight: 0.75,
    baseFPS: {
      1080p: {
        medium: { 1: 25, 2: 48, 3: 68, 4: 88, 5: 110 },
        high:   { 1: 18, 2: 35, 3: 52, 4: 70, 5: 88 },
      },
      1440p: {
        medium: { 1: 18, 2: 35, 3: 52, 4: 70, 5: 88 },
        high:   { 1: 12, 2: 25, 3: 38, 4: 52, 5: 68 },
      },
    },
  },
};

// ============================================================
// 平台优惠信息
// ============================================================
const PLATFORM_DEALS = {
  jd: {
    name: '京东',
    icon: '🔴',
    baseDiscount: 0.05,
    label: '88VIP + 满减券',
    note: '88VIP 95折 + 每满300减30',
  },
  taobao: {
    name: '淘宝',
    icon: '🟠',
    baseDiscount: 0.03,
    label: '淘金币 + 88VIP',
    note: '88VIP 95折 + 淘金币抵扣',
  },
  pdd: {
    name: '拼多多',
    icon: '🔴',
    baseDiscount: 0.08,
    label: '百亿补贴',
    note: '百亿补贴价，已含优惠',
  },
  douyin: {
    name: '抖音',
    icon: '⚫',
    baseDiscount: 0.04,
    label: '直播专属价',
    note: '直播间限时优惠',
  },
};

// ============================================================
// 需求类型配置
// ============================================================
const USE_CASE_PROFILES = {
  gaming: {
    name: '游戏',
    cpuBudgetRatio: 0.25,
    gpuBudgetRatio: 0.50,
    minGPUTier: 2,
    preferHighGPU: true,
    description: '侧重显卡性能，CPU 够用即可',
  },
  office: {
    name: '办公',
    cpuBudgetRatio: 0.40,
    gpuBudgetRatio: 0.10,
    minGPUTier: 1,
    preferHighGPU: false,
    description: '侧重 CPU 多核和内存容量',
  },
  creative: {
    name: '内容创作',
    cpuBudgetRatio: 0.35,
    gpuBudgetRatio: 0.30,
    minGPUTier: 2,
    preferHighGPU: false,
    description: 'CPU 和 GPU 均衡，内存要大',
  },
  esports: {
    name: '电竞网游',
    cpuBudgetRatio: 0.35,
    gpuBudgetRatio: 0.40,
    minGPUTier: 2,
    preferHighGPU: true,
    description: '高帧率优先，CPU 单核要强',
  },
};
